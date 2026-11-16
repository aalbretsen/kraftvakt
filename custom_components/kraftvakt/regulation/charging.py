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
    None without a valid value. `override_armed` is whether what ends the override
    has been seen at a decision since it was switched on: the car connected,
    or the charger activated and actively charging. `fault` is whether a fault
    flag shows a fault while the charger is deactivated on fault.
    """

    actively_charging: bool = False
    charging_power_w: float | None = None
    car_connected: bool = False
    car_disconnected: bool = False
    charging_stopped: bool = False
    excluded: bool = False
    window_override: bool = False
    override_armed: bool = False
    finish_after_window: bool = False
    fault: bool = False


class ChargingPermission(StrEnum):
    """Whether a charger may charge, and why."""

    FAULT = "fault"
    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    WINDOW = "window"
    OVERRIDE = "override"
    FINISHING = "finishing"

    @property
    def allowed(self) -> bool:
        return self in (
            ChargingPermission.WINDOW,
            ChargingPermission.OVERRIDE,
            ChargingPermission.FINISHING,
        )


class ChargerState(StrEnum):
    """How a charger stands after the last decision, the most important first."""

    FIRST_DECISION = "first_decision"
    FAULT = "fault"
    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    NO_CAR = "no_car"
    DONE = "done"
    QUEUED = "queued"
    STARTING = "starting"
    GRACE = "grace"
    OVERRIDE = "override"
    FINISHING = "finishing"
    CHARGING = "charging"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """How a charger stands after the last decision.

    `starting_until` is when the time to start of a starting charger ends,
    and `grace_until` when the grace period of a charger in grace ends.
    `charging` holds for an activated charger that charges or is in grace.
    """

    state: ChargerState
    ampere_steps_on: int
    current_a: int | None
    bypassed: bool
    charging: bool
    car_connected: bool
    starting_until: datetime | None = None
    grace_until: datetime | None = None


def ampere_step_count(charger: Charger) -> int:
    return charger.max_current_a - charger.min_current_a + 1


def charging_current(charger: Charger, ampere_steps_on: int) -> int:
    return charger.min_current_a + max(ampere_steps_on, 1) - 1


def time_to_start(charger: Charger, window: timedelta) -> timedelta:
    """Return how long a car gets to start charging after the charger is activated.

    A charger controlled through a cloud service may take much longer than
    two windows before the car draws power or it reports actively charging.
    """
    if charger.cloud_controlled:
        return max(2 * window, timedelta(seconds=charger.start_delay_s))
    return 2 * window


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


def override_ended(charger: Charger, reading: ChargerReading, becomes_done: bool) -> bool:
    """Return whether the override ends, because the car has stopped charging or left.

    Only evidence that the car has stopped charging or left ends it, unlike
    almost everywhere else where anything but evidence of true counts as
    false. An override that has ended does not come back, so a sensor that is
    unavailable for a moment, as while a cloud service is down, must not end
    it. A car that has stopped charging ends it when its charger becomes done,
    so a charger that the regulation has deactivated, or a car that pauses
    within its grace period, does not end it.
    """
    if not (_override_may_end(charger, reading) and reading.override_armed):
        return False
    if charger.override_ends is OverrideEnd.CAR_DISCONNECTED:
        return reading.car_disconnected
    return becomes_done and reading.charging_stopped


def _override_may_end(charger: Charger, reading: ChargerReading) -> bool:
    """Return whether the override can arm or end; a fault does neither, so charging goes on when it clears."""
    return charger.charging_window is not None and charger.override_ends is not OverrideEnd.MANUAL and reading.window_override and not reading.fault


def charging_permission(
    charger: Charger,
    reading: ChargerReading,
    override_active: bool,
    local_time: time,
    charging: bool,
) -> ChargingPermission:
    """Return whether the charger may charge, and why.

    `charging` is whether the charger is activated and charges or is in
    grace. Finishing needs that at every decision since its window ended, so
    a stop for any reason ends it until the window allows charging again.
    """
    window = charger.charging_window
    if reading.fault:
        return ChargingPermission.FAULT
    if reading.excluded:
        return ChargingPermission.EXCLUDED
    if window is None or in_charging_window(window, local_time):
        return ChargingPermission.WINDOW
    if override_active:
        return ChargingPermission.OVERRIDE
    if reading.finish_after_window and charging and reading.car_connected:
        return ChargingPermission.FINISHING
    return ChargingPermission.OUTSIDE_WINDOW


def charging_allowed_now(
    charger: Charger,
    status: ChargerStatus | None,
    excluded: bool,
    window_override: bool,
    local_time: time,
) -> bool:
    """Return whether the charger may charge at `local_time`.

    The charging window follows the clock, while finishing and a fault are
    judged from what the last decision read, so a charger that was charging
    when its window ended stays allowed until a decision ends the finishing.
    A charger in grace counts as charging.
    """
    reading = ChargerReading(
        fault=status is not None and status.state is ChargerState.FAULT,
        car_connected=status is not None and status.car_connected,
        excluded=excluded,
        window_override=window_override,
        finish_after_window=charger.finish_after_window,
    )
    return charging_permission(charger, reading, window_override, local_time, status is not None and status.charging).allowed


@dataclass(slots=True)
class ChargingState:
    """What the regulation keeps track of for the chargers of a group while it runs.

    A charger on trial may charge but does not charge actively, so it may only
    get its first ampere step. A starting charger is a charger on trial within
    its time to start, whose power reserve is held for the car that is about to
    draw power; `starting` has when its time to start ends. `charged` has the
    chargers whose car has charged since activation, `grace` when the grace
    period of each charger in grace started, and `resumed` the chargers that
    charge again after a grace period and are first in each round until full.
    """

    priority: list[str] = field(default_factory=list)
    ampere_steps_on: dict[str, int] = field(default_factory=dict)
    activated_at: dict[str, datetime] = field(default_factory=dict)
    charged: set[str] = field(default_factory=set)
    grace: dict[str, datetime] = field(default_factory=dict)
    done: set[str] = field(default_factory=set)
    bypassed: set[str] = field(default_factory=set)
    charging: set[str] = field(default_factory=set)
    resumed: set[str] = field(default_factory=set)
    may_charge: set[str] = field(default_factory=set)
    on_trial: set[str] = field(default_factory=set)
    starting: dict[str, datetime] = field(default_factory=dict)
    waiting: set[str] = field(default_factory=set)
    last_readings: dict[str, ChargerReading] = field(default_factory=dict)
    last_permissions: dict[str, ChargingPermission] = field(default_factory=dict)

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

        `now` is needed only when the charger is activated. A deactivated
        charger starts over: its car has not charged since activation.
        """
        if count == 0:
            self.activated_at.pop(charger_id, None)
            self.charged.discard(charger_id)
            self.grace.pop(charger_id, None)
        elif not self.ampere_steps_on.get(charger_id):
            if now is None:
                raise ValueError("The time is needed to activate a charger")
            self.activated_at[charger_id] = now
        self.ampere_steps_on[charger_id] = count

    def activated_long_enough(self, charger: Charger, now: datetime, window: timedelta) -> bool:
        """Return whether a car has had time to start charging since activation."""
        activated_at = self.activated_at.get(charger.id)
        return activated_at is not None and now - activated_at >= time_to_start(charger, window)

    def counts_as_charging(self, charger_id: str, reading: ChargerReading) -> bool:
        """Return whether an activated charger charges, or has charged since activation and so is in grace or starts it."""
        return charger_id in self.activated_at and (reading.actively_charging or charger_id in self.charged)

    def becomes_done(self, charger: Charger, reading: ChargerReading, now: datetime, window: timedelta) -> bool:
        """Return whether an activated charger that does not charge has had its time to start, or its grace period, without charging."""
        if charger.id not in self.activated_at or reading.actively_charging:
            return False
        grace_started = self.grace.get(charger.id)
        if charger.id in self.charged:
            return grace_started is not None and now - grace_started >= timedelta(seconds=charger.grace_period_s)
        return self.activated_long_enough(charger, now, window)

    def is_allowed(self, charger_id: str) -> bool:
        """Return whether the charger was allowed to charge at the last decision."""
        permission = self.last_permissions.get(charger_id)
        return permission is not None and permission.allowed

    def shares_by_charging_power(self, group: ChargerGroup) -> bool:
        return group.dynamic_order and not group.one_at_a_time

    def evaluate(
        self,
        group: ChargerGroup,
        readings: Mapping[str, ChargerReading],
        permissions: Mapping[str, ChargingPermission],
        now: datetime,
        window: timedelta,
    ) -> ChargerChanges:
        """Evaluate the chargers of the group at a decision and return those that must be switched off."""
        chargers = group.chargers
        previous_readings = self.last_readings
        previously_charging = self.charging
        self.last_readings = {charger.id: readings.get(charger.id, ChargerReading()) for charger in chargers}
        self.last_permissions = {charger.id: permissions.get(charger.id, ChargingPermission.OUTSIDE_WINDOW) for charger in chargers}
        changes = ChargerChanges()
        for charger in chargers:
            self._evaluate_charger(charger, previous_readings.get(charger.id), now, window, changes)
        self.charging = {charger.id for charger in chargers if self._charges(charger.id)}
        self.resumed = {charger_id for charger_id in self.resumed | changes.resumed if charger_id in self.charging}
        self.resumed -= {charger.id for charger in chargers if self.ampere_steps_on.get(charger.id) == ampere_step_count(charger)}
        self._update_priority(group, previously_charging, changes)
        self._select(group)
        self._update_on_trial()
        self._update_starting(group, now, window)
        return changes

    def _evaluate_charger(
        self,
        charger: Charger,
        previous: ChargerReading | None,
        now: datetime,
        window: timedelta,
        changes: ChargerChanges,
    ) -> None:
        """Update whether the charger is bypassed, in grace or done.

        A charger with a fault, or one that is not allowed to charge, stops
        because of that and not the car, so it neither starts a grace period
        nor becomes done, and neither does one without a car, which is bypassed.
        """
        charger_id = charger.id
        reading = self.last_readings[charger_id]
        if previous is not None and not previous.car_connected and reading.car_connected:
            self._restart_trial(charger_id, now)
        if reading.car_disconnected:
            self.done.discard(charger_id)
        if not reading.car_connected:
            if charger_id not in self.bypassed:
                changes.bypassed.append(charger_id)
            self.bypassed.add(charger_id)
        else:
            self.bypassed.discard(charger_id)
        if charger_id not in self.activated_at or not reading.car_connected or not self.is_allowed(charger_id):
            return
        if reading.actively_charging:
            self.charged.add(charger_id)
            if self.grace.pop(charger_id, None) is not None:
                changes.resumed.add(charger_id)
            return
        if self.becomes_done(charger, reading, now, window):
            self.done.add(charger_id)
            changes.done.append(charger_id)
        elif charger_id in self.charged and charger_id not in self.grace:
            self.grace[charger_id] = now
            changes.grace.append(charger_id)

    def _restart_trial(self, charger_id: str, now: datetime) -> None:
        """Give a car that is connected again its time to start, also on a charger that stayed activated."""
        if charger_id in self.activated_at:
            self.activated_at[charger_id] = now
        self.charged.discard(charger_id)
        self.grace.pop(charger_id, None)

    def _charges(self, charger_id: str) -> bool:
        """Return whether the charger is activated, charges or is in grace, and may go on."""
        stopped = charger_id in self.bypassed or charger_id in self.done or not self.is_allowed(charger_id)
        return not stopped and self.counts_as_charging(charger_id, self.last_readings[charger_id])

    def _update_priority(self, group: ChargerGroup, previously_charging: set[str], changes: ChargerChanges) -> None:
        """Move the chargers that stop charging, become done or become bypassed to the back, with dynamic charging order.

        A charger with a fault stops because of the fault, not the car, so it
        keeps its place. Without dynamic charging order, the configured
        priority always applies.
        """
        if not group.dynamic_order:
            self.priority = [charger.id for charger in group.chargers]
            return
        faulty = {charger_id for charger_id, permission in self.last_permissions.items() if permission is ChargingPermission.FAULT}
        stopped = (previously_charging - self.charging - faulty) | set(changes.done) | set(changes.bypassed)
        self.priority = [charger_id for charger_id in self.priority if charger_id not in stopped] + [charger_id for charger_id in self.priority if charger_id in stopped]

    def order(self, group: ChargerGroup) -> list[str]:
        """Return the chargers in the order of their ampere steps, highest first."""
        return [charger_id for block in self.blocks(group) for charger_id in block]

    def blocks(self, group: ChargerGroup) -> list[list[str]]:
        """Return the chargers in blocks whose ampere steps are interleaved, one block after the other.

        With several at once and dynamic charging order, the chargers that
        charge, and those activated to start, are the first block, in the
        configured priority with those that charge again after a grace period
        first, and the queued ones the second, in the current charging
        priority. A charger activated to start sits among those that charge,
        so room is never made for them from its first ampere step.
        """
        if not self.shares_by_charging_power(group):
            return [list(self.priority)]
        configured = [charger.id for charger in group.chargers]
        charging = [charger_id for charger_id in configured if charger_id in self.charging or (self.ampere_steps_on.get(charger_id) and charger_id in self.may_charge)]
        first = [charger_id for charger_id in charging if charger_id in self.resumed]
        return [
            first + [charger_id for charger_id in charging if charger_id not in self.resumed],
            [charger_id for charger_id in self.priority if charger_id not in charging],
        ]

    def queued(self, group: ChargerGroup) -> list[str]:
        """Return the chargers that may charge but are not activated and do not charge, in the order they get their turn."""
        return [charger_id for charger_id in self.order(group) if charger_id in self.may_charge and charger_id not in self.charging and not self.ampere_steps_on.get(charger_id)]

    def status(self, group: ChargerGroup) -> dict[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return {charger.id: self._status(charger) for charger in group.chargers}

    def _status(self, charger: Charger) -> ChargerStatus:
        steps_on = self.ampere_steps_on.get(charger.id, 0)
        reading = self.last_readings.get(charger.id, ChargerReading())
        charging = steps_on > 0 and (reading.actively_charging or charger.id in self.grace)
        grace_started = self.grace.get(charger.id)
        return ChargerStatus(
            state=self._state_of(charger.id, steps_on > 0, charging),
            ampere_steps_on=steps_on,
            current_a=charging_current(charger, steps_on) if steps_on else None,
            bypassed=charger.id in self.bypassed,
            charging=charging,
            car_connected=reading.car_connected,
            starting_until=self.starting.get(charger.id),
            grace_until=None if grace_started is None else grace_started + timedelta(seconds=charger.grace_period_s),
        )

    def _state_of(self, charger_id: str, activated: bool, charging: bool) -> ChargerState:
        permission = self.last_permissions.get(charger_id)
        if permission is None:
            return ChargerState.FIRST_DECISION
        if permission is ChargingPermission.FAULT:
            return ChargerState.FAULT
        if permission is ChargingPermission.EXCLUDED:
            return ChargerState.EXCLUDED
        if permission is ChargingPermission.OUTSIDE_WINDOW:
            return ChargerState.OUTSIDE_WINDOW
        if charger_id in self.bypassed:
            return ChargerState.NO_CAR
        if charger_id in self.done:
            return ChargerState.DONE
        if charger_id in self.waiting and not activated:
            return ChargerState.QUEUED
        if charger_id in self.starting:
            return ChargerState.STARTING
        if activated and charger_id in self.grace:
            return ChargerState.GRACE
        if permission is ChargingPermission.OVERRIDE and activated:
            return ChargerState.OVERRIDE
        if permission is ChargingPermission.FINISHING:
            return ChargerState.FINISHING
        if charging:
            return ChargerState.CHARGING
        return ChargerState.ACTIVATED if activated else ChargerState.DEACTIVATED

    def _update_on_trial(self) -> None:
        """Find the chargers that may charge but do not charge actively.

        A charger tried without a car that charges, or one in grace, must not
        get more current and hold back the steps below the entry of its group.
        """
        self.on_trial = {charger_id for charger_id in self.may_charge if not self.last_readings[charger_id].actively_charging}

    def _update_starting(self, group: ChargerGroup, now: datetime, window: timedelta) -> None:
        holds_reserve = self.shares_by_charging_power(group)
        self.starting = {
            charger.id: self.activated_at[charger.id] + time_to_start(charger, window)
            for charger in group.chargers
            if (charger.cloud_controlled or holds_reserve)
            and charger.id in self.on_trial
            and charger.id in self.activated_at
            and charger.id not in self.charged
            and not self.activated_long_enough(charger, now, window)
        }

    def _select(self, group: ChargerGroup) -> None:
        """Decide which chargers may get ampere steps turned on, and which are queued.

        With one charger at a time and dynamic charging order, a charger that
        charges goes first and the others wait; without dynamic charging order
        the first in the configured priority gets its steps. With several at
        once and dynamic charging order, the chargers that do not charge and
        are not activated are queued behind those that charge.
        """
        eligible = [charger_id for charger_id in self.priority if charger_id not in self.bypassed and charger_id not in self.done and self.is_allowed(charger_id)]
        self.waiting = set()
        if not group.one_at_a_time:
            self.may_charge = set(eligible)
            if group.dynamic_order:
                self.waiting = set(self.queued(group))
            return
        charging = [charger_id for charger_id in eligible if group.dynamic_order and (self.last_readings[charger_id].actively_charging or charger_id in self.grace)]
        if not charging:
            self.may_charge = set(eligible[:1])
            self.waiting = set(eligible[1:])
            return
        selected = next(
            (charger_id for charger_id in charging if self.ampere_steps_on.get(charger_id)),
            charging[0],
        )
        self.may_charge = {selected}
        self.waiting = set(eligible) - {selected}


@dataclass(slots=True)
class ChargerChanges:
    """What a decision found for the chargers of a group.

    The newly bypassed chargers and those that start their grace period keep
    only their first ampere step, and the done chargers are deactivated.
    """

    bypassed: list[str] = field(default_factory=list)
    grace: list[str] = field(default_factory=list)
    done: list[str] = field(default_factory=list)
    resumed: set[str] = field(default_factory=set)
