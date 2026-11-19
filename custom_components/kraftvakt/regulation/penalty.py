"""Overconsumption and the penalty period."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from typing import Final

PAID_BACK_TOLERANCE_WH: Final = 1e-6


class PenaltyOutcome(Enum):
    """What the penalty means for the rest of a decision."""

    NONE = auto()
    STARTED = auto()
    ONGOING = auto()
    ENDED = auto()


@dataclass(frozen=True, slots=True)
class PenaltyLimits:
    power_limit_w: float
    threshold_w: float


@dataclass(frozen=True, slots=True)
class RegulationAverage:
    """The regulation average of a closed window, and how long the window lasted."""

    average_w: float
    duration: timedelta


@dataclass(slots=True)
class PenaltyState:
    overconsuming: bool = False
    overconsumption_wh: float = 0.0
    active: bool = False
    recovery_started: bool = False

    def decide(
        self,
        limits: PenaltyLimits,
        tariff_average_w: float,
        regulation_averages: Sequence[RegulationAverage],
    ) -> PenaltyOutcome:
        """Count the overconsumption and decide on the penalty at a decision."""
        if self.overconsuming:
            self._count(limits, regulation_averages)
            if self.overconsumption_wh <= PAID_BACK_TOLERANCE_WH:
                penalty_ends = self.active
                self._reset()
                if penalty_ends:
                    return PenaltyOutcome.ENDED
        if self.active:
            return PenaltyOutcome.ONGOING
        if not self.overconsuming and tariff_average_w > limits.power_limit_w:
            self.overconsuming = True
        if tariff_average_w > limits.power_limit_w + limits.threshold_w and self.overconsumption_wh > PAID_BACK_TOLERANCE_WH:
            self.active = True
            return PenaltyOutcome.STARTED
        return PenaltyOutcome.NONE

    def _reset(self) -> None:
        self.overconsuming = False
        self.overconsumption_wh = 0.0
        self.active = False
        self.recovery_started = False

    def _count(self, limits: PenaltyLimits, regulation_averages: Sequence[RegulationAverage]) -> None:
        """Add the energy above the limit of each regulation average, net.

        During a penalty, recovery has started at the first regulation average
        under the limit.
        """
        for average in regulation_averages:
            excess_w = average.average_w - limits.power_limit_w
            if self.active and excess_w < 0:
                self.recovery_started = True
            self.overconsumption_wh += excess_w * average.duration.total_seconds() / 3600
