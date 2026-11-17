"""The regulation engine that makes each decision."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from ..config_model import Charger, ChargerGroup, KraftvaktConfig
from .charging import (
    ChargerReading,
    ChargerStatus,
    ChargingState,
    charging_current,
    charging_permission,
    override_arms,
    override_ended,
)
from .model import (
    ActivateCharger,
    AmpereStepKey,
    ApplianceStepKey,
    Command,
    DeactivateCharger,
    DecisionInput,
    DecisionResult,
    OverrideChanges,
    RegulationState,
    SetChargingCurrent,
    Step,
    StepKey,
    TurnOffAppliance,
    TurnOnAppliance,
    Waiting,
    without_superseded,
)
from .penalty import PenaltyLimits, PenaltyOutcome, PenaltyState
from .priority import ampere_steps, build_steps, current_variant
from .waiting import RepeatedTurnOnGrowth, WaitingCurve, waiting_time


class RegulationEngine:
    """Decides which appliances are on, in priority order.

    The engine only knows what it has told the appliances to do. The
    configuration cannot change while it runs, except the power limit.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create a stopped engine for the configuration."""
        self._config = config
        self._groups = config.charger_groups
        self._chargers: dict[str, Charger] = {charger.id: charger for group in self._groups for charger in group.chargers}
        self._group_of: dict[str, ChargerGroup] = {charger.id: group for group in self._groups for charger in group.chargers}
        general = config.general
        self._waiting_curve = WaitingCurve.from_settings(general.wait_curve_steepness, general.wait_curve_pivot)
        self._appliance_growth = RepeatedTurnOnGrowth.from_waiting_at_limit(
            general.wait_at_limit_s,
            general.appliance_repeat_increment_factor,
            general.appliance_repeat_increments,
        )
        self._ampere_step_growth = RepeatedTurnOnGrowth.from_waiting_at_limit(
            general.wait_at_limit_s,
            general.charger_repeat_increment_factor,
            general.charger_repeat_increments,
        )
        self._running = False
        self._state = RegulationState(charging_groups=self._new_charging_groups())

    @property
    def running(self) -> bool:
        return self._running

    @property
    def started_at(self) -> datetime | None:
        """Return when the regulation last started, or None while stopped."""
        return self._state.started_at

    @property
    def steps_on(self) -> int:
        """Return how many steps are on: appliances and ampere steps."""
        return len(self._state.appliances_on) + sum(sum(charging.ampere_steps_on.values()) for charging in self._state.charging_groups.values())

    def use_power_limit(self, power_limit_w: int) -> None:
        """Regulate against a new power limit from the next decision."""
        general = replace(self._config.general, power_limit_w=power_limit_w)
        self._config = replace(self._config, general=general)

    def curve_waiting_time(self, average_w: float) -> timedelta:
        """Return the waiting time from the curve for a regulation average."""
        general = self._config.general
        return timedelta(seconds=general.wait_at_limit_s) * self._waiting_curve.share(average_w / general.power_limit_w)

    @property
    def appliances_on(self) -> frozenset[str]:
        return frozenset(self._state.appliances_on)

    @property
    def excluded_appliances(self) -> frozenset[str]:
        return self._state.excluded_appliances

    @property
    def current_variants(self) -> Mapping[str, str | None]:
        """Return the current variant of each appliance, None for the appliance."""
        return dict(self._state.current_variants)

    @property
    def waiting(self) -> Waiting | None:
        """Return the waiting time that runs for the next step, if any."""
        return self._state.waiting

    @property
    def safe_state(self) -> bool:
        return self._state.safe_state

    @property
    def penalty(self) -> PenaltyState:
        """Return a copy of the overconsumption state and the penalty period."""
        return replace(self._state.penalty)

    @property
    def chargers(self) -> Mapping[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return {charger_id: status for group in self._groups for charger_id, status in self._charging(group.id).status(group).items()}

    @property
    def charging_priorities(self) -> Mapping[str, list[str]]:
        """Return the chargers of each group in the order their ampere steps are interleaved, highest first."""
        return {group.id: self._charging(group.id).order(group) for group in self._groups}

    def diagnostics(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "power_limit_w": self._config.general.power_limit_w,
            "waiting_curve": self._waiting_curve,
            "appliance_growth": self._appliance_growth,
            "ampere_step_growth": self._ampere_step_growth,
            "state": self._state,
        }

    def start(self, now: datetime) -> list[Command]:
        self._running = True
        self._state = RegulationState(started_at=now, charging_groups=self._new_charging_groups())
        return self._record_commands(self._turn_off_everything(), now)

    def stop(self) -> list[Command]:
        self._running = False
        commands = self._turn_off_everything()
        self._state = RegulationState(charging_groups=self._new_charging_groups())
        return commands

    def decide(self, decision: DecisionInput) -> DecisionResult:
        """Make one decision."""
        result = self._decide(decision)
        commands = without_superseded(result.commands)
        return replace(result, commands=self._record_commands(commands, decision.now))

    def repeat_commands(
        self,
        now: datetime,
        excluded_appliances: frozenset[str],
        excluded_chargers: frozenset[str],
        chargers_without_car: frozenset[str],
    ) -> list[Command]:
        """Return the command for the current state again where it is due.

        Due means no command for the repeat interval. An activated charger
        gets its current, a deactivated one is deactivated again. Waiting
        times and repeated turn-on counters are not touched, and excluded appliances
        and chargers get nothing, nor a cloud-controlled charger while no car is connected to it.
        """
        if not self._running:
            return []
        due_at = now - timedelta(minutes=self._config.general.command_repeat_interval_min)
        state = self._state
        commands: list[Command] = []
        for appliance in self._config.appliances:
            appliance_id = appliance.id
            if appliance_id in excluded_appliances or state.appliances_commanded_at[appliance_id] > due_at:
                continue
            variant_id = state.current_variants.get(appliance_id)
            if appliance_id in state.appliances_on:
                commands.append(TurnOnAppliance(appliance_id, variant_id))
            else:
                commands.append(TurnOffAppliance(appliance_id, variant_id))
        for charger in self._chargers.values():
            if charger.id in excluded_chargers or state.chargers_commanded_at[charger.id] > due_at:
                continue
            if charger.cloud_controlled and charger.id in chargers_without_car:
                continue
            commands += self._charger_commands(charger, self._charging_of(charger.id).ampere_steps_on[charger.id])
        return self._record_commands(commands, now)

    def _decide(self, decision: DecisionInput) -> DecisionResult:
        if not self._running:
            return DecisionResult([])
        if self._state.safe_state:
            if decision.power_sensor_valid:
                return DecisionResult(self.start(decision.now))
            return DecisionResult([])
        if decision.power_sensor_lost:
            self._state.safe_state = True
            return DecisionResult(self._hold_everything_off())
        average = decision.regulation_average_w
        if average is None:
            return DecisionResult([])
        overrides = self._overrides(decision)
        penalty = self._decide_penalty(decision)
        if penalty is PenaltyOutcome.ENDED:
            return DecisionResult(self.start(decision.now), overrides)
        commands: list[Command] = []
        if penalty is PenaltyOutcome.STARTED:
            commands += self._hold_everything_off()
        if self._state.penalty.active:
            commands += self._place_appliances(decision)
            return DecisionResult(commands, overrides)
        steps_on_before = self.steps_on
        commands += self._decide_chargers(decision, overrides.ended)
        commands += self._place_appliances(decision)
        forced_off = self.steps_on < steps_on_before
        if average > self._config.general.power_limit_w:
            commands += self._switch_off_above_limit(forced_off)
        else:
            commands += self._turn_on_next(decision.now, average, forced_off)
        return DecisionResult(commands, overrides)

    def _new_charging_groups(self) -> dict[str, ChargingState]:
        return {group.id: ChargingState.for_chargers(group.chargers) for group in self._groups}

    def _charging(self, group_id: str) -> ChargingState:
        return self._state.charging_groups[group_id]

    def _charging_of(self, charger_id: str) -> ChargingState:
        return self._charging(self._group_of[charger_id].id)

    def _turn_off_everything(self) -> list[Command]:
        """Turn every appliance off as its current variant does it.

        Before the first decision after a start, that is as the appliance does it.
        """
        current_variants = self._state.current_variants
        commands: list[Command] = [TurnOffAppliance(appliance.id, current_variants.get(appliance.id)) for appliance in self._config.appliances]
        for charger in self._chargers.values():
            commands += self._charger_commands(charger, 0)
        return commands

    def _overrides(self, decision: DecisionInput) -> OverrideChanges:
        """Return the overrides that arm or end at the decision."""
        changes = OverrideChanges()
        window = timedelta(seconds=self._config.general.regulation_window_s)
        for charger in self._chargers.values():
            reading = decision.chargers.get(charger.id, ChargerReading())
            charging = self._charging_of(charger.id)
            activated = charging.ampere_steps_on[charger.id] > 0
            if override_ended(charger, reading, charging.becomes_done(charger, reading, decision.now, window)):
                changes.ended.append(charger.id)
            elif override_arms(charger, reading, activated):
                changes.armed.append(charger.id)
        return changes

    def _decide_chargers(self, decision: DecisionInput, ended_overrides: list[str]) -> list[Command]:
        """Switch off what the chargers must, an exception to one step per decision."""
        local_time = decision.now.astimezone(decision.time_zone).time()
        readings = {charger_id: decision.chargers.get(charger_id, ChargerReading()) for charger_id in self._chargers}
        permissions = {
            charger.id: charging_permission(
                charger,
                readings[charger.id],
                readings[charger.id].window_override and charger.id not in ended_overrides,
                local_time,
                self._charging_of(charger.id).counts_as_charging(charger.id, readings[charger.id]),
            )
            for charger in self._chargers.values()
        }
        commands: list[Command] = []
        for group in self._groups:
            charging = self._charging(group.id)
            changes = charging.evaluate(group, readings, permissions, decision.now, timedelta(seconds=self._config.general.regulation_window_s))
            for charger_id in charging.activated():
                if charging.must_deactivate(group, charger_id):
                    commands += self._set_ampere_steps_on(charger_id, 0)
            for charger_id in changes.bypassed + changes.grace:
                if charging.ampere_steps_on[charger_id] > 1:
                    commands += self._set_ampere_steps_on(charger_id, 1)
        return commands

    def _decide_penalty(self, decision: DecisionInput) -> PenaltyOutcome:
        if decision.tariff_average_w is None:
            return PenaltyOutcome.NONE
        general = self._config.general
        limits = PenaltyLimits(
            power_limit_w=general.power_limit_w,
            threshold_w=general.penalty_threshold_w,
            window=timedelta(seconds=general.regulation_window_s),
        )
        return self._state.penalty.decide(limits, decision.tariff_average_w, decision.regulation_averages_w)

    def _hold_everything_off(self) -> list[Command]:
        """Turn everything off, an exception to one step per decision."""
        self._state.appliances_on.clear()
        self._state.waiting = None
        for charger_id in self._chargers:
            self._charging_of(charger_id).set_ampere_steps_on(charger_id, 0)
        return self._turn_off_everything()

    def _place_appliances(self, decision: DecisionInput) -> list[Command]:
        """Handle the appliances that are excluded, included again or switch variant.

        An excluded appliance that is on is switched off. An appliance at a new
        place is off afterwards and gets room there. A variant switch sends the
        turn-off action of the new variant also when the appliance was off,
        since variants may turn it off in different ways. Before the first
        decision after a start, the appliance itself is the variant. These
        switch-offs are not limited to one step per decision.
        """
        previous_variants = self._state.current_variants
        previous_excluded = self._state.excluded_appliances
        self._state.current_variants = {appliance.id: current_variant(appliance, decision.variant_conditions) for appliance in self._config.appliances}
        excluded = decision.excluded_appliances
        self._state.excluded_appliances = excluded
        moving = [
            appliance_id
            for appliance_id, variant in self._state.current_variants.items()
            if previous_variants.get(appliance_id) != variant or (appliance_id in previous_excluded and appliance_id not in excluded)
        ]
        was_on = self._state.appliances_on & set(moving)
        commands: list[Command] = []
        for appliance_id in sorted(excluded & self._state.appliances_on):
            commands += self._switch(ApplianceStepKey(appliance_id), turn_on=False)
        places = {step.key: place for place, step in enumerate(self._steps())}
        for key in sorted(map(ApplianceStepKey, moving), key=lambda key: places[key]):
            appliance_id = key.appliance_id
            was_off = appliance_id not in was_on
            switched_variant = previous_variants.get(appliance_id) != self._state.current_variants[appliance_id]
            if appliance_id in self._state.appliances_on or (was_off and switched_variant):
                commands += self._switch(key, turn_on=False)
            if was_off and appliance_id not in excluded:
                commands += self._make_room_below(key)
            self._forget_waiting(key)
            self._state.repeats.reset(key)
        return commands

    def _steps(self) -> list[Step]:
        return build_steps(
            self._config,
            self._state.current_variants,
            self._state.appliances_on,
            self._appliance_growth,
            {group.id: self._ampere_steps(group) for group in self._groups},
            self._state.excluded_appliances,
        )

    def _ampere_steps(self, group: ChargerGroup) -> list[Step]:
        charging = self._charging(group.id)
        return ampere_steps(
            group.id,
            [[self._chargers[charger_id] for charger_id in block] for block in charging.blocks(group)],
            charging.ampere_steps_on,
            charging.may_charge,
            charging.on_trial,
            charging.bypassed,
            charging.starting,
            self._ampere_step_growth,
        )

    def _steps_on_lowest_first(self) -> Iterator[Step]:
        return (step for step in reversed(self._steps()) if step.is_on and step.can_turn_off)

    def _switch_off_above_limit(self, forced_off: bool) -> list[Command]:
        """Switch off the lowest priority step that is on.

        Nothing more is switched off when the decision has already forced
        something off, since the average was measured before that.
        """
        self._state.waiting = None
        lowest_on = next(self._steps_on_lowest_first(), None)
        if forced_off or lowest_on is None:
            return []
        return self._switch(lowest_on.key, turn_on=False)

    def _make_room_below(self, key: StepKey) -> list[Command]:
        """Switch off the lowest step that is on below the step.

        Room for a charger's first ampere step that would be taken from
        another charger of its group is taken at once: every charger of the
        group that is on above its minimum below the step is set to its
        minimum, an exception to one step per decision.
        """
        steps = self._steps()
        place = next(place for place, step in enumerate(steps) if step.key == key)
        below_on = [step for step in steps[place + 1 :] if step.is_on and step.can_turn_off]
        if not below_on:
            return []
        lowest_on = below_on[-1]
        group_id = steps[place].group_id
        if _is_first_ampere_step(key) and lowest_on.group_id == group_id and not _is_first_ampere_step(lowest_on.key):
            above_minimum = dict.fromkeys(step.key.charger_id for step in below_on if step.group_id == group_id and isinstance(step.key, AmpereStepKey) and step.key.index > 0)
            return [command for charger_id in above_minimum for command in self._set_ampere_steps_on(charger_id, 1)]
        return self._switch(lowest_on.key, turn_on=False)

    def _turn_on_next(self, now: datetime, average_w: float, forced_off: bool) -> list[Command]:
        """Make a switch-over, or turn on the next step, or make room for it when there is none.

        No room is made, and no switch-over, when the decision has already
        forced something off, since the average was measured before that. The
        power reserves held for starting chargers above the step, and in its
        own group, count as used, also for its waiting time.
        """
        steps = self._steps()
        place = next((place for place, step in enumerate(steps) if not step.is_on and step.can_turn_on), None)
        switch_over = None if forced_off else self._switch_over(steps, place, now, average_w)
        if switch_over is not None:
            return switch_over
        if place is None:
            self._state.waiting = None
            return []
        candidate = steps[place]
        held_w = _held_reserves_w(steps, place)
        if not self._may_turn_on(candidate, average_w + held_w):
            self._state.waiting = None
            return [] if forced_off else self._make_room_below(candidate.key)
        if not self._has_waited(candidate, now, average_w + held_w):
            return []
        return self._switch(candidate.key, turn_on=True, now=now)

    def _switch_over(self, steps: list[Step], place: int | None, now: datetime, average_w: float) -> list[Command] | None:
        """Return the commands of a switch-over when one is due, an empty list while its waiting time runs, or None.

        The queued charger may start when the free power, plus what the chargers
        that charge above their minimum current draw above their power reserves,
        covers its reserve, also when none of them is above its minimum.
        Nothing above the group may be waiting for room, and no charger of the
        group may be starting, since its charging power would then be from
        before the last switch-over.
        """
        for group in self._groups:
            charging = self._charging(group.id)
            queued = charging.queued(group)
            if not charging.shares_by_charging_power(group) or charging.starting or not queued:
                continue
            group_places = [index for index, step in enumerate(steps) if step.group_id == group.id]
            if place is not None and place < group_places[0]:
                continue
            above_minimum = [charger_id for charger_id in charging.charging if charging.ampere_steps_on[charger_id] > 1]
            freed_w = sum(max(0.0, (charging.last_readings[charger_id].charging_power_w or 0.0) - self._chargers[charger_id].power_reserve_w) for charger_id in above_minimum)
            key = AmpereStepKey(queued[0], 0)
            step = next(step for step in steps if step.key == key)
            held_w = _held_reserves_w(steps, group_places[0])
            if not self._may_turn_on(step, average_w + held_w - freed_w):
                continue
            if not self._has_waited(step, now, average_w + held_w):
                return []
            commands: list[Command] = []
            for charger_id in sorted(above_minimum, key=charging.order(group).index):
                commands += self._set_ampere_steps_on(charger_id, 1)
            return commands + self._switch(key, turn_on=True, now=now)
        return None

    def _may_turn_on(self, step: Step, average_w: float) -> bool:
        """Return whether there is room to turn the step on.

        The average must be below the limit by the turn-on margin, since the
        window after a decision still holds some of the consumption from before
        its commands.
        """
        general = self._config.general
        limit_w = general.power_limit_w
        if average_w >= limit_w - general.turn_on_margin_w:
            return False
        reserve_w = step.power_reserve_w
        return reserve_w is None or average_w + reserve_w <= limit_w

    def _has_waited(self, step: Step, now: datetime, average_w: float) -> bool:
        waiting = self._state.waiting
        started_at = waiting.started_at if waiting is not None and waiting.key == step.key else now
        general = self._config.general
        required = waiting_time(
            average_w,
            general.power_limit_w,
            timedelta(seconds=general.wait_at_limit_s),
            self._waiting_curve,
            self._state.repeats.upcoming_repeat(step.key),
            step.growth,
        )
        self._state.waiting = Waiting(step.key, started_at, started_at + required)
        return now - started_at >= required

    def _forget_waiting(self, key: StepKey) -> None:
        if self._state.waiting is not None and self._state.waiting.key == key:
            self._state.waiting = None

    def _switch(self, key: StepKey, turn_on: bool, now: datetime | None = None) -> list[Command]:
        """`now` is needed only to turn on the first ampere step of a charger."""
        if isinstance(key, ApplianceStepKey):
            appliance_id = key.appliance_id
            self._record_switch(key, turn_on)
            variant_id = self._state.current_variants.get(appliance_id)
            if turn_on:
                self._state.appliances_on.add(appliance_id)
                return [TurnOnAppliance(appliance_id, variant_id)]
            self._state.appliances_on.discard(appliance_id)
            return [TurnOffAppliance(appliance_id, variant_id)]
        commands = self._deactivate_others(key.charger_id) if turn_on and key.index == 0 else []
        count = key.index + 1 if turn_on else key.index
        return commands + self._set_ampere_steps_on(key.charger_id, count, now)

    def _deactivate_others(self, charger_id: str) -> list[Command]:
        """Deactivate the others in the group, an exception to one step per decision."""
        if not self._group_of[charger_id].one_at_a_time:
            return []
        commands: list[Command] = []
        for other_id in self._charging_of(charger_id).activated():
            if other_id != charger_id:
                commands += self._set_ampere_steps_on(other_id, 0)
        return commands

    def _set_ampere_steps_on(self, charger_id: str, count: int, now: datetime | None = None) -> list[Command]:
        charging = self._charging_of(charger_id)
        before = charging.ampere_steps_on[charger_id]
        turn_on = count > before
        for index in range(min(before, count), max(before, count)):
            self._record_switch(AmpereStepKey(charger_id, index), turn_on)
        charging.set_ampere_steps_on(charger_id, count, now)
        return self._charger_commands(self._chargers[charger_id], count, activate=before == 0 and count > 0)

    def _charger_commands(self, charger: Charger, count: int, activate: bool = False) -> list[Command]:
        """Return the commands for the charger, always setting the current first.

        A charger switched by its current gets only the current: 0 A to
        deactivate it, and its minimum current to activate it.
        """
        if charger.switched_by_current:
            return [SetChargingCurrent(charger.id, charging_current(charger, count) if count else 0)]
        commands: list[Command] = [SetChargingCurrent(charger.id, charging_current(charger, count))]
        if count == 0:
            commands.append(DeactivateCharger(charger.id))
        elif activate:
            commands.append(ActivateCharger(charger.id))
        return commands

    def _record_commands(self, commands: list[Command], now: datetime) -> list[Command]:
        """Note when each appliance and charger in the commands got a command."""
        for command in commands:
            match command:
                case TurnOnAppliance(appliance_id) | TurnOffAppliance(appliance_id):
                    self._state.appliances_commanded_at[appliance_id] = now
                case ActivateCharger(charger_id) | DeactivateCharger(charger_id) | SetChargingCurrent(charger_id):
                    self._state.chargers_commanded_at[charger_id] = now
        return commands

    def _record_switch(self, key: StepKey, turn_on: bool) -> None:
        self._forget_waiting(key)
        self._state.repeats.record(key, turn_on)


def _is_first_ampere_step(key: StepKey) -> bool:
    return isinstance(key, AmpereStepKey) and key.index == 0


def _held_reserves_w(steps: list[Step], place: int) -> float:
    """Return the power reserves held for starting chargers above the place, and in the group of the step at the place."""
    group_id = steps[place].group_id
    return sum(
        step.power_reserve_w or 0
        for index, step in enumerate(steps)
        if step.holds_reserve and index != place and (index < place or (group_id is not None and step.group_id == group_id))
    )
