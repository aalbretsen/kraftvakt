"""Power models of the simulated devices, without Home Assistant."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

LINE_VOLTAGE_V: Final = 400


@dataclass(frozen=True)
class DutyCycle:
    """A heating device that heats a share of every period, on part first."""

    power_w: float
    duty_cycle_pct: int
    period: timedelta

    @property
    def on_duration(self) -> timedelta:
        """Return how long the device heats in each period."""
        return self.period * self.duty_cycle_pct / 100

    def is_heating(self, elapsed: timedelta) -> bool:
        """Return whether the device heats `elapsed` after the cycle started."""
        return elapsed % self.period < self.on_duration

    def power_at(self, elapsed: timedelta) -> float:
        """Return the power in W `elapsed` after the cycle started."""
        return self.power_w if self.is_heating(elapsed) else 0.0

    def time_to_next_change(self, elapsed: timedelta) -> timedelta | None:
        """Return the time from `elapsed` until the device starts or stops heating.

        None when the device never changes, at a duty cycle of 0 or 100 %.
        """
        if self.duty_cycle_pct in (0, 100):
            return None
        position = elapsed % self.period
        if position < self.on_duration:
            return self.on_duration - position
        return self.period - position


def three_phase_power_w(current_a: float) -> float:
    """Return the power in W of a 400 V three-phase load with power factor 1."""
    return math.sqrt(3) * LINE_VOLTAGE_V * current_a


@dataclass(frozen=True)
class ChargerState:
    """What decides the power of a simulated EV charger."""

    charging_allowed: bool
    current_a: float
    car_connected: bool
    car_fully_charged: bool

    @property
    def power_w(self) -> float:
        """Return the charging power in W."""
        charging = (
            self.charging_allowed and self.car_connected and not self.car_fully_charged
        )
        return three_phase_power_w(self.current_a) if charging else 0.0
