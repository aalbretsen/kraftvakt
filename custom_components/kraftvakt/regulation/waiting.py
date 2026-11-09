"""Waiting time before a slot is turned on."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

PERSISTENT_CYCLING_FROM: Final = 2
WAITING_STARTS_AT_UTILIZATION: Final = 0.5
SHARE_AT_PIVOT: Final = 0.8
PIVOT_CAP_FACTOR: Final = 0.999


@dataclass(frozen=True, slots=True)
class CyclingSteps:
    """How the waiting time grows on persistent cycling."""

    step: timedelta
    cap: timedelta


APPLIANCE_CYCLING: Final = CyclingSteps(
    step=timedelta(seconds=120), cap=timedelta(seconds=900)
)
FICTIVE_APPLIANCE_CYCLING: Final = CyclingSteps(
    step=timedelta(seconds=300), cap=timedelta(seconds=1800)
)


@dataclass(frozen=True, slots=True)
class WaitingCurve:
    """The share of the waiting time at the limit, by utilization of the limit.

    A normalized Hill function, settled with the owner: no waiting up to half
    the limit, then a slow start through 80 % at the pivot, and the whole
    waiting time at the limit.
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


def cycling_waiting_time(
    reon_number: int, wait_at_limit: timedelta, steps: CyclingSteps
) -> timedelta:
    """Return the fixed waiting time on persistent cycling.

    It starts at the waiting time at the limit the second time the slot is
    turned on again, and grows by one step each time up to the cap.
    """
    growth = steps.step * (reon_number - PERSISTENT_CYCLING_FROM)
    return min(steps.cap, wait_at_limit + growth)


def waiting_time(
    average_w: float,
    limit_w: float,
    wait_at_limit: timedelta,
    curve: WaitingCurve,
    reon_number: int,
    steps: CyclingSteps,
) -> timedelta:
    """Return the waiting time before a slot is turned on.

    `reon_number` tells how many times in a row the slot will have been turned
    on again when it is turned on next (see `CyclingCounter`).
    """
    if reon_number >= PERSISTENT_CYCLING_FROM:
        return cycling_waiting_time(reon_number, wait_at_limit, steps)
    return wait_at_limit * curve.share(average_w / limit_w)


class CyclingCounter:
    """Counts how many times the same slot is turned on again.

    Every command the regulation sends for another slot, forced or not, ends
    the count.
    """

    def __init__(self) -> None:
        """Start without any count."""
        self._last_key: Hashable | None = None
        self._reons = 0

    def record(self, key: Hashable, turned_on: bool) -> None:
        """Record that the regulation turned the slot on or off."""
        if key != self._last_key:
            self._last_key = key
            self._reons = 0
        elif turned_on:
            self._reons += 1

    def upcoming_reon_number(self, key: Hashable) -> int:
        """Return the count the slot gets if it is turned on next.

        Zero means the slot is not being turned on again.
        """
        return self._reons + 1 if key == self._last_key else 0

    def reset(self, key: Hashable) -> None:
        """Forget the count for the slot."""
        if key == self._last_key:
            self._last_key = None
            self._reons = 0
