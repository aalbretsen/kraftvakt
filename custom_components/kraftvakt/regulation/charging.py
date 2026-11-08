"""Rules for the EV chargers.

The regulation sees a charger as fictive appliances, one per ampere.
This module decides which chargers may charge, which are bypassed or waiting,
and in which order they get their fictive appliances turned on.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, tzinfo
from typing import Final

from ..config_model import Charger, ChargingWindow

ACTIVELY_CHARGING_ABOVE_KW: Final = 0.1
BYPASSED_AFTER_WINDOWS: Final = 2


@dataclass(frozen=True, slots=True)
class ChargerReading:
    """What a decision knows about a charger.

    `charge_power_kw` is None when the charging power has no valid value.
    `car_connected` is None when the setting is not given.
    `excluded` and `window_override` are the user's switches, and
    `override_switched_on_at` tells when the override was switched
    on, or None when that is not known.
    """

    charge_power_kw: float | None = None
    car_connected: bool | None = None
    excluded: bool = False
    window_override: bool = False
    override_switched_on_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ChargerStatus:
    """How a charger stands after the last decision.

    `current_a` is None while the charger is deactivated. `excluded` tells
    whether the charger was excluded from the regulation, and is None
    until the first decision.
    """

    fictive_on: int
    current_a: int | None
    allowed: bool
    bypassed: bool
    waiting: bool
    excluded: bool | None = None


def fictive_appliance_count(charger: Charger) -> int:
    """Return the number of fictive appliances, one per whole ampere."""
    return charger.max_current_a - charger.min_current_a + 1


def charging_current(charger: Charger, fictive_on: int) -> int:
    """Return the current for the number of fictive appliances that are on.

    It is the minimum current plus the fictive appliances that are on, minus
    one. A deactivated charger is set to the minimum current.
    """
    return charger.min_current_a + max(fictive_on, 1) - 1


def actively_charging(reading: ChargerReading) -> bool:
    """Return whether the charger counts as actively charging.

    The charging power is proof that the charger does not charge. Without a
    valid value there is no proof, so the charger counts as charging, also when
    it is deactivated.
    """
    power_kw = reading.charge_power_kw
    return power_kw is None or power_kw > ACTIVELY_CHARGING_ABOVE_KW


def in_charging_window(window: ChargingWindow, local_time: time) -> bool:
    """Return whether the time of day is inside the window.

    The start is inside and the end is not. A window whose end is before its
    start reaches across midnight.
    """
    if window.start < window.end:
        return window.start <= local_time < window.end
    return local_time >= window.start or local_time < window.end


def charging_window_started(
    window: ChargingWindow, after: datetime, until: datetime, time_zone: tzinfo
) -> bool:
    """Return whether the window started after `after` and no later than `until`.

    The start of the window is a time of day in `time_zone`.
    """
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

    It ends when a charging window has started after it was switched on, also
    when the regulation was stopped or in the safe state meanwhile. The start
    of the regulation counts only when the time it was switched on is not
    known. An override has no effect, and does not end, for a charger without
    a charging window.
    """
    window = charger.charging_window
    if window is None or not reading.window_override:
        return False
    since = reading.override_switched_on_at or started_at
    return charging_window_started(window, since, now, time_zone)


def allowed_to_charge(
    charger: Charger, reading: ChargerReading, override_active: bool, local_time: time
) -> bool:
    """Return whether the charger is allowed to charge.

    A charger excluded from the regulation never charges. Otherwise it may
    charge without a charging window, inside it, or while the window is
    overridden.
    """
    if reading.excluded:
        return False
    window = charger.charging_window
    return window is None or override_active or in_charging_window(window, local_time)


@dataclass(slots=True)
class ChargingState:
    """What the regulation keeps track of for the chargers while it runs.

    `priority` is the current charging priority, highest first.
    `fictive_on` counts the fictive appliances that are on per charger, and
    `activated_at` tells when the first one was turned on. The rest is the
    result of the last evaluation: the chargers that are excluded from the
    regulation (None before the first evaluation), allowed to charge, bypassed, may get
    more fictive appliances turned on, and are waiting.
    """

    priority: list[str] = field(default_factory=list)
    fictive_on: dict[str, int] = field(default_factory=dict)
    activated_at: dict[str, datetime] = field(default_factory=dict)
    excluded: set[str] | None = None
    allowed: set[str] = field(default_factory=set)
    bypassed: set[str] = field(default_factory=set)
    may_charge: set[str] = field(default_factory=set)
    waiting: set[str] = field(default_factory=set)

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

        `now` is when the charger is activated, and is needed only then.
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
    ) -> list[str]:
        """Evaluate the chargers at a decision and return the newly bypassed ones.

        `chargers` are in the configured charging priority, and `allowed` are
        the chargers allowed to charge.
        """
        self.excluded = {
            charger.id
            for charger in chargers
            if readings.get(charger.id, ChargerReading()).excluded
        }
        self.allowed = set(allowed)
        newly_bypassed = self._update_bypassed(chargers, readings, now, window)
        self._update_priority(chargers, newly_bypassed)
        self._select(readings, one_at_a_time)
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
        """Find the chargers that do not draw power.

        A charger is bypassed when no car is connected, or when it does not
        charge although its first fictive appliance has been on for at least
        two regulation windows.
        """
        bypassed = set()
        for charger in chargers:
            reading = readings.get(charger.id, ChargerReading())
            activated_at = self.activated_at.get(charger.id)
            if reading.car_connected is False or (
                not actively_charging(reading)
                and activated_at is not None
                and now - activated_at >= BYPASSED_AFTER_WINDOWS * window
            ):
                bypassed.add(charger.id)
        newly_bypassed = [
            charger_id
            for charger_id in self.priority
            if charger_id in bypassed and charger_id not in self.bypassed
        ]
        self.bypassed = bypassed
        return newly_bypassed

    def _update_priority(
        self, chargers: Sequence[Charger], newly_bypassed: Sequence[str]
    ) -> None:
        """Update the current charging priority.

        A charger that becomes bypassed moves to the back and stays there until
        the priority is corrected. The priority is corrected back to the
        configured one for the chargers that are not bypassed when a charger has
        all its fictive appliances on. Bypassed chargers stay at the back.
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

    def _select(
        self, readings: Mapping[str, ChargerReading], one_at_a_time: bool
    ) -> None:
        """Decide which chargers may get fictive appliances turned on.

        Several at once: every charger that is allowed and not bypassed. One at a time:
        a charger that charges actively goes first,
        whether or not it may charge, and the others wait.
        Of several that charge, the activated one goes first, otherwise the
        first in the current priority. When none charges, the first in the
        current priority that is allowed. Bypassed chargers do not
        stand in the way of others.
        """
        candidates = [
            charger_id
            for charger_id in self.priority
            if charger_id not in self.bypassed
        ]
        eligible = [
            charger_id for charger_id in candidates if charger_id in self.allowed
        ]
        self.waiting = set()
        if not one_at_a_time:
            self.may_charge = set(eligible)
            return
        charging = [
            charger_id
            for charger_id in candidates
            if actively_charging(readings.get(charger_id, ChargerReading()))
        ]
        if not charging:
            self.may_charge = set(eligible[:1])
            return
        selected = next(
            (charger_id for charger_id in charging if self.fictive_on.get(charger_id)),
            charging[0],
        )
        self.may_charge = {selected} & self.allowed
        self.waiting = set(eligible) - {selected}
