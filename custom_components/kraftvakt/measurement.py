"""Averages of the power sensor.

Pure logic without Home Assistant. The caller passes in the time of every
measurement, so the averages do not depend on a clock.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Final

CAPACITY_WINDOW: Final = timedelta(hours=1)
CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN: Final = 2

# A sensor without unit is read as watt.
_W_PER_UNIT: Final[dict[str | None, float]] = {None: 1.0, "W": 1.0, "kW": 1000.0}


def power_w(state: str | None, unit: str | None) -> float | None:
    """Return a sensor state in W, or None when it is not a valid measurement.

    A measurement is valid when the state is a number and the unit is W, kW or
    missing. Negative values count as 0.
    """
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
    """The averages calculated when a regulation window closes.

    The averages are None when there is no valid measurement to base them on.
    `sensor_valid` tells whether the power sensor had a valid
    measurement at the moment the window closed.
    """

    start: datetime
    end: datetime
    regulation_average_w: float | None
    capacity_average_w: float | None
    sensor_valid: bool


@dataclass(frozen=True, slots=True)
class _Step:
    """Power that applies from `start` until the next step starts."""

    start: datetime
    power_w: float


class PowerAverager:
    """Time-weighted averages of the power over the two windows.

    The power is piecewise constant: a measurement applies until the next one,
    and an invalid measurement keeps the last valid one in place.
    The first measurement also applies backwards in time, which fills the
    windows at startup, unless history from before it has been added.
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
        """Return when the current regulation window started."""
        return self._window_start

    @property
    def window_end(self) -> datetime:
        """Return when the current regulation window closes."""
        return self._window_start + self._window_length

    def change_window_length(self, window_length: timedelta) -> None:
        """Use a new length of the regulation window from the next window on.

        The current window keeps its end, and the history is kept.
        """
        self._next_window_length = window_length

    def add_measurement(self, when: datetime, power: float | None) -> None:
        """Record the power in W measured at `when`, or None if it is invalid.

        A measurement older than the latest one is treated as made at the time
        of the latest one, so closed windows never change.
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

        Like live measurements, an invalid one keeps the last valid one in
        place. Measurements at or after the first recorded step are left out,
        so the history only fills the past the averager has not measured.
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

        When the sensor was invalid at this and the previous close, the
        averages are unknown until a valid measurement comes. The history is
        kept, and the last valid measurement fills the gap, as it does for the
        time Home Assistant was down. Settled with the owner: filling the hour
        with the first measurement after the gap made the average consumption
        far too low or too high.
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

        self._forget_steps_before(end - CAPACITY_WINDOW)
        return WindowAverages(
            start,
            end,
            regulation_average_w=self._average(start, end),
            capacity_average_w=self._average(end - CAPACITY_WINDOW, end),
            sensor_valid=self._sensor_valid,
        )

    def _average(self, start: datetime, end: datetime) -> float:
        """Return the time-weighted average power between `start` and `end`."""
        bounds = [start, *(step.start for step in self._steps[1:]), end]
        energy = 0.0
        for step, (step_start, step_end) in zip(
            self._steps, pairwise(bounds), strict=True
        ):
            duration = (min(step_end, end) - max(step_start, start)).total_seconds()
            energy += step.power_w * max(duration, 0.0)
        return energy / (end - start).total_seconds()

    def _forget_steps_before(self, horizon: datetime) -> None:
        """Drop the steps that end before `horizon`; they no longer count."""
        first_needed = 0
        while (
            first_needed + 1 < len(self._steps)
            and self._steps[first_needed + 1].start <= horizon
        ):
            first_needed += 1
        del self._steps[:first_needed]
