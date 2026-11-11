"""Rules for the EV chargers, one fictive appliance per ampere."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, tzinfo
from typing import Final

from ..config_model import Charger, ChargingWindow

ACTIVELY_CHARGING_ABOVE_W: Final = 100
BYPASSED_AFTER_WINDOWS: Final = 2
RETRY_PAUSES: Final = (
    timedelta(minutes=15),
    timedelta(minutes=30),
    timedelta(minutes=60),
)


@dataclass(frozen=True, slots=True)
class ChargerReading:
    """What a decision knows about a charger.

    None means that the value is not valid or not given.
    """

    charge_power_w: float | None = None
    car_connected: bool | None = None
    excluded: bool = False
    window_override: bool = False
    override_switched_on_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """How a charger stands after the last decision."""

    fictive_on: int
    current_a: int | None
    allowed: bool
    bypassed: bool
    waiting: bool
    excluded: bool | None = None
    charging: bool = False
    window_overridden: bool = False
    car_connected: bool | None = None


def fictive_appliance_count(charger: Charger) -> int:
    """Return the number of fictive appliances, one per whole ampere."""
    return charger.max_current_a - charger.min_current_a + 1


def charging_current(charger: Charger, fictive_on: int) -> int:
    """Return the current for the number of fictive appliances that are on."""
    return charger.min_current_a + max(fictive_on, 1) - 1


def actively_charging(reading: ChargerReading) -> bool:
    """Return whether the charger counts as actively charging.

    Without a valid charging power there is no proof that the charger does not
    charge, so it counts as charging, also when it is deactivated.
    """
    power_w = reading.charge_power_w
    return power_w is None or power_w > ACTIVELY_CHARGING_ABOVE_W


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


def charging_window_started(
    window: ChargingWindow, after: datetime, until: datetime, time_zone: tzinfo
) -> bool:
    """Return whether the window started after `after` and no later than `until`."""
    day = after.astimezone(time_zone).date()
    last_day = until.astimezone(time_zone).date()
    while day <= last_day:
        if after < datetime.combine(day, window.start, time_zone) <= until:
            return True
        day += timedelta(days=1)
    return False


def override_expired(
    charger: Charger,
    reading: ChargerReading,
    started_at: datetime,
    now: datetime,
    time_zone: tzinfo,
) -> bool:
    """Return whether the override of the charging window has ended.

    The start of the regulation counts only when the time the override was
    switched on is not known, as after a restart of Home Assistant.
    """
    window = charger.charging_window
    if window is None or not reading.window_override:
        return False
    since = reading.override_switched_on_at or started_at
    return charging_window_started(window, since, now, time_zone)


def allowed_to_charge(
    charger: Charger, reading: ChargerReading, override_active: bool, local_time: time
) -> bool:
    """Return whether the charger is allowed to charge."""
    if reading.excluded:
        return False
    window = charger.charging_window
    return window is None or override_active or in_charging_window(window, local_time)


def window_overridden(
    charger: Charger, reading: ChargerReading, override_active: bool, local_time: time
) -> bool:
    """Return whether the charger may charge only because of the override."""
    window = charger.charging_window
    return (
        not reading.excluded
        and window is not None
        and override_active
        and not in_charging_window(window, local_time)
    )


@dataclass(slots=True)
class ChargingState:
    """What the regulation keeps track of for the chargers while it runs.

    A charger on trial may charge but does not charge actively, so it may only
    get its first fictive appliance.
    """

    priority: list[str] = field(default_factory=list)
    fictive_on: dict[str, int] = field(default_factory=dict)
    activated_at: dict[str, datetime] = field(default_factory=dict)
    excluded: set[str] | None = None
    allowed: set[str] = field(default_factory=set)
    overridden: set[str] = field(default_factory=set)
    charging: set[str] = field(default_factory=set)
    bypassed: set[str] = field(default_factory=set)
    may_charge: set[str] = field(default_factory=set)
    on_trial: set[str] = field(default_factory=set)
    waiting: set[str] = field(default_factory=set)
    rests: dict[str, Rest] = field(default_factory=dict)
    car_connected: dict[str, bool | None] = field(default_factory=dict)

    @classmethod
    def for_chargers(cls, chargers: Sequence[Charger]) -> ChargingState:
        """Return the state at a start, with the configured priority."""
        return cls(
            priority=[charger.id for charger in chargers],
            fictive_on={charger.id: 0 for charger in chargers},
        )

    def activated(self) -> list[str]:
        """Return the chargers with at least one fictive appliance on."""
        return [charger_id for charger_id, on in self.fictive_on.items() if on]

    def set_fictive_on(
        self, charger_id: str, count: int, now: datetime | None = None
    ) -> None:
        """Record how many fictive appliances of the charger are on.

        `now` is needed only when the charger is activated.
        """
        if count == 0:
            self.activated_at.pop(charger_id, None)
        elif not self.fictive_on.get(charger_id):
            if now is None:
                raise ValueError("The time is needed to activate a charger")
            self.activated_at[charger_id] = now
        self.fictive_on[charger_id] = count

    def evaluate(
        self,
        chargers: Sequence[Charger],
        readings: Mapping[str, ChargerReading],
        allowed: Collection[str],
        now: datetime,
        window: timedelta,
        one_at_a_time: bool,
        overridden: Collection[str] = (),
    ) -> list[str]:
        """Evaluate the chargers at a decision and return the newly bypassed ones."""
        self.excluded = {
            charger.id
            for charger in chargers
            if readings.get(charger.id, ChargerReading()).excluded
        }
        self.car_connected = {
            charger.id: readings.get(charger.id, ChargerReading()).car_connected
            for charger in chargers
        }
        self.allowed = set(allowed)
        self.overridden = set(overridden)
        self.charging = {
            charger_id
            for charger_id in self.activated()
            if actively_charging(readings.get(charger_id, ChargerReading()))
        }
        newly_bypassed = self._update_bypassed(chargers, readings, now, window)
        self._update_priority(chargers, newly_bypassed)
        self._select(readings, one_at_a_time)
        self._update_on_trial(readings)
        return newly_bypassed

    def status(self, chargers: Sequence[Charger]) -> dict[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return {
            charger.id: ChargerStatus(
                fictive_on=self.fictive_on.get(charger.id, 0),
                current_a=(
                    charging_current(charger, self.fictive_on[charger.id])
                    if self.fictive_on.get(charger.id)
                    else None
                ),
                allowed=charger.id in self.allowed,
                bypassed=charger.id in self.bypassed,
                waiting=charger.id in self.waiting,
                excluded=None if self.excluded is None else charger.id in self.excluded,
                charging=charger.id in self.charging
                and bool(self.fictive_on.get(charger.id)),
                window_overridden=charger.id in self.overridden,
                car_connected=self.car_connected.get(charger.id),
            )
            for charger in chargers
        }

    def _update_bypassed(
        self,
        chargers: Sequence[Charger],
        readings: Mapping[str, ChargerReading],
        now: datetime,
        window: timedelta,
    ) -> list[str]:
        bypassed = set()
        for charger in chargers:
            reading = readings.get(charger.id, ChargerReading())
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

        Settled with the owner: without a rest, two chargers with full cars take
        turns being activated forever when only one may charge at a time.
        """
        activated_at = self.activated_at.get(charger_id)
        charges = activated_at is not None and actively_charging(reading)
        if reading.car_connected is False or charges:
            self.rests.pop(charger_id, None)
        if reading.car_connected is False:
            return True
        rest = self.rests.get(charger_id)
        not_charging = (
            activated_at is not None
            and not charges
            and now - activated_at >= BYPASSED_AFTER_WINDOWS * window
        )
        if not_charging and (rest is None or rest.until <= now):
            rest = self.rests[charger_id] = Rest.after(rest, now)
        return not_charging or (rest is not None and now < rest.until)

    def _update_priority(
        self, chargers: Sequence[Charger], newly_bypassed: Sequence[str]
    ) -> None:
        """Move newly bypassed chargers to the back until a charger is full.

        The configured order comes back for the chargers that are not bypassed
        when a charger has all its fictive appliances on.
        """
        self.priority = [
            charger_id
            for charger_id in self.priority
            if charger_id not in newly_bypassed
        ] + list(newly_bypassed)
        if any(
            self.fictive_on.get(charger.id) == fictive_appliance_count(charger)
            for charger in chargers
        ):
            self.priority = [
                charger.id for charger in chargers if charger.id not in self.bypassed
            ] + [
                charger_id
                for charger_id in self.priority
                if charger_id in self.bypassed
            ]

    def _update_on_trial(self, readings: Mapping[str, ChargerReading]) -> None:
        """Find the chargers that may charge but do not charge actively.

        Settled with the owner: a charger tried without a car that charges must
        not get more current and hold back the appliances below «EV charging».
        """
        self.on_trial = {
            charger_id
            for charger_id in self.may_charge
            if not actively_charging(readings.get(charger_id, ChargerReading()))
        }

    def _select(
        self, readings: Mapping[str, ChargerReading], one_at_a_time: bool
    ) -> None:
        """Decide which chargers may get fictive appliances turned on.

        With one charger at a time, a charger that charges actively goes first
        and the others wait.
        """
        eligible = [
            charger_id
            for charger_id in self.priority
            if charger_id not in self.bypassed and charger_id in self.allowed
        ]
        self.waiting = set()
        if not one_at_a_time:
            self.may_charge = set(eligible)
            return
        charging = [
            charger_id
            for charger_id in eligible
            if actively_charging(readings.get(charger_id, ChargerReading()))
        ]
        if not charging:
            self.may_charge = set(eligible[:1])
            return
        selected = next(
            (charger_id for charger_id in charging if self.fictive_on.get(charger_id)),
            charging[0],
        )
        self.may_charge = {selected}
        self.waiting = set(eligible) - {selected}
