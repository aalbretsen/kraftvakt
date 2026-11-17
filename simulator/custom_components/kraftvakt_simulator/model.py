"""Power models of the simulated devices, without Home Assistant."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final

HEATING_MODES: Final = ("heat", "heat_cool", "auto")


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


def thermostat_heats(hvac_mode: str, target: float, room: float) -> bool:
    """Return whether a thermostat in the mode calls for heat in the room."""
    return hvac_mode in HEATING_MODES and target > room


def three_phase_power_w(current_a: float) -> float:
    """Return the power in W of a 400 V three-phase load with power factor 1."""
    return math.sqrt(3) * 400 * current_a


class ChargerStatus(StrEnum):
    """What a simulated EV charger reports as its status, as many real chargers do."""

    DISCONNECTED = "disconnected"
    AWAITING_START = "awaiting_start"
    STARTING = "starting"
    CHARGING = "charging"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class ChargerState:
    """What decides the power of a simulated EV charger.

    A car that wants power draws none while `starting`, as when a charger
    controlled through a cloud service takes time to start charging. A
    charger with a `fault`, or at 0 A, gives no power.
    """

    charging_allowed: bool
    current_a: float
    car_connected: bool
    car_fully_charged: bool
    starting: bool = False
    fault: bool = False

    @property
    def wants_power(self) -> bool:
        return self.charging_allowed and self.current_a > 0 and self.car_connected and not self.car_fully_charged and not self.fault

    @property
    def power_w(self) -> float:
        return three_phase_power_w(self.current_a) if self.wants_power and not self.starting else 0.0

    @property
    def status(self) -> ChargerStatus:
        if self.fault:
            return ChargerStatus.ERROR
        if not self.car_connected:
            return ChargerStatus.DISCONNECTED
        if self.car_fully_charged:
            return ChargerStatus.COMPLETED
        if not self.charging_allowed or self.current_a == 0:
            return ChargerStatus.AWAITING_START
        return ChargerStatus.STARTING if self.starting else ChargerStatus.CHARGING
