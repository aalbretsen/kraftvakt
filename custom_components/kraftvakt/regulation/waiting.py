"""Waiting time before a step is turned on."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

GROWTH_FROM_REPEAT: Final = 2
WAITING_STARTS_AT_UTILIZATION: Final = 0.5
SHARE_AT_PIVOT: Final = 0.8
PIVOT_CAP_FACTOR: Final = 0.999


@dataclass(frozen=True, slots=True)
class RepeatedTurnOnGrowth:
    """How the waiting time grows on repeated turn-on."""

    increment: timedelta
    cap: timedelta

    @classmethod
    def from_waiting_at_limit(
        cls, wait_at_limit_s: float, increment_factor: float, increments: int
    ) -> RepeatedTurnOnGrowth:
        """Return the growth, with the increment a share of the waiting at the limit."""
        increment = timedelta(seconds=wait_at_limit_s * increment_factor)
        return cls(
            increment=increment,
            cap=timedelta(seconds=wait_at_limit_s) + increment * increments,
        )


@dataclass(frozen=True, slots=True)
class WaitingCurve:
    """The share of the waiting time at the limit, by utilization of the limit.

    A normalized Hill function: no waiting up to half the limit, then a slow
    start through 80 % at the pivot, and the whole waiting time at the limit.
    """

    steepness: float
    shape: float

    @classmethod
    def from_settings(cls, steepness: float, pivot_percent: int) -> WaitingCurve:
        """Return the curve that passes through 80 % at the pivot."""
        pivot = _above_start(pivot_percent / 100)
        # A pivot the curve cannot reach at this steepness is capped silently.
        pivot = min(pivot, SHARE_AT_PIVOT ** (1 / steepness) * PIVOT_CAP_FACTOR)
        pivot_power = pivot**steepness
        shape = pivot_power * (1 - SHARE_AT_PIVOT) / (SHARE_AT_PIVOT - pivot_power)
        return cls(steepness, shape)

    def share(self, utilization: float) -> float:
        """Return the share, 0 to 1, for an average as a share of the limit."""
        power = _above_start(utilization) ** self.steepness
        if power == 0:
            return 0.0
        return power * (1 + self.shape) / (power + self.shape)


def _above_start(utilization: float) -> float:
    span = 1 - WAITING_STARTS_AT_UTILIZATION
    return min(1.0, max(0.0, (utilization - WAITING_STARTS_AT_UTILIZATION) / span))


def repeated_turn_on_waiting_time(
    repeat: int, wait_at_limit: timedelta, growth: RepeatedTurnOnGrowth
) -> timedelta:
    """Return the fixed waiting time on repeated turn-on."""
    return min(
        growth.cap, wait_at_limit + growth.increment * (repeat - GROWTH_FROM_REPEAT)
    )


def waiting_time(
    average_w: float,
    limit_w: float,
    wait_at_limit: timedelta,
    curve: WaitingCurve,
    repeat: int,
    growth: RepeatedTurnOnGrowth,
) -> timedelta:
    """Return the waiting time before a step is turned on.

    `repeat` is the count from `RepeatedTurnOnCounter.upcoming_repeat()`.
    """
    if repeat >= GROWTH_FROM_REPEAT:
        return repeated_turn_on_waiting_time(repeat, wait_at_limit, growth)
    return wait_at_limit * curve.share(average_w / limit_w)


class RepeatedTurnOnCounter:
    """Counts how many times the same step is turned on again.

    Every command the regulation sends for another step, forced or not, ends
    the count.
    """

    def __init__(self) -> None:
        """Start without any count."""
        self._last_key: Hashable | None = None
        self._repeats = 0

    def record(self, key: Hashable, turned_on: bool) -> None:
        """Record that the regulation turned the step on or off."""
        if key != self._last_key:
            self._last_key = key
            self._repeats = 0
        elif turned_on:
            self._repeats += 1

    def upcoming_repeat(self, key: Hashable) -> int:
        """Return the count the step gets if it is turned on next, 0 if not again."""
        return self._repeats + 1 if key == self._last_key else 0

    def reset(self, key: Hashable) -> None:
        """Forget the count for the step."""
        if key == self._last_key:
            self._last_key = None
            self._repeats = 0
