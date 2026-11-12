"""The regulation engine that makes each decision."""

from __future__ import annotations

from collections.abc import Hashable, Iterator, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from itertools import islice
from typing import Final

from ..config_model import Charger, ChargerGroup, KraftvaktConfig
from .charging import (
    ChargerReading,
    ChargerStatus,
    ChargingState,
    allowed_to_charge,
    charging_current,
    finishing_after_window,
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

SLOTS_PER_DECISION: Final = 1


class RegulationEngine:
    """Decides which appliances are on, in priority order.

    The engine only knows what it has told the appliances to do. The
    configuration cannot change while it runs, so it is given once.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create a stopped engine for the configuration."""
        self._config = config
        self._groups = config.charger_groups
        self._chargers: dict[str, Charger] = {
            charger.id: charger for group in self._groups for charger in group.chargers
        }
        self._group_of: dict[str, ChargerGroup] = {
            charger.id: group for group in self._groups for charger in group.chargers
        }
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
        self._state = RegulationState(charging_groups=self._new_charging_groups())

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
            sum(charging.fictive_on.values())
            for charging in self._state.charging_groups.values()
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
        return {
            charger_id: status
            for group in self._groups
            for charger_id, status in self._charging(group.id)
            .status(group.chargers)
            .items()
        }

    @property
    def charging_priorities(self) -> Mapping[str, list[str]]:
        """Return the current charging priority of each group, highest first."""
        return {
            group_id: list(charging.priority)
            for group_id, charging in self._state.charging_groups.items()
        }

    def start(self, now: datetime) -> list[Command]:
        """Start the regulation with a new state and everything off."""
        self._running = True
        self._state = RegulationState(
            started_at=now, charging_groups=self._new_charging_groups()
        )
        return self._record_commands(self._turn_off_everything(), now)

    def stop(self) -> list[Command]:
        """Stop the regulation and turn everything off."""
        self._running = False
        commands = self._turn_off_everything()
        self._state = RegulationState(charging_groups=self._new_charging_groups())
        return commands

    def decide(self, decision: DecisionInput) -> list[Command]:
        """Make one decision and return the commands to carry out."""
        commands = _last_command_per_appliance(self._decide(decision))
        return self._record_commands(commands, decision.now)

    def repeat_commands(
        self,
        now: datetime,
        excluded_appliances: frozenset[str],
        excluded_chargers: frozenset[str],
    ) -> list[Command]:
        """Return the command for the current state again where it is due.

        Due means no command for the repeat interval. An activated charger
        gets its current, a deactivated one is deactivated again. Waiting
        times and cycling counters are not touched, and excluded appliances
        and chargers get nothing.
        """
        if not self._running:
            return []
        due_at = now - timedelta(
            minutes=self._config.general.command_repeat_interval_min
        )
        state = self._state
        commands: list[Command] = []
        for appliance in self._config.appliances:
            appliance_id = appliance.id
            if (
                appliance_id in excluded_appliances
                or state.appliances_commanded_at[appliance_id] > due_at
            ):
                continue
            variant_id = state.current_variants.get(appliance_id)
            if appliance_id in state.appliances_on:
                commands.append(TurnOnAppliance(appliance_id, variant_id))
            else:
                commands.append(TurnOffAppliance(appliance_id, variant_id))
        for charger in self._chargers.values():
            if (
                charger.id in excluded_chargers
                or state.chargers_commanded_at[charger.id] > due_at
            ):
                continue
            commands += self._charger_commands(
                charger, self._charging_of(charger.id).fictive_on[charger.id]
            )
        return self._record_commands(commands, now)

    def _decide(self, decision: DecisionInput) -> list[Command]:
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
        forced_off = self.slots_on < slots_on_before
        if average > self._config.general.power_limit_w:
            return commands + self._switch_off_above_limit(forced_off)
        return commands + self._turn_on_next(decision.now, average, forced_off)

    def _new_charging_groups(self) -> dict[str, ChargingState]:
        return {
            group.id: ChargingState.for_chargers(group.chargers)
            for group in self._groups
        }

    def _charging(self, group_id: str) -> ChargingState:
        return self._state.charging_groups[group_id]

    def _charging_of(self, charger_id: str) -> ChargingState:
        """Return the state of the group the charger is in."""
        return self._charging(self._group_of[charger_id].id)

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
        activated = {
            charger_id
            for group in self._groups
            for charger_id in self._charging(group.id).activated()
        }
        finishing = [
            charger.id
            for charger in self._chargers.values()
            if finishing_after_window(
                charger,
                readings[charger.id],
                override_active[charger.id],
                local_time,
                charger.id in activated,
            )
        ]
        allowed = finishing + [
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
        commands: list[Command] = []
        for group in self._groups:
            charging = self._charging(group.id)
            newly_bypassed = charging.evaluate(
                group.chargers,
                readings,
                allowed,
                decision.now,
                timedelta(seconds=self._config.general.regulation_window_s),
                group.one_at_a_time,
                overridden,
                finishing,
            )
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
            self._charging_of(charger_id).set_fictive_on(charger_id, 0)
        return self._turn_off_everything()

    def _place_appliances(self, decision: DecisionInput) -> list[Command]:
        """Handle the appliances that are excluded, included again or switch variant.

        An excluded appliance that is on is switched off. An appliance at a new
        place is off afterwards and gets room there. A variant switch sends the
        turn-off action of the new variant also when the appliance was off,
        since variants may turn it off in different ways. Before the first
        decision after a start, the appliance itself is the variant. These
        switch-offs are not limited to one slot per decision.
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
                commands += self._make_room_below(key)
            self._forget_waiting(key)
            self._state.cycling.reset(key)
        return commands

    def _slots(self) -> list[Slot]:
        return build_slots(
            self._config,
            self._state.current_variants,
            self._state.appliances_on,
            self._appliance_cycling,
            {
                group_id: self._fictive_slots(charging)
                for group_id, charging in self._state.charging_groups.items()
            },
            self._state.excluded_appliances,
        )

    def _fictive_slots(self, charging: ChargingState) -> list[Slot]:
        return fictive_slots(
            [self._chargers[charger_id] for charger_id in charging.priority],
            charging.fictive_on,
            charging.may_charge,
            charging.on_trial,
            charging.bypassed,
            self._fictive_appliance_cycling,
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

    def _make_room_below(self, key: Hashable) -> list[Command]:
        """Switch off the lowest slot that is on below the slot, if any."""
        slots = self._slots()
        place = next(place for place, slot in enumerate(slots) if slot.key == key)
        lowest_on = next(
            (
                slot
                for slot in reversed(slots[place + 1 :])
                if slot.is_on and slot.can_turn_off
            ),
            None,
        )
        if lowest_on is None:
            return []
        return self._switch(lowest_on.key, turn_on=False)

    def _turn_on_next(
        self, now: datetime, average_w: float, forced_off: bool
    ) -> list[Command]:
        """Turn on the next slot, or make room for it when there is none.

        No room is made when the decision has already forced something off,
        since the average was measured before that.
        """
        commands: list[Command] = []
        for _ in range(SLOTS_PER_DECISION):
            candidate = next(
                (slot for slot in self._slots() if not slot.is_on and slot.can_turn_on),
                None,
            )
            if candidate is None:
                self._state.waiting = None
                break
            if not self._may_turn_on(candidate, average_w):
                self._state.waiting = None
                if not forced_off:
                    commands += self._make_room_below(candidate.key)
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
        """Deactivate the others in the group, an exception to one slot per decision."""
        if not self._group_of[charger_id].one_at_a_time:
            return []
        commands: list[Command] = []
        for other_id in self._charging_of(charger_id).activated():
            if other_id != charger_id:
                commands += self._set_fictive_on(other_id, 0)
        return commands

    def _set_fictive_on(
        self, charger_id: str, count: int, now: datetime | None = None
    ) -> list[Command]:
        charging = self._charging_of(charger_id)
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

    def _record_commands(self, commands: list[Command], now: datetime) -> list[Command]:
        """Note when each appliance and charger in the commands got a command."""
        for command in commands:
            match command:
                case TurnOnAppliance(appliance_id) | TurnOffAppliance(appliance_id):
                    self._state.appliances_commanded_at[appliance_id] = now
                case (
                    ActivateCharger(charger_id)
                    | DeactivateCharger(charger_id)
                    | SetChargingCurrent(charger_id)
                ):
                    self._state.chargers_commanded_at[charger_id] = now
        return commands

    def _record_switch(self, key: Hashable, turn_on: bool) -> None:
        self._forget_waiting(key)
        self._state.cycling.record(key, turn_on)


def _last_command_per_appliance(commands: list[Command]) -> list[Command]:
    """Keep only the last command for each appliance.

    An appliance turned off and on again at the same decision only gets the
    turn-on, since switching a device off and on at once wears its relays.
    """
    last = {
        command.appliance_id: index
        for index, command in enumerate(commands)
        if isinstance(command, TurnOnAppliance | TurnOffAppliance)
    }
    return [
        command
        for index, command in enumerate(commands)
        if not isinstance(command, TurnOnAppliance | TurnOffAppliance)
        or last[command.appliance_id] == index
    ]
