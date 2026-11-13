"""Averages of the power sensor, pure Python without Home Assistant.

The caller passes in the time of every measurement, so the averages do not
depend on a clock.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Final

TARIFF_WINDOW: Final = timedelta(hours=1)
CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN: Final = 2

_W_PER_UNIT: Final[dict[str | None, float]] = {None: 1.0, "W": 1.0, "kW": 1000.0}


def power_w(state: str | None, unit: str | None) -> float | None:
    """Return a sensor state in W, or None when it is not a valid measurement."""
    factor = _W_PER_UNIT.get(unit or None)
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
class _Step:
    """Power that applies from `start` until the next step starts."""

    start: datetime
    power_w: float


class PowerAverager:
    """Time-weighted averages over the regulation window and the tariff window.

    An invalid measurement keeps the last valid one in place, and the first
    measurement also applies backwards in time unless history has been added.
    """

    def __init__(self, window_length: timedelta, start: datetime) -> None:
        """Start the first regulation window at `start`."""
        self._window_length = window_length
        self._next_window_length = window_length
        self._window_start = start
        self._latest = start
        self._steps: list[_Step] = []
        self._sensor_valid = False
        self._consecutive_invalid_closes = 0

    @property
    def window_start(self) -> datetime:
        return self._window_start

    @property
    def window_end(self) -> datetime:
        return self._window_start + self._window_length

    def change_window_length(self, window_length: timedelta) -> None:
        self._next_window_length = window_length

    def add_measurement(self, when: datetime, power: float | None) -> None:
        """Record the power in W measured at `when`, or None if it is invalid.

        A measurement older than the latest one counts as made at the time of the
        latest one, so closed windows never change.
        """
        when = max(when, self._latest)
        self._latest = when
        self._sensor_valid = power is not None
        if power is None:
            return
        if self._steps and self._steps[-1].start == when:
            self._steps.pop()
        if not self._steps or self._steps[-1].power_w != power:
            self._steps.append(_Step(when, power))

    def add_history(
        self, measurements: Iterable[tuple[datetime, float | None]]
    ) -> None:
        """Add measurements from before the first measurement, oldest first.

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

    def close_window(self) -> WindowAverages:
        """Close the current regulation window and start the next one.

        When the averages are unknown after two invalid closes, the history is
        kept and the last valid measurement fills the gap. The first
        measurement after the gap is only the background or a short peak, so it
        cannot stand for the time before.
        """
        start, end = self._window_start, self.window_end
        self._window_start = end
        self._window_length = self._next_window_length
        self._latest = max(self._latest, end)
        self._consecutive_invalid_closes = (
            0 if self._sensor_valid else self._consecutive_invalid_closes + 1
        )
        if (
            not self._steps
            or self._consecutive_invalid_closes
            >= CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN
        ):
            return WindowAverages(start, end, None, None, self._sensor_valid)

        self._forget_steps_before(end - TARIFF_WINDOW)
        return WindowAverages(
            start,
            end,
            regulation_average_w=self._average(start, end),
            tariff_average_w=self._average(end - TARIFF_WINDOW, end),
            sensor_valid=self._sensor_valid,
        )

    def _average(self, start: datetime, end: datetime) -> float:
        bounds = [start, *(step.start for step in self._steps[1:]), end]
        energy = 0.0
        for step, (step_start, step_end) in zip(
            self._steps, pairwise(bounds), strict=True
        ):
            duration = (min(step_end, end) - max(step_start, start)).total_seconds()
            energy += step.power_w * max(duration, 0.0)
        return energy / (end - start).total_seconds()

    def _forget_steps_before(self, horizon: datetime) -> None:
        first_needed = 0
        while (
            first_needed + 1 < len(self._steps)
            and self._steps[first_needed + 1].start <= horizon
        ):
            first_needed += 1
        del self._steps[:first_needed]
