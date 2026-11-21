"""Averages of the power sensor, pure Python without Home Assistant.

The caller passes in the time of every measurement and of every window close,
so the averages do not depend on a clock.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Sequence
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


def update_interval_s(times: Sequence[datetime], fewest_intervals: int) -> float | None:
    """Return how often a sensor reports, from the times of its reports, oldest first, to a tenth of a second.

    It is the median of the intervals, when there are at least `fewest_intervals`
    and at least half of them are within a quarter of it, so a sensor that reports
    irregularly, or history with repeated values left out, gives None.
    """
    intervals = [(later - earlier).total_seconds() for earlier, later in pairwise(times)]
    if len(intervals) < fewest_intervals:
        return None
    median = statistics.median(intervals)
    regular = [interval for interval in intervals if abs(interval - median) <= median / 4]
    if median <= 0 or len(regular) * 2 < len(intervals):
        return None
    return round(median, 1)


class PowerAverager:
    """Time-weighted averages over the regulation window and the tariff window.

    A regulation window has a number of updates of the power sensor, valid or
    not, and lasts at least three quarters of its length at the update interval;
    the caller closes it at the update that completes it, or by the clock.
    Each measurement covers the time since the measurement before it or the last
    close, whichever is later, so a closed window never changes, and the latest
    one also covers the time after it until the next. An invalid measurement
    keeps the last valid one in place, and the first measurement also applies
    backwards in time unless history has been added.
    """

    def __init__(self, updates_per_window: int, start: datetime, update_interval: timedelta | None = None) -> None:
        """Start the first regulation window at `start`, without a shortest length while the update interval is not known."""
        self._updates_per_window = updates_per_window
        self._next_updates_per_window = updates_per_window
        self._update_interval = update_interval
        self._next_update_interval = update_interval
        self._window_start = start
        self._updates = 0
        self._latest = start
        self._covers_from = start
        self._steps: list[_Step] = []
        self._sensor_valid = False
        self._consecutive_invalid_closes = 0
        self._last_missed: MissedWindows | None = None

    @property
    def window_start(self) -> datetime:
        return self._window_start

    @property
    def update_interval(self) -> timedelta | None:
        """Return the update interval of the current window."""
        return self._update_interval

    @property
    def updates(self) -> int:
        """Return the number of updates in the current window."""
        return self._updates

    @property
    def window_complete(self) -> bool:
        """Return whether the window has all its updates and has lasted three quarters of its length.

        Why the shortest length: a meter may send an extra report, as a
        Kamstrup does with its hourly list, which must not close a window that
        has only just started.
        """
        lasted = self._latest - self._window_start
        shortest = self._update_interval * self._updates_per_window * 0.75 if self._update_interval is not None else timedelta(0)
        return self._updates >= self._updates_per_window and lasted > timedelta(0) and lasted >= shortest

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
            "updates_per_window": self._updates_per_window,
            "next_updates_per_window": self._next_updates_per_window,
            "update_interval": self._update_interval,
            "next_update_interval": self._next_update_interval,
            "updates": self._updates,
            "latest_measurement_at": self._latest,
            "sensor_valid": self._sensor_valid,
            "consecutive_invalid_closes": self._consecutive_invalid_closes,
            "last_missed_windows": self._last_missed,
            "power_steps": self._steps,
        }

    def change_window(self, updates_per_window: int, update_interval: timedelta | None) -> None:
        """Use the number of updates and the update interval from the next window."""
        self._next_updates_per_window = updates_per_window
        self._next_update_interval = update_interval

    def add_measurement(self, when: datetime, power: float | None, *, update: bool = True) -> None:
        """Record the power in W measured at `when`, or None if it is invalid.

        `update` tells whether it counts as an update of the window, which the
        state of the sensor when it is first followed does not. A measurement
        older than the latest one counts as made at the time of the latest one,
        and the latest at the same time wins.
        """
        if when > self._latest:
            self._covers_from = self._latest
            self._latest = when
        self._updates += update
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
        self._updates = 0
        self._updates_per_window = self._next_updates_per_window
        self._update_interval = self._next_update_interval

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


@dataclass(frozen=True, slots=True)
class IntervalChange:
    """A power sensor that reports about every `reported_interval` instead of every `update_interval`."""

    reported_interval: timedelta
    update_interval: timedelta


@dataclass(frozen=True, slots=True)
class _ReportedWindow:
    length: timedelta
    updates: int


class ReportIntervalCheck:
    """Finds a power sensor that no longer reports at its update interval, as when its HAN reader is set up anew.

    A window closed by an update is off when its length divided by its updates
    is more than a quarter off the update interval, in either direction. Five
    windows off in a row are a change, and five in a row that are not off end it.
    A window that is not closed by an update breaks the row, so a lost
    measurement or a single extra report is no change.
    """

    def __init__(self) -> None:
        self._change: IntervalChange | None = None
        self._row: list[_ReportedWindow] = []

    @property
    def change(self) -> IntervalChange | None:
        return self._change

    def diagnostics(self) -> dict[str, Any]:
        return {"change": self._change, "row": self._row}

    def window_closed(self, length: timedelta, updates: int, update_interval: timedelta) -> bool:
        """Count a window closed by an update, and return whether a change was found or ended with it."""
        off = abs(length / updates - update_interval) > update_interval / 4
        if off == (self._change is not None):
            self._row.clear()
            return False
        self._row.append(_ReportedWindow(length, updates))
        if len(self._row) < 5:
            return False
        reported_interval = sum((window.length for window in self._row), timedelta()) / sum(window.updates for window in self._row)
        self._change = IntervalChange(reported_interval, update_interval) if off else None
        self._row.clear()
        return True

    def break_row(self) -> None:
        self._row.clear()

    def reset(self) -> None:
        self._change = None
        self._row.clear()
