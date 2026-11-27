"""Averages of the power sensor, pure Python without Home Assistant.

The caller passes in the time of every measurement and of every window close,
so the averages do not depend on a clock.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Any, Final

TARIFF_WINDOW: Final = timedelta(hours=1)
CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN: Final = 2


def power_w(state: str | None, unit: str | None) -> float | None:
    """Return a sensor state in W, or None when it is not a valid measurement."""
    factor = {None: 1.0, "W": 1.0, "kW": 1000.0}.get(unit or None)
    if factor is None or state is None:
        return None
    try:
        value = float(state)
    except ValueError:
        return None
    if not math.isfinite(value):
        return None
    return max(value, 0.0) * factor


@dataclass(frozen=True, slots=True)
class WindowAverages:
    start: datetime
    end: datetime
    regulation_average_w: float | None
    tariff_average_w: float | None
    sensor_valid: bool


@dataclass(frozen=True, slots=True)
class MissedWindows:
    """Windows that were never closed, from `start` to `end`."""

    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class _Step:
    """Power that applies from `start` until the next step starts."""

    start: datetime
    power_w: float


class PowerAverager:
    """Time-weighted averages over the regulation window and the tariff window.

    The caller closes a regulation window. Each measurement covers the time
    since the measurement before it or the last close, whichever is later, and
    at most one update interval back, so a closed window never changes; the
    latest one also covers the time after it until the next. An invalid
    measurement keeps the last valid one in place, and the first measurement
    also applies backwards in time unless history has been added.
    """

    def __init__(self, start: datetime) -> None:
        self._window_start = start
        self._latest = start
        self._covers_from = start
        self._update_interval: timedelta | None = None
        self._steps: list[_Step] = []
        self._sensor_valid = False
        self._consecutive_invalid_closes = 0
        self._last_missed: MissedWindows | None = None

    @property
    def window_start(self) -> datetime:
        return self._window_start

    @property
    def sensor_valid(self) -> bool:
        return self._sensor_valid

    @property
    def measurements(self) -> list[tuple[datetime, float]]:
        """Return the power in W from each start until the next, oldest first, over the tariff window and the step that reaches into it."""
        return [(step.start, step.power_w) for step in self._steps]

    @property
    def last_missed_windows(self) -> MissedWindows | None:
        return self._last_missed

    def diagnostics(self) -> dict[str, Any]:
        return {
            "window_start": self._window_start,
            "update_interval": self._update_interval,
            "latest_measurement_at": self._latest,
            "sensor_valid": self._sensor_valid,
            "consecutive_invalid_closes": self._consecutive_invalid_closes,
            "last_missed_windows": self._last_missed,
            "power_steps": self._steps,
        }

    def set_update_interval(self, update_interval: timedelta | None) -> None:
        """Let a measurement cover at most `update_interval` back, or back to the one before it while it is unknown."""
        self._update_interval = update_interval

    def add_measurement(self, when: datetime, power: float | None) -> None:
        """Record the power in W measured at `when`, or None if it is invalid.

        A measurement older than the latest one counts as made at the time of
        the latest one, and the latest at the same time wins.
        """
        if when > self._latest:
            self._covers_from = self._latest if self._update_interval is None else max(self._latest, when - self._update_interval)
            self._latest = when
        self._sensor_valid = power is not None
        if power is None:
            return
        if self._steps and self._steps[-1].start == self._covers_from:
            self._steps.pop()
        if not self._steps or self._steps[-1].power_w != power:
            self._steps.append(_Step(self._covers_from, power))

    def add_history(self, measurements: Iterable[tuple[datetime, float | None]]) -> None:
        """Add measurements from before the first measurement, oldest first, each holding until the next.

        The recorder keeps only changes, so a value holds until the next change.
        Only the past the averager has not measured is filled.
        """
        first_measured = self._steps[0].start if self._steps else self._latest
        history: list[_Step] = []
        for when, power in measurements:
            if when >= first_measured:
                break
            if power is not None and (not history or history[-1].power_w != power):
                history.append(_Step(when, power))
        if self._steps and history and history[-1].power_w == self._steps[0].power_w:
            self._steps[0] = history.pop()
        self._steps[:0] = history

    def skip_windows(self, until: datetime) -> MissedWindows:
        """Skip the current window and start the next at `until`.

        The time skipped counts with the last valid measurement, since nothing
        was measured meanwhile.
        """
        self._last_missed = MissedWindows(self._window_start, until)
        self._start_window(until)
        return self._last_missed

    def close_window(self, end: datetime) -> WindowAverages:
        """Close the current regulation window at `end` and start the next one.

        When the averages are unknown after two invalid closes, the history is
        kept and the last valid measurement fills the gap. The first
        measurement after the gap is only the background or a short peak, so it
        cannot stand for the time before.
        """
        start = self._window_start
        self._start_window(end)
        self._consecutive_invalid_closes = 0 if self._sensor_valid else self._consecutive_invalid_closes + 1
        if not self._steps or self._consecutive_invalid_closes >= CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN:
            return WindowAverages(start, end, None, None, self._sensor_valid)

        self._forget_steps_before(end - TARIFF_WINDOW)
        return WindowAverages(
            start,
            end,
            regulation_average_w=self._average(start, end),
            tariff_average_w=self._average(end - TARIFF_WINDOW, end),
            sensor_valid=self._sensor_valid,
        )

    def _start_window(self, start: datetime) -> None:
        self._window_start = start
        self._latest = max(self._latest, start)
        self._covers_from = self._latest

    def _average(self, start: datetime, end: datetime) -> float:
        bounds = [start, *(step.start for step in self._steps[1:]), end]
        energy = 0.0
        for step, (step_start, step_end) in zip(self._steps, pairwise(bounds), strict=True):
            duration = (min(step_end, end) - max(step_start, start)).total_seconds()
            energy += step.power_w * max(duration, 0.0)
        return energy / (end - start).total_seconds()

    def _forget_steps_before(self, horizon: datetime) -> None:
        first_needed = 0
        while first_needed + 1 < len(self._steps) and self._steps[first_needed + 1].start <= horizon:
            first_needed += 1
        del self._steps[:first_needed]


class WindowClock:
    """When the regulation window closes, by Kraftvakt's own clock in step with the updates of the power sensor.

    A window lasts its whole number of update intervals, at least one. It
    closes at the first update from a quarter of an update interval before
    they have passed since its anchor, or by the clock a little after the
    update expected then, the newest update plus whole update intervals. While
    the update interval is unknown, it closes when it has lasted its length.
    """

    def __init__(self, length: timedelta, anchor: datetime) -> None:
        self._length = length
        self._update_interval: timedelta | None = None
        self._anchor = anchor
        self._newest_update: datetime | None = None

    @property
    def length(self) -> timedelta:
        return self._length

    @property
    def earliest_close(self) -> datetime:
        """Return when an update may close the window."""
        if self._update_interval is None:
            return self._anchor + self._length
        return self._anchor + self._update_interval * (self._intervals() - 0.25)

    @property
    def expected_end(self) -> datetime:
        """Return the update expected to close the window."""
        interval, earliest = self._update_interval, self.earliest_close
        if interval is None:
            return earliest
        base = self._newest_update or self._anchor
        return base + interval * max(0, math.ceil((earliest - base) / interval - 1e-9))

    @property
    def close_at(self) -> datetime:
        """Return when the clock closes the window if no update has closed it, half an update interval, at most 2 s, after the update expected."""
        interval = self._update_interval
        wait = timedelta(0) if interval is None else min(interval / 2, timedelta(seconds=2))
        return self.expected_end + wait

    def diagnostics(self) -> dict[str, Any]:
        return {
            "length": self._length,
            "update_interval": self._update_interval,
            "anchor": self._anchor,
            "newest_update": self._newest_update,
            "earliest_close": self.earliest_close,
            "close_at": self.close_at,
        }

    def update(self, when: datetime) -> bool:
        """Record an update at `when`, and return whether it closes the window."""
        self._newest_update = when
        return when >= self.earliest_close

    def start(self, anchor: datetime, length: timedelta, update_interval: timedelta | None) -> None:
        """Start the next window from `anchor`: the update that closed the one before, or the update expected when the clock closed it."""
        self._anchor = anchor
        self._length = length
        self._update_interval = update_interval

    def _intervals(self) -> int:
        assert self._update_interval is not None
        return max(1, math.floor(self._length / self._update_interval + 0.5))
