"""Overconsumption and the penalty period."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from typing import Final

# Lets rounding errors in the sum count as paid back.
PAID_BACK_TOLERANCE_KWH: Final = 1e-9
SECONDS_PER_HOUR: Final = 3600


class PenaltyOutcome(Enum):
    """What the penalty means for the rest of a decision."""

    NONE = auto()
    STARTED = auto()
    ONGOING = auto()
    ENDED = auto()


@dataclass(frozen=True, slots=True)
class PenaltyLimits:
    """The settings that decide overconsumption and penalty.

    `window` is the regulation window that each regulation average covers.
    """

    power_limit_kw: float
    threshold_kw: float
    window: timedelta


@dataclass(slots=True)
class PenaltyState:
    """The overconsumption state and the penalty period.

    A new state with default values is created at each start, so a
    penalty only ends by being paid back here or by a restart.
    """

    overconsuming: bool = False
    overconsumption_kwh: float = 0.0
    active: bool = False
    recovery_started: bool = False

    def decide(
        self,
        limits: PenaltyLimits,
        capacity_average_kw: float,
        regulation_averages_kw: Sequence[float],
    ) -> PenaltyOutcome:
        """Count the overconsumption and decide on the penalty at a decision.

        `regulation_averages_kw` holds every regulation average computed since
        the previous decision, oldest first.
        """
        if self.overconsuming:
            self._count(limits, regulation_averages_kw)
            if self.overconsumption_kwh <= PAID_BACK_TOLERANCE_KWH:
                penalty_ends = self.active
                self._reset()
                if penalty_ends:
                    return PenaltyOutcome.ENDED
        if self.active:
            return PenaltyOutcome.ONGOING
        if not self.overconsuming and capacity_average_kw > limits.power_limit_kw:
            self.overconsuming = True
        if (
            capacity_average_kw > limits.power_limit_kw + limits.threshold_kw
            and self.overconsumption_kwh > PAID_BACK_TOLERANCE_KWH
        ):
            self.active = True
            return PenaltyOutcome.STARTED
        return PenaltyOutcome.NONE

    def _reset(self) -> None:
        self.overconsuming = False
        self.overconsumption_kwh = 0.0
        self.active = False
        self.recovery_started = False

    def _count(
        self, limits: PenaltyLimits, regulation_averages_kw: Sequence[float]
    ) -> None:
        """Add the net energy over the limit of each regulation average.

        Energy under the limit only comes from a regulation average under the
        limit, so during a penalty nothing is subtracted before the recovery
        starts at the first such average, and it goes on net from then.
        """
        hours = limits.window.total_seconds() / SECONDS_PER_HOUR
        for average_kw in regulation_averages_kw:
            excess_kw = average_kw - limits.power_limit_kw
            if self.active and excess_kw < 0:
                self.recovery_started = True
            self.overconsumption_kwh += excess_kw * hours
