"""Power models of the simulated devices, without Home Assistant."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final

HEATING_MODES: Final = ("heat", "heat_cool", "auto")


@dataclass(frozen=True)
class HanReporting:
    """When a HAN reader sends the power it read at an interval of the meter.

    With a change of 0 W it sends every reading, as a reader on a wire does.
    Otherwise it sends only a reading that differs from the last one sent by
    more than the change, or when the maximum report interval has passed, as
    many readers on a radio network such as Zigbee do.
    """

    change_w: int
    max_interval: timedelta

    def reports(self, power_w: float, reported_w: float, since_report: timedelta) -> bool:
        return self.change_w == 0 or abs(power_w - reported_w) > self.change_w or since_report >= self.max_interval


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


def ramp_share(elapsed: timedelta, ramp_up: timedelta) -> float:
    """Return the share of its power a car draws `elapsed` into a ramp-up that rises evenly over `ramp_up`."""
    return 1.0 if elapsed >= ramp_up else elapsed / ramp_up


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
    controlled through a cloud service takes time to start charging, and
    then `ramp_share` of the power of its current while it ramps up. A
    charger with a `fault`, or at 0 A, gives no power.
    """

    charging_allowed: bool
    current_a: float
    car_connected: bool
    car_fully_charged: bool
    starting: bool = False
    ramp_share: float = 1.0
    fault: bool = False

    @property
    def wants_power(self) -> bool:
        return self.charging_allowed and self.current_a > 0 and self.car_connected and not self.car_fully_charged and not self.fault

    @property
    def power_w(self) -> float:
        return three_phase_power_w(self.current_a) * self.ramp_share if self.wants_power and not self.starting else 0.0

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
