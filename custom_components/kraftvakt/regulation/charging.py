"""Rules for the EV chargers, one ampere step per ampere."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum
from typing import Final

from ..config_model import Charger, ChargingWindow, OverrideEnd

BYPASSED_AFTER_WINDOWS: Final = 2
RETRY_PAUSES: Final = (
    timedelta(minutes=15),
    timedelta(minutes=30),
    timedelta(minutes=60),
)


@dataclass(frozen=True, slots=True)
class ChargerReading:
    """What a decision reads for a charger; `car_connected` is None when not set.

    `car_disconnected` and `charging_stopped` hold only with evidence that no
    car is connected or that it does not charge. `override_armed` is whether
    what ends the override has been seen at a decision since it was switched
    on: the car connected, or the charger activated and actively charging.
    """

    actively_charging: bool = False
    car_connected: bool | None = None
    car_disconnected: bool = False
    charging_stopped: bool = False
    excluded: bool = False
    window_override: bool = False
    override_armed: bool = False
    finish_after_window: bool = False


class ChargingPermission(StrEnum):
    """Whether a charger may charge, and why."""

    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    WINDOW = "window"
    OVERRIDE = "override"
    FINISHING = "finishing"

    @property
    def allowed(self) -> bool:
        return self in _ALLOWED


_ALLOWED: Final = frozenset(
    {
        ChargingPermission.WINDOW,
        ChargingPermission.OVERRIDE,
        ChargingPermission.FINISHING,
    }
)


class ChargerState(StrEnum):
    """How a charger stands after the last decision, the most important first."""

    FIRST_DECISION = "first_decision"
    EXCLUDED = "excluded"
    OUTSIDE_WINDOW = "outside_window"
    NO_CAR = "no_car"
    NOT_CHARGING = "not_charging"
    QUEUED = "queued"
    OVERRIDE = "override"
    FINISHING = "finishing"
    CHARGING = "charging"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """How a charger stands after the last decision."""

    state: ChargerState
    ampere_steps_on: int
    current_a: int | None
    bypassed: bool
    charging: bool
    car_connected: bool | None


def ampere_step_count(charger: Charger) -> int:
    return charger.max_current_a - charger.min_current_a + 1


def charging_current(charger: Charger, ampere_steps_on: int) -> int:
    return charger.min_current_a + max(ampere_steps_on, 1) - 1


@dataclass(frozen=True, slots=True)
class Rest:
    """A charger that did not charge, and when it may be tried again."""

    until: datetime
    count: int

    @classmethod
    def after(cls, previous: Rest | None, now: datetime) -> Rest:
        """Return the rest that starts at `now`, longer than the previous one."""
        count = 0 if previous is None else previous.count + 1
        pause = RETRY_PAUSES[min(count, len(RETRY_PAUSES) - 1)]
        return cls(until=now + pause, count=count)


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
        return reading.car_connected is True
    return activated and reading.actively_charging


def override_ended(
    charger: Charger, reading: ChargerReading, activated_long_enough: bool
) -> bool:
    """Return whether the override ends, because the car has stopped charging or left.

    Only evidence that the car has stopped charging or left ends it, unlike
    everywhere else where anything but evidence of true counts as false. An
    override that has ended does not come back, so a sensor that is
    unavailable for a moment, as while a cloud service is down, must not end
    it. A charger that the regulation has deactivated, or activated too
    recently for a car that starts slowly, does not end it either.
    """
    if not (_override_may_end(charger, reading) and reading.override_armed):
        return False
    if charger.override_ends is OverrideEnd.CAR_DISCONNECTED:
        return reading.car_disconnected
    return activated_long_enough and reading.charging_stopped


def _override_may_end(charger: Charger, reading: ChargerReading) -> bool:
    return (
        charger.charging_window is not None
        and charger.override_ends is not OverrideEnd.MANUAL
        and reading.window_override
    )


def charging_permission(
    charger: Charger,
    reading: ChargerReading,
    override_active: bool,
    local_time: time,
    activated: bool,
) -> ChargingPermission:
    """Return whether the charger may charge, and why.

    Finishing needs the charger to have stayed activated and actively charging
    at every decision since its window ended, so a stop for any reason ends it
    until the window allows charging again.
    """
    window = charger.charging_window
    if reading.excluded:
        return ChargingPermission.EXCLUDED
    if window is None or in_charging_window(window, local_time):
        return ChargingPermission.WINDOW
    if override_active:
        return ChargingPermission.OVERRIDE
    if (
        reading.finish_after_window
        and activated
        and reading.actively_charging
        and reading.car_connected is not False
    ):
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

    The charging window follows the clock, while finishing is judged from what
    the last decision read, so a charger that was charging when its window
    ended stays allowed until a decision ends the finishing.
    """
    reading = ChargerReading(
        actively_charging=status is not None and status.charging,
        car_connected=None if status is None else status.car_connected,
        excluded=excluded,
        window_override=window_override,
        finish_after_window=charger.finish_after_window,
    )
    activated = status is not None and status.ampere_steps_on > 0
    return charging_permission(
        charger, reading, window_override, local_time, activated
    ).allowed


