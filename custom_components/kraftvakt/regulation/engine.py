"""The regulation engine that makes each decision."""

from __future__ import annotations

from collections.abc import Hashable, Iterator, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from itertools import islice
from typing import Final

from ..config_model import Charger, KraftvaktConfig
from .charging import (
    ChargerReading,
    ChargerStatus,
    ChargingState,
    allowed_to_charge,
    charging_current,
    override_expired,
    window_overridden,
)
from .model import (
    ActivateCharger,
    ApplianceSlotKey,
    ChargerSlotKey,
    Command,
    DeactivateCharger,
    DecisionInput,
    RegulationState,
    ResetWindowOverride,
    SetChargingCurrent,
    Slot,
    TurnOffAppliance,
    TurnOnAppliance,
    Waiting,
)
from .penalty import PenaltyLimits, PenaltyOutcome, PenaltyState
from .priority import build_slots, current_variant, fictive_slots
from .waiting import waiting_time

# Kept apart so it can change without changing the rest of the regulation.
SLOTS_PER_DECISION: Final = 1


class RegulationEngine:
    """Decides which appliances are on, in priority order (REG, STR, APP, LAD).

    The engine only knows what it has told the appliances to do and
    keeps its state only while it runs. The configuration cannot
    change while the regulation runs, so it is given once. The
    chargers are part of the regulation only while charging is enabled.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create a stopped engine for the configuration."""
        self._config = config
        self._chargers: dict[str, Charger] = (
            {charger.id: charger for charger in config.charging.chargers}
            if config.charging.enabled
            else {}
        )
        self._running = False
        self._state = RegulationState()

    @property
    def running(self) -> bool:
        """Return whether the regulation runs."""
        return self._running

    @property
    def started_at(self) -> datetime | None:
        """Return when the regulation last started, or None while stopped."""
        return self._state.started_at

    @property
    def appliances_on(self) -> frozenset[str]:
        """Return the ids of the appliances the regulation has turned on."""
        return frozenset(self._state.appliances_on)

    @property
    def current_variants(self) -> Mapping[str, str | None]:
        """Return the current variant of each appliance, None for the appliance."""
        return dict(self._state.current_variants)

    @property
    def waiting(self) -> Waiting | None:
        """Return the waiting time that runs for the next slot, if any."""
        return self._state.waiting

    @property
    def safe_state(self) -> bool:
        """Return whether the regulation is in the safe state."""
        return self._state.safe_state

    @property
    def penalty(self) -> PenaltyState:
        """Return a copy of the overconsumption state and the penalty period."""
        return replace(self._state.penalty)

    @property
    def chargers(self) -> Mapping[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return self._state.charging.status(list(self._chargers.values()))

    @property
    def charging_priority(self) -> list[str]:
        """Return the current charging priority, highest first."""
        return list(self._state.charging.priority)

    def start(self, now: datetime) -> list[Command]:
        """Start the regulation with a new state and everything off."""
        self._running = True
        self._state = RegulationState(started_at=now, charging=self._new_charging())
        return self._turn_off_everything()

    def stop(self) -> list[Command]:
        """Stop the regulation and turn everything off."""
        self._running = False
        self._state = RegulationState(charging=self._new_charging())
        return self._turn_off_everything()

    def decide(self, decision: DecisionInput) -> list[Command]:
        """Make one decision and return the commands to carry out.

        The regulation starts again when the power sensor
        is back after the safe state and when a penalty ends. While a penalty lasts, the
        current variants are still found, but nothing is turned on.
        """
        if not self._running:
            return []
        if self._state.safe_state:
            return self.start(decision.now) if decision.power_sensor_valid else []
        if decision.power_sensor_lost:
            self._state.safe_state = True
            return self._hold_everything_off()
        average = decision.regulation_average_kw
        if average is None:
            return []
        overrides_ended = self._overrides_ended(decision)
        commands: list[Command] = [
            ResetWindowOverride(charger_id) for charger_id in overrides_ended
        ]
        penalty = self._decide_penalty(decision)
        if penalty is PenaltyOutcome.ENDED:
            return commands + self.start(decision.now)
        if penalty is PenaltyOutcome.STARTED:
            commands += self._hold_everything_off()
        if self._state.penalty.active:
            return commands + self._switch_variants(decision.variant_conditions)
        forced = self._decide_chargers(decision, overrides_ended)
        forced += self._switch_variants(decision.variant_conditions)
        commands += forced
        if average > self._config.general.power_limit_kw:
            return commands + self._switch_off_above_limit(forced_off=bool(forced))
        return commands + self._turn_on_next(decision.now, average)

    def _new_charging(self) -> ChargingState:
        return ChargingState.for_chargers(list(self._chargers.values()))

    def _turn_off_everything(self) -> list[Command]:
        """Turn off every appliance and deactivate every charger."""
        commands: list[Command] = [
            TurnOffAppliance(appliance.id) for appliance in self._config.appliances
        ]
        for charger in self._chargers.values():
            commands += self._charger_commands(charger, 0)
        return commands

    def _overrides_ended(self, decision: DecisionInput) -> list[str]:
        """Return the chargers whose override of the charging window ends."""
        started_at = self._state.started_at
        assert started_at is not None
        return [
            charger.id
            for charger in self._chargers.values()
            if override_expired(
                charger,
                decision.chargers.get(charger.id, ChargerReading()),
                started_at,
                decision.now,
                decision.time_zone,
            )
        ]

    def _decide_chargers(
        self, decision: DecisionInput, overrides_ended: list[str]
    ) -> list[Command]:
        """Evaluate the chargers and switch off what they must.

        Chargers that are not allowed to charge get all their fictive
        appliances switched off, and chargers that
        become bypassed are limited to the first one. These are
        exceptions from one slot per decision.
        """
        if not self._chargers:
            return []
        charging = self._state.charging
        local_time = decision.now.astimezone(decision.time_zone).time()
        readings = {
            charger_id: decision.chargers.get(charger_id, ChargerReading())
            for charger_id in self._chargers
        }
        override_active = {
            charger_id: readings[charger_id].window_override
            and charger_id not in overrides_ended
            for charger_id in self._chargers
        }
        allowed = [
            charger.id
            for charger in self._chargers.values()
            if allowed_to_charge(
                charger, readings[charger.id], override_active[charger.id], local_time
            )
        ]
        overridden = [
            charger.id
            for charger in self._chargers.values()
            if window_overridden(
                charger, readings[charger.id], override_active[charger.id], local_time
            )
        ]
        newly_bypassed = charging.evaluate(
            list(self._chargers.values()),
            readings,
            allowed,
            decision.now,
            timedelta(seconds=self._config.general.regulation_window_s),
            self._config.charging.one_at_a_time,
            overridden,
        )
        commands: list[Command] = []
        for charger_id in charging.activated():
            if charger_id not in charging.allowed:
                commands += self._set_fictive_on(charger_id, 0)
        for charger_id in newly_bypassed:
            if charging.fictive_on[charger_id] > 1:
                commands += self._set_fictive_on(charger_id, 1)
        return commands

    def _decide_penalty(self, decision: DecisionInput) -> PenaltyOutcome:
        """Count the overconsumption and decide on the penalty."""
        if decision.capacity_average_kw is None:
            return PenaltyOutcome.NONE
        general = self._config.general
        limits = PenaltyLimits(
            power_limit_kw=general.power_limit_kw,
            threshold_kw=general.penalty_threshold_kw,
            window=timedelta(seconds=general.regulation_window_s),
        )
        return self._state.penalty.decide(
            limits, decision.capacity_average_kw, decision.regulation_averages_kw
        )

    def _hold_everything_off(self) -> list[Command]:
        """Turn everything off at once in a penalty or the safe state.

        This is an exception from one slot per decision.
        """
        self._state.appliances_on.clear()
        self._state.waiting = None
        for charger_id in self._chargers:
            self._state.charging.set_fictive_on(charger_id, 0)
        return self._turn_off_everything()

    def _switch_variants(self, variant_conditions: Mapping[str, bool]) -> list[Command]:
        """Find the current variants and handle the appliances that switch.

        An appliance that switches is off afterwards, in the place of its new
        variant. If it was off and its new place is above the lowest slot that
        is on, that slot is switched off to make room. Several appliances that
        switch at once are handled one by one from the highest new place.
        These switch-offs are exceptions from one slot per decision.
        """
        previous = self._state.current_variants
        self._state.current_variants = {
            appliance.id: current_variant(appliance, variant_conditions)
            for appliance in self._config.appliances
        }
        switching = [
            appliance_id
            for appliance_id, variant in self._state.current_variants.items()
            if appliance_id in previous and previous[appliance_id] != variant
        ]
        was_on = self._state.appliances_on & set(switching)
        places = {slot.key: place for place, slot in enumerate(self._slots())}
        commands: list[Command] = []
        for key in sorted(
            map(ApplianceSlotKey, switching), key=lambda key: places[key]
        ):
            if key.appliance_id in was_on:
                if key.appliance_id in self._state.appliances_on:
                    commands += self._switch(key, turn_on=False)
            else:
                lowest_on = next(self._slots_on_lowest_first(), None)
                if lowest_on is not None and places[key] < places[lowest_on.key]:
                    commands += self._switch(lowest_on.key, turn_on=False)
            self._forget_waiting(key)
            self._state.cycling.reset(key)
        return commands

    def _slots(self) -> list[Slot]:
        charging = self._state.charging
        return build_slots(
            self._config,
            self._state.current_variants,
            self._state.appliances_on,
            fictive_slots(
                [self._chargers[charger_id] for charger_id in charging.priority],
                charging.fictive_on,
                charging.may_charge,
                charging.on_trial,
                charging.bypassed,
            ),
        )

    def _slots_on_lowest_first(self) -> Iterator[Slot]:
        """Return the slots the regulation may switch off, lowest priority first."""
        return (
            slot for slot in reversed(self._slots()) if slot.is_on and slot.can_turn_off
        )

    def _switch_off_above_limit(self, forced_off: bool) -> list[Command]:
        """Switch off the lowest priority slots that are on.

        Nothing more is switched off when the decision has already forced
        something off. Settled with the owner: the average was measured before
        that, so switching off one more was often too much.
        """
        self._state.waiting = None
        if forced_off:
            return []
        commands: list[Command] = []
        for slot in list(islice(self._slots_on_lowest_first(), SLOTS_PER_DECISION)):
            commands += self._switch(slot.key, turn_on=False)
        return commands

    def _turn_on_next(self, now: datetime, average_kw: float) -> list[Command]:
        """Turn on the next slots in fixed priority order after waiting.

        Only the first slot that is off can be turned on, and only
        when there is room for it and its waiting time has passed. A waiting time for
        any other slot is cancelled.
        """
        commands: list[Command] = []
        for _ in range(SLOTS_PER_DECISION):
            candidate = next(
                (slot for slot in self._slots() if not slot.is_on and slot.can_turn_on),
                None,
            )
            if candidate is None or not self._may_turn_on(candidate, average_kw):
                self._state.waiting = None
                break
            if not self._has_waited(candidate, now, average_kw):
                break
            commands += self._switch(candidate.key, turn_on=True, now=now)
        return commands

    def _may_turn_on(self, slot: Slot, average_kw: float) -> bool:
        """Return whether there is room to turn the slot on.

        The average must be below the limit by more than the turn-on margin.
        Settled with the owner: the window after a decision still holds some of
        the consumption from before its commands, so an average just below the
        limit made the regulation turn on an appliance only to turn one off at
        the next decision.
        """
        general = self._config.general
        limit_kw = general.power_limit_kw
        if average_kw >= limit_kw - general.turn_on_margin_kw:
            return False
        reserve_kw = slot.power_reserve_kw
        return reserve_kw is None or average_kw + reserve_kw <= limit_kw

    def _has_waited(self, slot: Slot, now: datetime, average_kw: float) -> bool:
        """Start or continue the waiting time for the slot.

        The waiting time is calculated again at each decision from the
        average at that decision, unless the slot cycles persistently.
        """
        waiting = self._state.waiting
        started_at = (
            waiting.started_at
            if waiting is not None and waiting.key == slot.key
            else now
        )
        general = self._config.general
        required = waiting_time(
            average_kw,
            general.power_limit_kw,
            timedelta(seconds=general.wait_at_limit_s),
            self._state.cycling.upcoming_reon_number(slot.key),
            slot.cycling,
        )
        self._state.waiting = Waiting(slot.key, started_at, started_at + required)
        return now - started_at >= required

    def _forget_waiting(self, key: Hashable) -> None:
        if self._state.waiting is not None and self._state.waiting.key == key:
            self._state.waiting = None

    def _switch(
        self, key: Hashable, turn_on: bool, now: datetime | None = None
    ) -> list[Command]:
        """Return the commands that switch the slot and record it as switched.

        `now` is needed only to turn on the first fictive appliance of a charger.
        """
        match key:
            case ApplianceSlotKey(appliance_id):
                self._record_switch(key, turn_on)
                if turn_on:
                    self._state.appliances_on.add(appliance_id)
                    return [TurnOnAppliance(appliance_id)]
                self._state.appliances_on.discard(appliance_id)
                return [TurnOffAppliance(appliance_id)]
            case ChargerSlotKey(charger_id, index):
                commands = (
                    self._deactivate_others(charger_id)
                    if turn_on and index == 0
                    else []
                )
                count = index + 1 if turn_on else index
                return commands + self._set_fictive_on(charger_id, count, now)
        raise TypeError(f"Unknown slot {key!r}")

    def _deactivate_others(self, charger_id: str) -> list[Command]:
        """Deactivate the other chargers before one is activated.

        Only when one charger at a time may charge. This is an exception from
        one slot per decision.
        """
        if not self._config.charging.one_at_a_time:
            return []
        commands: list[Command] = []
        for other_id in self._state.charging.activated():
            if other_id != charger_id:
                commands += self._set_fictive_on(other_id, 0)
        return commands

    def _set_fictive_on(
        self, charger_id: str, count: int, now: datetime | None = None
    ) -> list[Command]:
        """Switch the fictive appliances of the charger so `count` are on.

        Each fictive appliance that changes counts as switched.
        `now` is needed only when the charger is activated.
        """
        charging = self._state.charging
        before = charging.fictive_on[charger_id]
        turn_on = count > before
        for index in range(min(before, count), max(before, count)):
            self._record_switch(ChargerSlotKey(charger_id, index), turn_on)
        charging.set_fictive_on(charger_id, count, now)
        commands = self._charger_commands(self._chargers[charger_id], count)
        if before == 0 and count > 0:
            commands.append(ActivateCharger(charger_id))
        return commands

    def _charger_commands(self, charger: Charger, count: int) -> list[Command]:
        """Return the commands that give the charger `count` fictive appliances on.

        The current is always set first. A charger with none on is set to the
        minimum current and then deactivated. Activating it
        is added by the caller after the current.
        """
        commands: list[Command] = [
            SetChargingCurrent(charger.id, charging_current(charger, count))
        ]
        if count == 0:
            commands.append(DeactivateCharger(charger.id))
        return commands

    def _record_switch(self, key: Hashable, turn_on: bool) -> None:
        self._forget_waiting(key)
        self._state.cycling.record(key, turn_on)
