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
from .waiting import CyclingSteps, WaitingCurve, waiting_time

# Kept apart so it can change without changing the rest of the regulation.
SLOTS_PER_DECISION: Final = 1


class RegulationEngine:
    """Decides which appliances are on, in priority order.

    The engine only knows what it has told the appliances to do. The
    configuration cannot change while it runs, so it is given once.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create a stopped engine for the configuration."""
        self._config = config
        self._chargers: dict[str, Charger] = (
            {charger.id: charger for charger in config.charging.chargers}
            if config.charging.enabled
            else {}
        )
        general = config.general
        self._waiting_curve = WaitingCurve.from_settings(
            general.wait_curve_steepness, general.wait_curve_pivot
        )
        self._appliance_cycling = CyclingSteps.from_waiting_at_limit(
            general.wait_at_limit_s,
            general.appliance_cycling_step_factor,
            general.appliance_cycling_steps,
        )
        self._fictive_appliance_cycling = CyclingSteps.from_waiting_at_limit(
            general.wait_at_limit_s,
            general.charger_cycling_step_factor,
            general.charger_cycling_steps,
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
    def power_limit_w(self) -> int:
        """Return the power limit the engine regulates against."""
        return self._config.general.power_limit_w

    @property
    def slots_on(self) -> int:
        """Return how many slots are on: appliances and fictive appliances."""
        return len(self._state.appliances_on) + sum(
            self._state.charging.fictive_on.values()
        )

    def curve_waiting_time(self, average_w: float) -> timedelta:
        """Return the waiting time from the curve for a regulation average."""
        general = self._config.general
        return timedelta(seconds=general.wait_at_limit_s) * self._waiting_curve.share(
            average_w / general.power_limit_w
        )

    @property
    def appliances_on(self) -> frozenset[str]:
        """Return the ids of the appliances the regulation has turned on."""
        return frozenset(self._state.appliances_on)

    @property
    def excluded_appliances(self) -> frozenset[str]:
        """Return the ids of the appliances excluded at the last decision."""
        return self._state.excluded_appliances

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
        commands = self._turn_off_everything()
        self._state = RegulationState(charging=self._new_charging())
        return commands

    def decide(self, decision: DecisionInput) -> list[Command]:
        """Make one decision and return the commands to carry out."""
        if not self._running:
            return []
        if self._state.safe_state:
            return self.start(decision.now) if decision.power_sensor_valid else []
        if decision.power_sensor_lost:
            self._state.safe_state = True
            return self._hold_everything_off()
        average = decision.regulation_average_w
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
            return commands + self._place_appliances(decision)
        slots_on_before = self.slots_on
        commands += self._decide_chargers(decision, overrides_ended)
        commands += self._place_appliances(decision)
        if average > self._config.general.power_limit_w:
            forced_off = self.slots_on < slots_on_before
            return commands + self._switch_off_above_limit(forced_off)
        return commands + self._turn_on_next(decision.now, average)

    def _new_charging(self) -> ChargingState:
        return ChargingState.for_chargers(list(self._chargers.values()))

    def _turn_off_everything(self) -> list[Command]:
        """Turn every appliance off as its current variant does it.

        Before the first decision after a start, that is as the appliance does it.
        """
        current_variants = self._state.current_variants
        commands: list[Command] = [
            TurnOffAppliance(appliance.id, current_variants.get(appliance.id))
            for appliance in self._config.appliances
        ]
        for charger in self._chargers.values():
            commands += self._charger_commands(charger, 0)
        return commands

    def _overrides_ended(self, decision: DecisionInput) -> list[str]:
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
        """Switch off what the chargers must, an exception to one slot per decision."""
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
        if decision.capacity_average_w is None:
            return PenaltyOutcome.NONE
        general = self._config.general
        limits = PenaltyLimits(
            power_limit_w=general.power_limit_w,
            threshold_w=general.penalty_threshold_w,
            window=timedelta(seconds=general.regulation_window_s),
        )
        return self._state.penalty.decide(
            limits, decision.capacity_average_w, decision.regulation_averages_w
        )

    def _hold_everything_off(self) -> list[Command]:
        """Turn everything off, an exception to one slot per decision."""
        self._state.appliances_on.clear()
        self._state.waiting = None
        for charger_id in self._chargers:
            self._state.charging.set_fictive_on(charger_id, 0)
        return self._turn_off_everything()

    def _place_appliances(self, decision: DecisionInput) -> list[Command]:
        """Handle the appliances that are excluded, included again or switch variant.

        An excluded appliance that is on is switched off. An appliance that
        comes to a new place, by switching variant or by being included again,
        is off afterwards and gets room there. An appliance that switches
        variant is sent the turn-off action of the new variant also when it was
        off, since the variants may turn it off in different ways. Before the
        first decision after a start, the appliance itself is the variant. The
        switch-offs are an exception to one slot per decision.
        """
        previous_variants = self._state.current_variants
        previous_excluded = self._state.excluded_appliances
        self._state.current_variants = {
            appliance.id: current_variant(appliance, decision.variant_conditions)
            for appliance in self._config.appliances
        }
        excluded = decision.excluded_appliances
        self._state.excluded_appliances = excluded
        moving = [
            appliance_id
            for appliance_id, variant in self._state.current_variants.items()
            if previous_variants.get(appliance_id) != variant
            or (appliance_id in previous_excluded and appliance_id not in excluded)
        ]
        was_on = self._state.appliances_on & set(moving)
        commands: list[Command] = []
        for appliance_id in sorted(excluded & self._state.appliances_on):
            commands += self._switch(ApplianceSlotKey(appliance_id), turn_on=False)
        places = {slot.key: place for place, slot in enumerate(self._slots())}
        for key in sorted(map(ApplianceSlotKey, moving), key=lambda key: places[key]):
            appliance_id = key.appliance_id
            was_off = appliance_id not in was_on
            switched_variant = (
                previous_variants.get(appliance_id)
                != self._state.current_variants[appliance_id]
            )
            if appliance_id in self._state.appliances_on or (
                was_off and switched_variant
            ):
                commands += self._switch(key, turn_on=False)
            if was_off and appliance_id not in excluded:
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
            self._appliance_cycling,
            fictive_slots(
                [self._chargers[charger_id] for charger_id in charging.priority],
                charging.fictive_on,
                charging.may_charge,
                charging.on_trial,
                charging.bypassed,
                self._fictive_appliance_cycling,
            ),
            self._state.excluded_appliances,
        )

    def _slots_on_lowest_first(self) -> Iterator[Slot]:
        return (
            slot for slot in reversed(self._slots()) if slot.is_on and slot.can_turn_off
        )

    def _switch_off_above_limit(self, forced_off: bool) -> list[Command]:
        """Switch off the lowest priority slot that is on.

        Nothing more is switched off when the decision has already forced
        something off, since the average was measured before that.
        """
        self._state.waiting = None
        if forced_off:
            return []
        commands: list[Command] = []
        for slot in list(islice(self._slots_on_lowest_first(), SLOTS_PER_DECISION)):
            commands += self._switch(slot.key, turn_on=False)
        return commands

    def _turn_on_next(self, now: datetime, average_w: float) -> list[Command]:
        commands: list[Command] = []
        for _ in range(SLOTS_PER_DECISION):
            candidate = next(
                (slot for slot in self._slots() if not slot.is_on and slot.can_turn_on),
                None,
            )
            if candidate is None or not self._may_turn_on(candidate, average_w):
                self._state.waiting = None
                break
            if not self._has_waited(candidate, now, average_w):
                break
            commands += self._switch(candidate.key, turn_on=True, now=now)
        return commands

    def _may_turn_on(self, slot: Slot, average_w: float) -> bool:
        """Return whether there is room to turn the slot on.

        The average must be below the limit by the turn-on margin, since the
        window after a decision still holds some of the consumption from before
        its commands.
        """
        general = self._config.general
        limit_w = general.power_limit_w
        if average_w >= limit_w - general.turn_on_margin_w:
            return False
        reserve_w = slot.power_reserve_w
        return reserve_w is None or average_w + reserve_w <= limit_w

    def _has_waited(self, slot: Slot, now: datetime, average_w: float) -> bool:
        waiting = self._state.waiting
        started_at = (
            waiting.started_at
            if waiting is not None and waiting.key == slot.key
            else now
        )
        general = self._config.general
        required = waiting_time(
            average_w,
            general.power_limit_w,
            timedelta(seconds=general.wait_at_limit_s),
            self._waiting_curve,
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
        """`now` is needed only to turn on the first fictive appliance of a charger."""
        match key:
            case ApplianceSlotKey(appliance_id):
                self._record_switch(key, turn_on)
                variant_id = self._state.current_variants.get(appliance_id)
                if turn_on:
                    self._state.appliances_on.add(appliance_id)
                    return [TurnOnAppliance(appliance_id, variant_id)]
                self._state.appliances_on.discard(appliance_id)
                return [TurnOffAppliance(appliance_id, variant_id)]
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
        """Deactivate the other chargers, an exception to one slot per decision."""
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
        """Return the commands for the charger, always setting the current first."""
        commands: list[Command] = [
            SetChargingCurrent(charger.id, charging_current(charger, count))
        ]
        if count == 0:
            commands.append(DeactivateCharger(charger.id))
        return commands

    def _record_switch(self, key: Hashable, turn_on: bool) -> None:
        self._forget_waiting(key)
        self._state.cycling.record(key, turn_on)
