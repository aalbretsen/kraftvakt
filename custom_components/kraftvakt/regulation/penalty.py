"""Overconsumption and the penalty period."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from typing import Final

# Lets rounding errors in the sum count as paid back.
PAID_BACK_TOLERANCE_WH: Final = 1e-6
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

    power_limit_w: float
    threshold_w: float
    window: timedelta


@dataclass(slots=True)
class PenaltyState:
    """The overconsumption state and the penalty period.

    A new state with default values is created at each start, so a
    penalty only ends by being paid back here or by a restart.
    """

    overconsuming: bool = False
    overconsumption_wh: float = 0.0
    active: bool = False
    recovery_started: bool = False

    def decide(
        self,
        limits: PenaltyLimits,
        capacity_average_w: float,
        regulation_averages_w: Sequence[float],
    ) -> PenaltyOutcome:
        """Count the overconsumption and decide on the penalty at a decision.

        `regulation_averages_w` holds every regulation average computed since
        the previous decision, oldest first.
        """
        if self.overconsuming:
            self._count(limits, regulation_averages_w)
            if self.overconsumption_wh <= PAID_BACK_TOLERANCE_WH:
                penalty_ends = self.active
                self._reset()
                if penalty_ends:
                    return PenaltyOutcome.ENDED
        if self.active:
            return PenaltyOutcome.ONGOING
        if not self.overconsuming and capacity_average_w > limits.power_limit_w:
            self.overconsuming = True
        if (
            capacity_average_w > limits.power_limit_w + limits.threshold_w
            and self.overconsumption_wh > PAID_BACK_TOLERANCE_WH
        ):
            self.active = True
            return PenaltyOutcome.STARTED
        return PenaltyOutcome.NONE

    def _reset(self) -> None:
        self.overconsuming = False
        self.overconsumption_wh = 0.0
        self.active = False
        self.recovery_started = False

    def _count(
        self, limits: PenaltyLimits, regulation_averages_w: Sequence[float]
    ) -> None:
        """Add the net energy over the limit of each regulation average.

        Energy under the limit only comes from a regulation average under the
        limit, so during a penalty nothing is subtracted before the recovery
        starts at the first such average, and it goes on net from then.
        """
        hours = limits.window.total_seconds() / SECONDS_PER_HOUR
        for average_w in regulation_averages_w:
            excess_w = average_w - limits.power_limit_w
            if self.active and excess_w < 0:
                self.recovery_started = True
            self.overconsumption_wh += excess_w * hours
