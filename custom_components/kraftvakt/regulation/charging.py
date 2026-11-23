"""Rules for the EV chargers, one ampere step per ampere."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum

from ..config_model import Charger, ChargerGroup, ChargingWindow, OverrideEnd


@dataclass(frozen=True, slots=True)
class ChargerReading:
    """What a decision reads for a charger.

    `car_connected` and `actively_charging` hold only with evidence that they
    are true, and `car_disconnected` and `charging_stopped` only with evidence
    that they are false. `charging_power_w` is the power the charger reports,
    None without a valid value. `override_armed` is whether what ends the
    override has been seen at a decision since it was switched on: the car
    connected, or the charger activated and actively charging.
    `charged_in_window` is whether the charger was activated and actively
    charging at a decision inside its charging window since the car was
    connected. `fault` is whether a fault flag shows a fault while the charger
    is deactivated on fault.
    """

    actively_charging: bool = False
    charging_power_w: float | None = None
    car_connected: bool = False
    car_disconnected: bool = False
    charging_stopped: bool = False
    excluded: bool = False
    window_override: bool = False
    override_armed: bool = False
    charge_until_disconnected: bool = False
    charged_in_window: bool = False
    fault: bool = False


class ChargingPermission(StrEnum):
    """Whether a charger may charge, and why."""

    FAULT = "fault"
    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    WINDOW = "window"
    OVERRIDE = "override"
    UNTIL_DISCONNECTED = "until_disconnected"

    @property
    def allowed(self) -> bool:
        return self in (
            ChargingPermission.WINDOW,
            ChargingPermission.OVERRIDE,
            ChargingPermission.UNTIL_DISCONNECTED,
        )


class ChargerState(StrEnum):
    """How a charger stands after the last decision, the most important first."""

    STOPPED = "stopped"
    FAULT = "fault"
    FIRST_DECISION = "first_decision"
    NO_CAR = "no_car"
    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    QUEUED = "queued"
    STARTING = "starting"
    CHARGING = "charging"
    ACTIVATED = "activated"
    OVERRIDE = "override"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """How a charger stands after the last decision.

    `starting_until` is when the start delay of a starting charger ends.
    `charging` holds for an activated charger that charges actively.
    """

    state: ChargerState
    ampere_steps_on: int
    current_a: int | None
    bypassed: bool
    charging: bool
    starting_until: datetime | None = None


def ampere_step_count(charger: Charger) -> int:
    return charger.max_current_a - charger.min_current_a + 1


def charging_current(charger: Charger, ampere_steps_on: int) -> int:
    return charger.min_current_a + max(ampere_steps_on, 1) - 1


def may_step_up(charger: Charger, reading: ChargerReading, starting: bool) -> bool:
    """Return whether the car draws enough power to get more than the minimum current.

    It must charge actively and draw at least half of the power at minimum
    current, which the user sets to what the car draws at the minimum current,
    so a car that draws little or nothing, as one that is full, cannot
    suddenly draw much more. While the charger is starting, the car must have
    ramped up to almost all of it.
    """
    power_w = reading.charging_power_w
    share = 0.9 if starting else 0.5
    return reading.actively_charging and power_w is not None and power_w >= share * charger.min_current_power_w


def estimated_draw_w(charger: Charger, power_w: float, ampere_steps_on: int, power_per_ampere_w: float) -> float:
    """Return what a charger that draws `power_w` now is estimated to draw with `ampere_steps_on` ampere steps on.

    A car that draws less than its current allows goes on drawing that.
    """
    if not ampere_steps_on:
        return 0.0
    return min(power_w, charging_current(charger, ampere_steps_on) * power_per_ampere_w)


def in_charging_window(window: ChargingWindow, local_time: time) -> bool:
    """Return whether the time of day is inside the window, which may span midnight."""
    if window.start < window.end:
        return window.start <= local_time < window.end
    return local_time >= window.start or local_time < window.end


def override_arms(charger: Charger, reading: ChargerReading, activated: bool) -> bool:
    """Return whether what ends the override has started, so it may end."""
    if not _override_may_end(charger, reading):
        return False
    if charger.override_ends is OverrideEnd.CAR_DISCONNECTED:
        return reading.car_connected
    return activated and reading.actively_charging


def override_ended(charger: Charger, reading: ChargerReading, activated: bool) -> bool:
    """Return whether the override ends, because the car has stopped charging or left.

    Only evidence that the car has stopped charging or left ends it, unlike
    almost everywhere else where anything but evidence of true counts as
    false. An override that has ended does not come back, so a sensor that is
    unavailable for a moment, as while a cloud service is down, must not end
    it. A charger that the regulation has deactivated does not end it either.
    """
    if not (_override_may_end(charger, reading) and reading.override_armed):
        return False
    if charger.override_ends is OverrideEnd.CAR_DISCONNECTED:
        return reading.car_disconnected
    return activated and reading.charging_stopped


def _override_may_end(charger: Charger, reading: ChargerReading) -> bool:
    """Return whether the override can arm or end; a fault does neither, so charging goes on when it clears."""
    return charger.charging_window is not None and charger.override_ends is not OverrideEnd.MANUAL and reading.window_override and not reading.fault


def charges_in_window(charger: Charger, reading: ChargerReading, activated: bool, local_time: time) -> bool:
    """Return whether the charger is activated and actively charging inside its charging window."""
    window = charger.charging_window
    return window is not None and in_charging_window(window, local_time) and activated and reading.actively_charging


def charging_permission(
    charger: Charger,
    reading: ChargerReading,
    override_active: bool,
    local_time: time,
) -> ChargingPermission:
    """Return whether the charger may charge, and why."""
    window = charger.charging_window
    if reading.fault:
        return ChargingPermission.FAULT
    if reading.excluded:
        return ChargingPermission.EXCLUDED
    if window is None or in_charging_window(window, local_time):
        return ChargingPermission.WINDOW
    if override_active:
        return ChargingPermission.OVERRIDE
    if reading.charge_until_disconnected and reading.charged_in_window and not reading.car_disconnected:
        return ChargingPermission.UNTIL_DISCONNECTED
    return ChargingPermission.OUTSIDE_WINDOW


def charging_allowed_now(
    charger: Charger,
    status: ChargerStatus | None,
    excluded: bool,
    window_override: bool,
    charged_in_window: bool,
    local_time: time,
) -> bool:
    """Return whether the charger may charge at `local_time`.

    The charging window follows the clock, while a fault is judged from what
    the last decision read.
    """
    reading = ChargerReading(
        fault=status is not None and status.state is ChargerState.FAULT,
        excluded=excluded,
        window_override=window_override,
        charge_until_disconnected=charger.charge_until_disconnected,
        charged_in_window=charged_in_window,
    )
    return charging_permission(charger, reading, window_override, local_time).allowed


@dataclass(slots=True)
class ChargingState:
    """What the regulation keeps track of for the chargers of a group while it runs.

    `charging` has the activated chargers that charge actively and may go on,
    `held_at_min` the chargers whose car does not draw enough to get more than
    the minimum current, and `starting` when the start delay of each activated
    charger ends, while it lasts. `may_charge` has the chargers that may have ampere steps on,
    and `waiting` the queued ones. `measured_power_per_ampere_w` has what each
    charger drew per ampere at the last decision where it was activated and drew power.
    """

    priority: list[str] = field(default_factory=list)
    ampere_steps_on: dict[str, int] = field(default_factory=dict)
    activated_at: dict[str, datetime] = field(default_factory=dict)
    bypassed: set[str] = field(default_factory=set)
    charging: set[str] = field(default_factory=set)
    held_at_min: set[str] = field(default_factory=set)
    may_charge: set[str] = field(default_factory=set)
    starting: dict[str, datetime] = field(default_factory=dict)
    waiting: set[str] = field(default_factory=set)
    last_readings: dict[str, ChargerReading] = field(default_factory=dict)
    last_permissions: dict[str, ChargingPermission] = field(default_factory=dict)
    measured_power_per_ampere_w: dict[str, float] = field(default_factory=dict)
    last_decision: datetime | None = None

    @classmethod
    def for_chargers(cls, chargers: Sequence[Charger]) -> ChargingState:
        """Return the state at a start, with the configured priority."""
        return cls(
            priority=[charger.id for charger in chargers],
            ampere_steps_on={charger.id: 0 for charger in chargers},
        )

    def activated(self) -> list[str]:
        """Return the chargers with at least one ampere step on."""
        return [charger_id for charger_id, on in self.ampere_steps_on.items() if on]

    def set_ampere_steps_on(self, charger_id: str, count: int, now: datetime | None = None) -> None:
        """Record how many ampere steps of the charger are on.

        `now` is needed only when the charger is activated.
        """
        if count == 0:
            self.activated_at.pop(charger_id, None)
            self.starting.pop(charger_id, None)
        elif not self.ampere_steps_on.get(charger_id):
            if now is None:
                raise ValueError("The time is needed to activate a charger")
            self.activated_at[charger_id] = now
        self.ampere_steps_on[charger_id] = count

    def power_per_ampere_w(self, charger: Charger) -> float:
        """Return the measured power per ampere, or the power at minimum current divided by the minimum current before it is measured."""
        return self.measured_power_per_ampere_w.get(charger.id, charger.min_current_power_w / charger.min_current_a)

    def charges(self, charger_id: str, reading: ChargerReading) -> bool:
        return charger_id in self.activated_at and reading.actively_charging

    def must_deactivate(self, group: ChargerGroup, charger_id: str) -> bool:
        """Return whether an activated charger is deactivated at once.

        It is when it is not allowed to charge. With dynamic charging order, it
        is also when its car is known to be disconnected, so a car connected
        again is queued instead of drawing power at once. With one charger at a
        time, one after the charger that charges is too, so only one car draws.
        """
        if not self.is_allowed(charger_id):
            return True
        if group.dynamic_order and self.last_readings[charger_id].car_disconnected:
            return True
        return group.one_at_a_time and charger_id not in self.may_charge and charger_id not in self.bypassed

    def is_allowed(self, charger_id: str) -> bool:
        """Return whether the charger was allowed to charge at the last decision."""
        permission = self.last_permissions.get(charger_id)
        return permission is not None and permission.allowed

    def may_switch_off(self, charger_id: str) -> bool:
        """Return whether the ampere steps of the charger may be switched off for room: not those of a car that does not charge, which frees nothing."""
        return charger_id not in self.bypassed and self.last_readings.get(charger_id, ChargerReading()).actively_charging

    def shares_by_charging_power(self, group: ChargerGroup) -> bool:
        return group.dynamic_order and not group.one_at_a_time

    def evaluate(
        self,
        group: ChargerGroup,
        readings: Mapping[str, ChargerReading],
        permissions: Mapping[str, ChargingPermission],
        now: datetime,
    ) -> list[str]:
        """Evaluate the chargers of the group at a decision and return those that are newly bypassed."""
        chargers = group.chargers
        previously_charging = self.charging
        self.last_readings = {charger.id: readings.get(charger.id, ChargerReading()) for charger in chargers}
        self.last_permissions = {charger.id: permissions.get(charger.id, ChargingPermission.OUTSIDE_WINDOW) for charger in chargers}
        self.last_decision = now
        self._measure_power_per_ampere(group)
        newly_bypassed = [charger.id for charger in chargers if not self.last_readings[charger.id].car_connected and charger.id not in self.bypassed]
        self.bypassed = {charger.id for charger in chargers if not self.last_readings[charger.id].car_connected}
        self.charging = {charger.id for charger in chargers if self._charges_and_may_go_on(charger.id)}
        self._update_priority(group, previously_charging, newly_bypassed)
        self._select(group)
        self._update_starting(group, now)
        self.held_at_min = {charger.id for charger in chargers if not may_step_up(charger, self.last_readings[charger.id], charger.id in self.starting)}
        return newly_bypassed

    def _measure_power_per_ampere(self, group: ChargerGroup) -> None:
        """Divide the charging power by the current the charger has had since the last decision, while it draws power."""
        for charger in group.chargers:
            reading = self.last_readings[charger.id]
            steps_on = self.ampere_steps_on.get(charger.id, 0)
            power_w = reading.charging_power_w
            if steps_on and reading.actively_charging and power_w is not None and power_w > 0:
                self.measured_power_per_ampere_w[charger.id] = power_w / charging_current(charger, steps_on)

    def _charges_and_may_go_on(self, charger_id: str) -> bool:
        stopped = charger_id in self.bypassed or not self.is_allowed(charger_id)
        return not stopped and self.charges(charger_id, self.last_readings[charger_id])

    def _update_priority(self, group: ChargerGroup, previously_charging: set[str], newly_bypassed: list[str]) -> None:
        """Keep the chargers that charge ahead, in the order they started, with dynamic charging order.

        A charger that starts charging moves behind those that already charge,
        and one that stops charging for any reason, or becomes bypassed, moves
        to the back. Without dynamic charging order, the configured priority
        always applies.
        """
        if not group.dynamic_order:
            self.priority = [charger.id for charger in group.chargers]
            return
        stopped = (previously_charging - self.charging) | set(newly_bypassed)
        went_on = previously_charging & self.charging
        started = self.charging - previously_charging
        self.priority = [
            *(charger_id for charger_id in self.priority if charger_id in went_on),
            *(charger_id for charger_id in self.priority if charger_id in started),
            *(charger_id for charger_id in self.priority if charger_id not in self.charging and charger_id not in stopped),
            *(charger_id for charger_id in self.priority if charger_id in stopped),
        ]

    def order(self, group: ChargerGroup) -> list[str]:
        """Return the chargers in the order of their ampere steps, highest first."""
        return [charger_id for block in self.blocks(group) for charger_id in block]

    def blocks(self, group: ChargerGroup) -> list[list[str]]:
        """Return the chargers in blocks whose ampere steps are interleaved, one block after the other.

        With several at once and dynamic charging order, the activated chargers
        are the first block, in the configured priority, and the queued ones the
        second, in the current charging priority. A charger activated to start
        sits among those that charge, so room is never made for them from its
        first ampere step.
        """
        if not self.shares_by_charging_power(group):
            return [list(self.priority)]
        configured = [charger.id for charger in group.chargers]
        activated = [charger_id for charger_id in configured if charger_id in self.charging or (self.ampere_steps_on.get(charger_id) and charger_id in self.may_charge)]
        return [activated, [charger_id for charger_id in self.priority if charger_id not in activated]]

    def queued(self, group: ChargerGroup) -> list[str]:
        """Return the chargers that may charge but are not activated, in the order they get their turn."""
        return [charger_id for charger_id in self.order(group) if charger_id in self.may_charge and not self.ampere_steps_on.get(charger_id)]

    def status(self, group: ChargerGroup) -> dict[str, ChargerStatus]:
        return {charger.id: self._status(charger) for charger in group.chargers}

    def _status(self, charger: Charger) -> ChargerStatus:
        steps_on = self.ampere_steps_on.get(charger.id, 0)
        reading = self.last_readings.get(charger.id, ChargerReading())
        charging = steps_on > 0 and reading.actively_charging
        return ChargerStatus(
            state=self._state_of(charger.id, steps_on > 0, charging),
            ampere_steps_on=steps_on,
            current_a=charging_current(charger, steps_on) if steps_on else None,
            bypassed=charger.id in self.bypassed,
            charging=charging,
            starting_until=self.starting.get(charger.id),
        )

    def _state_of(self, charger_id: str, activated: bool, charging: bool) -> ChargerState:
        permission = self.last_permissions.get(charger_id)
        if permission is ChargingPermission.FAULT:
            return ChargerState.FAULT
        if permission is None:
            return ChargerState.FIRST_DECISION
        if charger_id in self.bypassed:
            return ChargerState.NO_CAR
        if permission is ChargingPermission.EXCLUDED:
            return ChargerState.EXCLUDED
        if permission is ChargingPermission.OUTSIDE_WINDOW:
            return ChargerState.OUTSIDE_WINDOW
        if charger_id in self.waiting and not activated:
            return ChargerState.QUEUED
        if charging:
            return ChargerState.CHARGING
        if charger_id in self.starting:
            return ChargerState.STARTING
        if activated:
            return ChargerState.ACTIVATED
        if permission is ChargingPermission.OVERRIDE:
            return ChargerState.OVERRIDE
        return ChargerState.DEACTIVATED

    def _update_starting(self, group: ChargerGroup, now: datetime) -> None:
        """Find the activated chargers within their start delay, whether their car draws power yet or not."""
        self.starting = {
            charger.id: self.activated_at[charger.id] + timedelta(seconds=charger.start_delay_s)
            for charger in group.chargers
            if charger.id in self.may_charge and charger.id in self.activated_at and now < self.activated_at[charger.id] + timedelta(seconds=charger.start_delay_s)
        }

    def _select(self, group: ChargerGroup) -> None:
        """Decide which chargers may have ampere steps on, and which are queued.

        With one charger at a time, the first charger in the current charging
        priority that charges may go on, the chargers before it may be
        activated and wait at their minimum current for their car to draw
        power, and those after it are queued. With several at once and dynamic
        charging order, the chargers that are not activated are queued behind
        the activated ones.
        """
        eligible = [charger_id for charger_id in self.priority if charger_id not in self.bypassed and self.is_allowed(charger_id)]
        self.may_charge = set(eligible)
        self.waiting = set()
        if not group.one_at_a_time:
            if group.dynamic_order:
                self.waiting = set(self.queued(group))
            return
        charging = next((index for index, charger_id in enumerate(eligible) if charger_id in self.charging), None)
        if charging is not None:
            self.may_charge = set(eligible[: charging + 1])
            self.waiting = set(eligible[charging + 1 :])
