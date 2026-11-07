"""Waiting time before a slot is turned on (REG-012 to REG-015, LAD-014, T6)."""

from __future__ import annotations

from collections.abc import Hashable
from datetime import timedelta
from typing import Final

from .model import CyclingSteps

PERSISTENT_CYCLING_FROM: Final = 2


def linear_waiting_time(
    average_kw: float, limit_kw: float, wait_at_limit: timedelta
) -> timedelta:
    """Return the waiting time in proportion to the average (REG-013).

    An average of 0 gives no waiting time, and an average at or above the
    limit gives the waiting time at the limit.
    """
    return wait_at_limit * min(1.0, max(average_kw, 0.0) / limit_kw)


def cycling_waiting_time(
    reon_number: int, wait_at_limit: timedelta, steps: CyclingSteps
) -> timedelta:
    """Return the fixed waiting time on persistent cycling (REG-015, T6).

    It starts at the waiting time at the limit the second time the slot is
    turned on again, and grows by one step each time up to the cap.
    """
    growth = steps.step * (reon_number - PERSISTENT_CYCLING_FROM)
    return min(steps.cap, wait_at_limit + growth)


def waiting_time(
    average_kw: float,
    limit_kw: float,
    wait_at_limit: timedelta,
    reon_number: int,
    steps: CyclingSteps,
) -> timedelta:
    """Return the waiting time before a slot is turned on.

    `reon_number` tells how many times in a row the slot will have been turned
    on again when it is turned on next (see `CyclingCounter`).
    """
    if reon_number >= PERSISTENT_CYCLING_FROM:
        return cycling_waiting_time(reon_number, wait_at_limit, steps)
    return linear_waiting_time(average_kw, limit_kw, wait_at_limit)


class CyclingCounter:
    """Counts how many times the same slot is turned on again (REG-015, T6).

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
        """Forget the count for the slot (APP-009)."""
        if key == self._last_key:
            self._last_key = None
            self._reons = 0