@dataclass(slots=True)
class ChargingState:
    """What the regulation keeps track of for the chargers while it runs.

    A charger on trial may charge but does not charge actively, so it may only
    get its first ampere step.
    """

    priority: list[str] = field(default_factory=list)
    ampere_steps_on: dict[str, int] = field(default_factory=dict)
    activated_at: dict[str, datetime] = field(default_factory=dict)
    bypassed: set[str] = field(default_factory=set)
    may_charge: set[str] = field(default_factory=set)
    on_trial: set[str] = field(default_factory=set)
    waiting: set[str] = field(default_factory=set)
    rests: dict[str, Rest] = field(default_factory=dict)
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

    def set_ampere_steps_on(
        self, charger_id: str, count: int, now: datetime | None = None
    ) -> None:
        """Record how many ampere steps of the charger are on.

        `now` is needed only when the charger is activated.
        """
        if count == 0:
            self.activated_at.pop(charger_id, None)
        elif not self.ampere_steps_on.get(charger_id):
            if now is None:
                raise ValueError("The time is needed to activate a charger")
            self.activated_at[charger_id] = now
        self.ampere_steps_on[charger_id] = count

    def activated_long_enough(
        self, charger_id: str, now: datetime, window: timedelta
    ) -> bool:
        """Return whether a car has had time to start charging since activation."""
        activated_at = self.activated_at.get(charger_id)
        return (
            activated_at is not None
            and now - activated_at >= BYPASSED_AFTER_WINDOWS * window
        )

    def is_allowed(self, charger_id: str) -> bool:
        """Return whether the charger was allowed to charge at the last decision."""
        permission = self.last_permissions.get(charger_id)
        return permission is not None and permission.allowed

    def evaluate(
        self,
        chargers: Sequence[Charger],
        readings: Mapping[str, ChargerReading],
        permissions: Mapping[str, ChargingPermission],
        now: datetime,
        window: timedelta,
        one_at_a_time: bool,
    ) -> list[str]:
        """Evaluate the chargers at a decision and return the newly bypassed ones."""
        self.last_readings = {
            charger.id: readings.get(charger.id, ChargerReading())
            for charger in chargers
        }
        self.last_permissions = {
            charger.id: permissions.get(charger.id, ChargingPermission.OUTSIDE_WINDOW)
            for charger in chargers
        }
        newly_bypassed = self._update_bypassed(chargers, now, window)
        self._update_priority(chargers, newly_bypassed)
        self._select(one_at_a_time)
        self._update_on_trial()
        return newly_bypassed

    def status(self, chargers: Sequence[Charger]) -> dict[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return {charger.id: self._status(charger) for charger in chargers}

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
            car_connected=reading.car_connected,
        )

    def _state_of(
        self, charger_id: str, activated: bool, charging: bool
    ) -> ChargerState:
        permission = self.last_permissions.get(charger_id)
        if permission is None:
            return ChargerState.FIRST_DECISION
        if permission is ChargingPermission.EXCLUDED:
            return ChargerState.EXCLUDED
        if permission is ChargingPermission.OUTSIDE_WINDOW:
            return ChargerState.OUTSIDE_WINDOW
        if charger_id in self.bypassed:
            if self.last_readings[charger_id].car_connected is False:
                return ChargerState.NO_CAR
            return ChargerState.NOT_CHARGING
        if charger_id in self.waiting:
            return ChargerState.QUEUED
        if permission is ChargingPermission.OVERRIDE and activated:
            return ChargerState.OVERRIDE
        if permission is ChargingPermission.FINISHING:
            return ChargerState.FINISHING
        if charging:
            return ChargerState.CHARGING
        return ChargerState.ACTIVATED if activated else ChargerState.DEACTIVATED

    def _update_bypassed(
        self,
        chargers: Sequence[Charger],
        now: datetime,
        window: timedelta,
    ) -> list[str]:
        bypassed = set()
        for charger in chargers:
            reading = self.last_readings[charger.id]
            if self._update_rest(charger.id, reading, now, window):
                bypassed.add(charger.id)
        newly_bypassed = [
            charger_id
            for charger_id in self.priority
            if charger_id in bypassed and charger_id not in self.bypassed
        ]
        self.bypassed = bypassed
        return newly_bypassed

    def _update_rest(
        self,
        charger_id: str,
        reading: ChargerReading,
        now: datetime,
        window: timedelta,
    ) -> bool:
        """Update the rest of the charger and return whether it is bypassed.

        Without a rest, two chargers with full cars take turns being activated
        forever when only one may charge at a time.
        """
        charges = charger_id in self.activated_at and reading.actively_charging
        if reading.car_connected is False or charges:
            self.rests.pop(charger_id, None)
        if reading.car_connected is False:
            return True
        rest = self.rests.get(charger_id)
        not_charging = not charges and self.activated_long_enough(
            charger_id, now, window
        )
        if not_charging and (rest is None or rest.until <= now):
            rest = self.rests[charger_id] = Rest.after(rest, now)
        return not_charging or (rest is not None and now < rest.until)

    def _update_priority(
        self, chargers: Sequence[Charger], newly_bypassed: Sequence[str]
    ) -> None:
        """Move newly bypassed chargers to the back until a charger is full.

        The configured order comes back for the chargers that are not bypassed
        when a charger has all its ampere steps on.
        """
        self.priority = [
            charger_id
            for charger_id in self.priority
            if charger_id not in newly_bypassed
        ] + list(newly_bypassed)
        if any(
            self.ampere_steps_on.get(charger.id) == ampere_step_count(charger)
            for charger in chargers
        ):
            self.priority = [
                charger.id for charger in chargers if charger.id not in self.bypassed
            ] + [
                charger_id
                for charger_id in self.priority
                if charger_id in self.bypassed
            ]

    def _update_on_trial(self) -> None:
        """Find the chargers that may charge but do not charge actively.

        A charger tried without a car that charges must not get more current
        and hold back the steps below the entry of its group.
        """
        self.on_trial = {
            charger_id
            for charger_id in self.may_charge
            if not self.last_readings[charger_id].actively_charging
        }

    def _select(self, one_at_a_time: bool) -> None:
        """Decide which chargers may get ampere steps turned on.

        With one charger at a time, a charger that charges actively goes first
        and the others wait.
        """
        eligible = [
            charger_id
            for charger_id in self.priority
            if charger_id not in self.bypassed and self.is_allowed(charger_id)
        ]
        self.waiting = set()
        if not one_at_a_time:
            self.may_charge = set(eligible)
            return
        charging = [
            charger_id
            for charger_id in eligible
            if self.last_readings[charger_id].actively_charging
        ]
        if not charging:
            self.may_charge = set(eligible[:1])
            return
        selected = next(
            (
                charger_id
                for charger_id in charging
                if self.ampere_steps_on.get(charger_id)
            ),
            charging[0],
        )
        self.may_charge = {selected}
        self.waiting = set(eligible) - {selected}
