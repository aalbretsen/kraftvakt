"""The regulation engine that makes each decision."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from ..config_model import Charger, ChargerGroup, KraftvaktConfig
from .charging import (
    ChargerReading,
    ChargerState,
    ChargerStatus,
    ChargingState,
    charges_in_window,
    charging_current,
    charging_permission,
    estimated_draw_w,
    override_arms,
    override_ended,
)
from .model import (
    ActivateCharger,
    AmpereStepKey,
    ApplianceStepKey,
    ChargedInWindowChanges,
    Command,
    DeactivateCharger,
    DecisionInput,
    DecisionResult,
    OverrideChanges,
    PowerToFree,
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
from .waiting import RepeatedTurnOnGrowth, WaitingCurve, curve_waiting_time, waiting_time


class RegulationEngine:
    """Decides which appliances are on, in priority order.

    The engine only knows what it has told the appliances to do. The
    configuration cannot change while it runs, except the power limit.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        self._config = config
        self._groups = config.charger_groups
        self._chargers: dict[str, Charger] = {charger.id: charger for group in self._groups for charger in group.chargers}
        self._group_of: dict[str, ChargerGroup] = {charger.id: group for group in self._groups for charger in group.chargers}
        self._essential = frozenset(appliance.id for appliance in config.appliances if appliance.essential)
        general = config.general
        self._waiting_curve = WaitingCurve.from_settings(general.wait_curve_steepness, general.wait_curve_pivot)
        self._appliance_growth = RepeatedTurnOnGrowth.from_waiting_at_limit(
            general.wait_at_limit_s,
            general.appliance_repeat_increment_factor,
            general.appliance_repeat_increments,
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
        """Return how many steps are on: appliances that are not essential, and ampere steps."""
        return len(self._state.appliances_on - self._essential) + self._ampere_steps_on()

    def use_power_limit(self, power_limit_w: int) -> None:
        """Regulate against a new power limit from the next decision."""
        general = replace(self._config.general, power_limit_w=power_limit_w)
        self._config = replace(self._config, general=general)

    def curve_waiting_time(self, average_w: float) -> timedelta:
        """Return the waiting time from the curve for a regulation average."""
        general = self._config.general
        return curve_waiting_time(average_w, general.power_limit_w, timedelta(seconds=general.wait_at_limit_s), self._waiting_curve)

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
    def power_to_free(self) -> PowerToFree | None:
        """Return how far the regulation average had to drop at the last decision before the next step could be turned on, if it had to."""
        return self._state.power_to_free

    @property
    def safe_state(self) -> bool:
        return self._state.safe_state

    @property
    def penalty(self) -> PenaltyState:
        """Return a copy of the overconsumption state and the penalty period."""
        return replace(self._state.penalty)

    @property
    def chargers(self) -> Mapping[str, ChargerStatus]:
        """Return how each charger stands after the last decision, and stopped while the regulation is stopped."""
        statuses = {charger_id: status for group in self._groups for charger_id, status in self._charging(group.id).status(group).items()}
        if self._running:
            return statuses
        return {charger_id: replace(status, state=ChargerState.STOPPED) for charger_id, status in statuses.items()}

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
            "state": self._state,
        }

    def start(self, now: datetime, excluded_appliances: frozenset[str] = frozenset()) -> list[Command]:
        """Start with everything off, except the essential appliances that are not excluded."""
        self._running = True
        self._state = RegulationState(started_at=now, charging_groups=self._new_charging_groups(), excluded_appliances=excluded_appliances)
        return self._record_commands(self._hold_everything_off(essential_on=True), now)

    def stop(self, excluded_appliances: frozenset[str] = frozenset()) -> list[Command]:
        """Stop with everything off, except the essential appliances that are not excluded, so a stop during a penalty does not leave them off."""
        self._running = False
        self._state.excluded_appliances = excluded_appliances
        commands = self._hold_everything_off(essential_on=True)
        self._state = RegulationState(charging_groups=self._new_charging_groups())
        return commands

    def decide(self, decision: DecisionInput) -> DecisionResult:
        charged_in_window = self._charged_in_window(decision)
        result = self._decide(decision)
        commands = without_superseded(result.commands)
        return replace(result, commands=self._record_commands(commands, decision.now), charged_in_window=charged_in_window)

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
        self._state.power_to_free = None
        if self._state.safe_state:
            if decision.power_sensor_valid:
                return DecisionResult(self.start(decision.now, decision.excluded_appliances))
            return DecisionResult([])
        if decision.power_sensor_lost:
            self._state.safe_state = True
            return DecisionResult(self._hold_everything_off(essential_on=True))
        average = decision.regulation_average_w
        if average is None:
            return DecisionResult([])
        self._forget_settled(decision.window_start)
        self._forget_damping(decision.now)
        overrides = self._overrides(decision)
        penalty = self._decide_penalty(decision)
        if penalty is PenaltyOutcome.ENDED:
            return DecisionResult(self.start(decision.now, decision.excluded_appliances), overrides)
        commands: list[Command] = []
        if penalty is PenaltyOutcome.STARTED:
            commands += self._hold_everything_off(essential_on=False)
        if self._state.penalty.active:
            commands += self._place_appliances(decision)
            return DecisionResult(commands, overrides)
        appliances_on_before = set(self._state.appliances_on)
        ampere_steps_on_before = self._ampere_steps_on()
        commands += self._decide_chargers(decision, overrides.ended)
        commands += self._place_appliances(decision)
        forced_off = bool(appliances_on_before - self._state.appliances_on) or self._ampere_steps_on() < ampere_steps_on_before
        if average > self._config.general.power_limit_w:
            commands += self._switch_off_above_limit(average, forced_off, decision.now)
        else:
            commands += self._turn_on_next(decision.now, average, forced_off)
        self._state.power_to_free = self._power_to_free(average)
        return DecisionResult(commands, overrides)

    def _forget_settled(self, window_start: datetime) -> None:
        """Keep the steps turned on since the start of the regulation window of the decision, since its average shows them only in part."""
        self._state.settling_since = {key: since for key, since in self._state.settling_since.items() if since >= window_start}

    def _forget_damping(self, now: datetime) -> None:
        self._state.damped_since = {key: since for key, since in self._state.damped_since.items() if now < since + self._ampere_damping_time}

    @property
    def _ampere_damping_time(self) -> timedelta:
        return timedelta(seconds=self._config.general.ampere_damping_s)

    def _damping(self, key: StepKey) -> Waiting | None:
        """Return the damping of an ampere step taken back for power, while it lasts."""
        since = self._state.damped_since.get(key) if isinstance(key, AmpereStepKey) else None
        return None if since is None else Waiting(key, since, since + self._ampere_damping_time)

    def _new_charging_groups(self) -> dict[str, ChargingState]:
        return {group.id: ChargingState.for_chargers(group.chargers) for group in self._groups}

    def _charging(self, group_id: str) -> ChargingState:
        return self._state.charging_groups[group_id]

    def _charging_of(self, charger_id: str) -> ChargingState:
        return self._charging(self._group_of[charger_id].id)

    def _ampere_steps_on(self) -> int:
        return sum(sum(charging.ampere_steps_on.values()) for charging in self._state.charging_groups.values())

    def _overrides(self, decision: DecisionInput) -> OverrideChanges:
        """Return the overrides that arm or end at the decision."""
        changes = OverrideChanges()
        for charger in self._chargers.values():
            reading = decision.chargers.get(charger.id, ChargerReading())
            activated = self._charging_of(charger.id).ampere_steps_on[charger.id] > 0
            if override_ended(charger, reading, activated):
                changes.ended.append(charger.id)
            elif override_arms(charger, reading, activated):
                changes.armed.append(charger.id)
        return changes

    def _charged_in_window(self, decision: DecisionInput) -> ChargedInWindowChanges:
        """Return the chargers that start or stop counting as charged in their charging window, judged before the commands of the decision.

        Also judged in the safe state and during a penalty, so a car that is
        disconnected meanwhile does not leave the next car allowed.
        """
        changes = ChargedInWindowChanges()
        if not self._running:
            return changes
        local_time = decision.now.astimezone(decision.time_zone).time()
        for charger in self._chargers.values():
            reading = decision.chargers.get(charger.id, ChargerReading())
            if reading.car_disconnected:
                if reading.charged_in_window:
                    changes.removed.append(charger.id)
            elif not reading.charged_in_window and charges_in_window(charger, reading, self._charging_of(charger.id).ampere_steps_on[charger.id] > 0, local_time):
                changes.added.append(charger.id)
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
            )
            for charger in self._chargers.values()
        }
        commands: list[Command] = []
        for group in self._groups:
            charging = self._charging(group.id)
            newly_bypassed = charging.evaluate(group, readings, permissions, decision.now)
            for charger_id in charging.activated():
                if charging.must_deactivate(group, charger_id):
                    commands += self._set_ampere_steps_on(charger_id, 0)
                elif (charger_id in newly_bypassed or charger_id in charging.held_at_min) and charging.ampere_steps_on[charger_id] > 1:
                    commands += self._set_ampere_steps_on(charger_id, 1)
        return commands

    def _decide_penalty(self, decision: DecisionInput) -> PenaltyOutcome:
        if decision.tariff_average_w is None:
            return PenaltyOutcome.NONE
        general = self._config.general
        limits = PenaltyLimits(power_limit_w=general.power_limit_w, threshold_w=general.penalty_threshold_w)
        return self._state.penalty.decide(limits, decision.tariff_average_w, decision.regulation_averages)

    def _hold_everything_off(self, essential_on: bool) -> list[Command]:
        """Send every appliance and charger the command for off, an exception to one step per decision.

        With `essential_on`, the essential appliances that are not excluded
        are turned on instead. An appliance is turned off as its current
        variant does it, which before the first decision after a start is as
        the appliance does it.
        """
        state = self._state
        state.appliances_on = set(self._essential - state.excluded_appliances) if essential_on else set()
        state.waiting = None
        state.settling_since = {}
        commands: list[Command] = []
        for appliance in self._config.appliances:
            variant_id = state.current_variants.get(appliance.id)
            on = appliance.id in state.appliances_on
            commands.append(TurnOnAppliance(appliance.id, variant_id) if on else TurnOffAppliance(appliance.id, variant_id))
        for charger in self._chargers.values():
            self._charging_of(charger.id).set_ampere_steps_on(charger.id, 0)
            commands += self._charger_commands(charger, 0)
        return commands

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
        included_again = previous_excluded - excluded
        moving = [
            appliance_id
            for appliance_id, variant in self._state.current_variants.items()
            if appliance_id not in self._essential and (previous_variants.get(appliance_id) != variant or appliance_id in included_again)
        ]
        was_on = self._state.appliances_on & set(moving)
        commands = self._place_essential_appliances()
        for appliance_id in sorted((excluded & self._state.appliances_on) - self._essential):
            commands += self._switch(ApplianceStepKey(appliance_id), turn_on=False)
        places = {step.key: place for place, step in enumerate(self._steps())}
        for key in sorted(map(ApplianceStepKey, moving), key=lambda key: places[key]):
            appliance_id = key.appliance_id
            was_off = appliance_id not in was_on
            switched_variant = previous_variants.get(appliance_id) != self._state.current_variants[appliance_id]
            if appliance_id in self._state.appliances_on or (was_off and switched_variant):
                commands += self._switch(key, turn_on=False)
            if was_off and appliance_id not in excluded:
                commands += self._make_room_below(key, decision.now)
            self._forget_waiting(key)
            self._state.repeats.reset(key)
        return commands

    def _place_essential_appliances(self) -> list[Command]:
        """Turn each essential appliance on, or off while it is excluded or a penalty lasts.

        It is no step, so it neither waits nor counts against one step per
        decision, and leaves the repeated turn-on counters alone.
        """
        state = self._state
        commands: list[Command] = []
        for appliance in self._config.appliances:
            if not appliance.essential:
                continue
            on = appliance.id not in state.excluded_appliances and not state.penalty.active
            if on == (appliance.id in state.appliances_on):
                continue
            if on:
                state.appliances_on.add(appliance.id)
                commands.append(TurnOnAppliance(appliance.id))
            else:
                state.appliances_on.discard(appliance.id)
                commands.append(TurnOffAppliance(appliance.id))
        return commands

    def _steps(self) -> list[Step]:
        return build_steps(
            self._config,
            self._state.current_variants,
            self._state.appliances_on,
            {group.id: self._ampere_steps(group) for group in self._groups},
            self._state.excluded_appliances,
            self._state.settling_since.keys(),
        )

    def _ampere_steps(self, group: ChargerGroup) -> list[Step]:
        charging = self._charging(group.id)
        blocks = [[self._chargers[charger_id] for charger_id in block] for block in charging.blocks(group)]
        return ampere_steps(group.id, blocks, charging, self._state.settling_since.keys())

    def _steps_on_lowest_first(self) -> Iterator[Step]:
        return (step for step in reversed(self._steps()) if step.is_on and step.can_turn_off)

    def _switch_off_above_limit(self, average_w: float, forced_off: bool, now: datetime) -> list[Command]:
        """Switch off the lowest priority steps that are on, as many as the power above the limit needs.

        Nothing more is switched off when the decision has already forced
        something off, since the average was measured before that.
        """
        self._state.waiting = None
        if forced_off:
            return []
        return self._free_power(list(self._steps_on_lowest_first()), average_w - self._config.general.power_limit_w, now)

    def _make_room_below(self, key: StepKey, now: datetime) -> list[Command]:
        """Switch off the lowest step that is on below the step."""
        steps = self._steps()
        place = next(place for place, step in enumerate(steps) if step.key == key)
        below_on = _steps_on_below(steps, place)
        return self._take_back(below_on[0].key, now) if below_on else []

    def _take_back(self, key: StepKey, now: datetime) -> list[Command]:
        """Switch off a step for power. An ampere step is damped from now."""
        if isinstance(key, AmpereStepKey):
            self._state.damped_since[key] = now
        return self._switch(key, turn_on=False)

    def _free_power(self, steps_lowest_first: list[Step], needed_w: float, now: datetime) -> list[Command]:
        """Switch off steps, lowest first, until the power they are estimated to free covers `needed_w`.

        Only what a charger draws is known, from its charging power, so an
        appliance ends it: it is switched off only when it is the first.
        At least one step is switched off when any is on. These switch-offs are
        an exception to one step per decision.
        """
        commands: list[Command] = []
        draws_before: dict[str, float] = {}
        for step in steps_lowest_first:
            if isinstance(step.key, ApplianceStepKey):
                return commands or self._take_back(step.key, now)
            charger_id = step.key.charger_id
            if charger_id not in draws_before:
                draws_before[charger_id] = self._draw_now_w(charger_id)
            commands += self._take_back(step.key, now)
            freed_w = sum(draw_w - self._draw_after_w(drawing_id, draw_w) for drawing_id, draw_w in draws_before.items())
            if freed_w >= needed_w:
                break
        return commands

    def _draw_now_w(self, charger_id: str) -> float:
        """Return what the charger draws by its charging power, or its estimate with the ampere steps it has on without a valid value."""
        power_w = self._charging_of(charger_id).last_readings[charger_id].charging_power_w
        return power_w if power_w is not None else self._estimated_draw_w(charger_id, float("inf"), self._charging_of(charger_id).ampere_steps_on[charger_id])

    def _draw_above_minimum_w(self, charger_id: str) -> float:
        draw_w = self._draw_now_w(charger_id)
        return draw_w - self._estimated_draw_w(charger_id, draw_w, 1)

    def _draw_after_w(self, charger_id: str, draw_w: float) -> float:
        return self._estimated_draw_w(charger_id, draw_w, self._charging_of(charger_id).ampere_steps_on[charger_id])

    def _estimated_draw_w(self, charger_id: str, power_w: float, ampere_steps_on: int) -> float:
        charger = self._chargers[charger_id]
        return estimated_draw_w(charger, power_w, ampere_steps_on, self._charging_of(charger_id).power_per_ampere_w(charger))

    def _turn_on_next(self, now: datetime, average_w: float, forced_off: bool) -> list[Command]:
        """Make a switch-over, or turn on the next step, or make room for it when there is none.

        No room is made, and no switch-over, when the decision has already
        forced something off, since the average was measured before that. The
        power reserves held above the step, and in its own group, count as
        used, also for its waiting time.
        """
        steps = self._steps()
        place = _next_place(steps)
        switch_over = None if forced_off else self._switch_over(steps, place, now, average_w)
        if switch_over is not None:
            return switch_over
        if place is None:
            self._state.waiting = None
            return []
        candidate = steps[place]
        damping = self._damping(candidate.key)
        if damping is not None:
            self._state.waiting = damping
            return []
        held_w = _held_reserves_w(steps, place)
        if not self._may_turn_on(candidate, average_w + held_w):
            self._state.waiting = None
            return [] if forced_off else self._make_room(steps, place, average_w + held_w, now)
        if not self._has_waited(steps, place, now, average_w + held_w):
            return []
        return self._turn_on(candidate.key, now)

    def _make_room(self, steps: list[Step], place: int, average_w: float, now: datetime) -> list[Command]:
        """Switch off steps below the step at the place, as many as it is estimated to need to fit."""
        return self._free_power(_steps_on_below(steps, place), self._power_needed_w(steps[place], average_w), now)

    def _power_to_free(self, average_w: float) -> PowerToFree | None:
        steps = self._steps()
        place = _next_place(steps)
        if place is None:
            return None
        needed_w = self._power_needed_w(steps[place], average_w + _held_reserves_w(steps, place))
        return PowerToFree(steps[place].key, needed_w) if needed_w > 0 else None

    def _power_needed_w(self, step: Step, average_w: float) -> float:
        """Return how far the average must drop for the step to fit: below the limit by the turn-on margin, and with room for its power reserve."""
        general = self._config.general
        limit_w = general.power_limit_w
        return max(average_w - (limit_w - general.turn_on_margin_w), average_w + (step.power_reserve_w or 0) - limit_w)

    def _switch_over(self, steps: list[Step], place: int | None, now: datetime, average_w: float) -> list[Command] | None:
        """Return the commands of a switch-over when one is due, or None.

        The queued charger may start when the free power, plus what the chargers
        that charge above their minimum current draw above their estimated draw
        at it, covers its power at minimum current, also when none of them is
        above its minimum.
        Nothing above the group may be waiting for room, and no charger of the
        group may be starting, since its charging power would then be from
        before the last switch-over. A damped queued charger waits for its
        damping time to pass.
        """
        for group in self._groups:
            charging = self._charging(group.id)
            queued = charging.queued(group)
            if not charging.shares_by_charging_power(group) or charging.starting or not queued:
                continue
            group_places = [index for index, step in enumerate(steps) if step.group_id == group.id]
            if place is not None and place < group_places[0]:
                continue
            key = AmpereStepKey(queued[0], 0)
            if self._damping(key) is not None:
                continue
            above_minimum = [charger_id for charger_id in charging.charging if charging.ampere_steps_on[charger_id] > 1]
            freed_w = sum(self._draw_above_minimum_w(charger_id) for charger_id in above_minimum)
            step = next(step for step in steps if step.key == key)
            held_w = _held_reserves_w(steps, group_places[0])
            if not self._may_turn_on(step, average_w + held_w - freed_w):
                continue
            self._state.waiting = None
            commands: list[Command] = []
            for charger_id in sorted(above_minimum, key=charging.order(group).index):
                commands += self._set_ampere_steps_on(charger_id, 1)
            return commands + self._turn_on(key, now)
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

    def _has_waited(self, steps: list[Step], place: int, now: datetime, average_w: float) -> bool:
        """Return whether the step at the place has waited its waiting time.

        A step with a power reserve does not wait, since the reserve tells
        whether it fits. Nor does one with steps on below it that may be
        switched off for room: none of them can be turned on while it waits,
        so waiting changes nothing, and they give way if it takes the average
        above the limit.
        """
        step = steps[place]
        if step.power_reserve_w is not None or _steps_on_below(steps, place):
            self._state.waiting = None
            return True
        waiting = self._state.waiting
        started_at = waiting.started_at if waiting is not None and waiting.key == step.key else now
        general = self._config.general
        required = waiting_time(
            average_w,
            general.power_limit_w,
            timedelta(seconds=general.wait_at_limit_s),
            self._waiting_curve,
            self._state.repeats.upcoming_repeat(step.key),
            self._appliance_growth,
        )
        self._state.waiting = Waiting(step.key, started_at, started_at + required)
        return now - started_at >= required

    def _forget_waiting(self, key: StepKey) -> None:
        if self._state.waiting is not None and self._state.waiting.key == key:
            self._state.waiting = None

    def _turn_on(self, key: StepKey, now: datetime) -> list[Command]:
        """Turn the step on, settling until the average shows it."""
        commands = self._switch(key, turn_on=True, now=now)
        self._state.settling_since[key] = now
        return commands

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
        count = key.index + 1 if turn_on else key.index
        return self._set_ampere_steps_on(key.charger_id, count, now)

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
        if not turn_on:
            self._state.settling_since.pop(key, None)
        elif isinstance(key, AmpereStepKey):
            self._state.damped_since.pop(key, None)


def _next_place(steps: list[Step]) -> int | None:
    """Return the place of the first step that is off and may be turned on, if any."""
    return next((place for place, step in enumerate(steps) if not step.is_on and step.can_turn_on), None)


def _steps_on_below(steps: list[Step], place: int) -> list[Step]:
    """Return the steps below the place that are on and may be switched off for room, lowest first."""
    return [step for step in reversed(steps[place + 1 :]) if step.is_on and step.can_turn_off]


def _held_reserves_w(steps: list[Step], place: int) -> float:
    """Return the power reserves held above the place, and in the group of the step at the place."""
    group_id = steps[place].group_id
    return sum(
        step.power_reserve_w or 0
        for index, step in enumerate(steps)
        if step.holds_reserve and index != place and (index < place or (group_id is not None and step.group_id == group_id))
    )
