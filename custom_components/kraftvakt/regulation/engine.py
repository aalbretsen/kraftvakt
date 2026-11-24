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
    ampere_step_count,
    charges_in_window,
    charging_current,
    charging_permission,
    estimated_draw_w,
    may_step_up,
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
    RepeatsDue,
    SetChargingCurrent,
    Step,
    StepKey,
    TurnOffAppliance,
    TurnOnAppliance,
    Waiting,
    WaitingReason,
    without_superseded,
)
from .penalty import PenaltyLimits, PenaltyOutcome, PenaltyState
from .priority import ampere_steps, build_steps, current_variant
from .waiting import RepeatedActivationCounter, RepeatedTurnOnGrowth, WaitingCurve, curve_waiting_time, waiting_time


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
        self._charger_wait_at_limit_s = general.wait_at_limit_s * general.charger_waiting_factor
        self._charger_growth = RepeatedTurnOnGrowth.from_waiting_at_limit(
            self._charger_wait_at_limit_s,
            general.appliance_repeat_increment_factor,
            general.appliance_repeat_increments,
        )
        self._running = False
        self._state = self._new_state()

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
    def one_at_a_time(self) -> Mapping[str, bool]:
        """Return whether each group was restricted to one charger at a time at the last decision."""
        return {group.id: self._charging(group.id).one_at_a_time for group in self._groups}

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
            "charger_wait_at_limit_s": self._charger_wait_at_limit_s,
            "charger_growth": self._charger_growth,
            "state": self._state,
        }

    def start(self, now: datetime, excluded_appliances: frozenset[str] = frozenset()) -> list[Command]:
        """Start with everything off, except the essential appliances that are not excluded."""
        self._running = True
        self._state = self._new_state(started_at=now, excluded_appliances=excluded_appliances)
        return self._record_commands(self._hold_everything_off(essential_on=True), now)

    def stop(self, excluded_appliances: frozenset[str] = frozenset()) -> list[Command]:
        """Stop with everything off, except the essential appliances that are not excluded, so a stop during a penalty does not leave them off."""
        self._running = False
        self._state.excluded_appliances = excluded_appliances
        commands = self._hold_everything_off(essential_on=True)
        self._state = self._new_state()
        return commands

    def decide(self, decision: DecisionInput) -> DecisionResult:
        charged_in_window = self._charged_in_window(decision)
        result = self._decide(decision)
        self._forget_activations_of_disconnected_cars(decision)
        commands = without_superseded(result.commands)
        return replace(result, commands=self._record_commands(commands, decision.now), charged_in_window=charged_in_window)

    def _forget_activations_of_disconnected_cars(self, decision: DecisionInput) -> None:
        """A charger whose car is disconnected was not switched on and off, so a car connected again is activated as the first time."""
        for charger_id, reading in decision.chargers.items():
            if reading.car_disconnected:
                self._state.activations.forget(charger_id)

    def repeat_commands(
        self,
        now: datetime,
        excluded_appliances: frozenset[str],
        excluded_chargers: frozenset[str],
        chargers_without_car: frozenset[str],
    ) -> list[Command]:
        """Return the command for the current state again where it is due.

        An activated charger gets its current, a deactivated one is deactivated
        again. Waiting times and repeated turn-on counters are not touched.
        """
        due = self.repeats_due_at(excluded_appliances, excluded_chargers, chargers_without_car)
        state = self._state
        commands: list[Command] = []
        for appliance_id, due_at in due.appliances.items():
            if due_at > now:
                continue
            variant_id = state.current_variants.get(appliance_id)
            if appliance_id in state.appliances_on:
                commands.append(TurnOnAppliance(appliance_id, variant_id))
            else:
                commands.append(TurnOffAppliance(appliance_id, variant_id))
        for charger_id, due_at in due.chargers.items():
            if due_at <= now:
                commands += self._charger_commands(self._chargers[charger_id], self._charging_of(charger_id).ampere_steps_on[charger_id])
        return self._record_commands(commands, now)

    def repeats_due_at(
        self,
        excluded_appliances: frozenset[str],
        excluded_chargers: frozenset[str],
        chargers_without_car: frozenset[str],
    ) -> RepeatsDue:
        """Return when the command for each appliance and charger is repeated, in the order of the configuration.

        It is due when it has had no command for the repeat interval. Excluded
        appliances and chargers get none, nor a cloud-controlled charger while
        no car is connected to it, and nothing does while the regulation is stopped.
        """
        if not self._running:
            return RepeatsDue({}, {})
        interval = timedelta(minutes=self._config.general.command_repeat_interval_min)
        state = self._state
        appliances = {appliance.id: state.appliances_commanded_at[appliance.id] + interval for appliance in self._config.appliances if appliance.id not in excluded_appliances}
        chargers = {
            charger.id: state.chargers_commanded_at[charger.id] + interval
            for charger in self._chargers.values()
            if charger.id not in excluded_chargers and not (charger.cloud_controlled and charger.id in chargers_without_car)
        }
        return RepeatsDue(appliances, chargers)

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
        self._state.power_to_free = None if self._state.waiting is not None else self._power_to_free(average)
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
        return None if since is None else Waiting(key, since, since + self._ampere_damping_time, WaitingReason.DAMPING)

    def _start_delay(self, steps: list[Step], place: int, key: StepKey) -> Waiting | None:
        """Return the start delay of a starting charger whose first ampere step is above the place, unless `key` is one of its own ampere steps."""
        for step in steps[:place]:
            above = step.key
            if not isinstance(above, AmpereStepKey) or above.index > 0 or (isinstance(key, AmpereStepKey) and key.charger_id == above.charger_id):
                continue
            charging = self._charging_of(above.charger_id)
            until = charging.starting.get(above.charger_id)
            if until is not None:
                return Waiting(above, charging.activated_at[above.charger_id], until, WaitingReason.START_DELAY)
        return None

    def _new_state(self, started_at: datetime | None = None, excluded_appliances: frozenset[str] = frozenset()) -> RegulationState:
        return RegulationState(
            started_at=started_at,
            excluded_appliances=excluded_appliances,
            charging_groups={group.id: ChargingState.for_chargers(group.chargers) for group in self._groups},
            activations=RepeatedActivationCounter(forgotten_after=self._charger_growth.cap),
        )

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
            one_at_a_time = group.one_at_a_time if isinstance(group.one_at_a_time, bool) else decision.one_at_a_time_conditions.get(group.id, False)
            newly_bypassed = charging.evaluate(group, readings, permissions, decision.now, one_at_a_time)
            for charger_id in charging.activated():
                if charging.must_deactivate(group, charger_id):
                    commands += self._set_ampere_steps_on(charger_id, 0, decision.now)
                elif (charger_id in newly_bypassed or charger_id in charging.held_at_min) and charging.ampere_steps_on[charger_id] > 1:
                    commands += self._set_ampere_steps_on(charger_id, 1, decision.now)
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

        An excluded appliance that is on is switched off. An appliance that is
        on and switches variant stays on, with the turn-on action of the new
        variant, when the fixed order holds at its new place. Any other
        appliance at a new place is off afterwards and gets room there, from an
        appliance below it that is switched off anyway at this decision, or else
        by switching off the lowest step that is on below it. A variant switch
        sends the turn-off action of the new variant also when the appliance was
        off, since variants may turn it off in different ways. Before the first
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
        switched_off = [ApplianceStepKey(appliance_id) for appliance_id in sorted((excluded & self._state.appliances_on) - self._essential)]
        for key in switched_off:
            commands += self._switch(key, turn_on=False, now=decision.now)
        places = {step.key: place for place, step in enumerate(self._steps())}
        in_new_places = sorted(map(ApplianceStepKey, moving), key=lambda key: places[key])
        for key in in_new_places:
            if key.appliance_id in was_on and key.appliance_id not in excluded and self._step_above_is_on(key):
                commands.append(TurnOnAppliance(key.appliance_id, self._state.current_variants[key.appliance_id]))
                continue
            switched_variant = previous_variants.get(key.appliance_id) != self._state.current_variants[key.appliance_id]
            if key.appliance_id in was_on and key not in switched_off:
                switched_off.append(key)
            if key.appliance_id in was_on or switched_variant:
                commands += self._switch(key, turn_on=False, now=decision.now)
        for key in in_new_places:
            if key.appliance_id not in was_on and key.appliance_id not in excluded:
                room = next((below for below in switched_off if places[below] > places[key]), None)
                if room is None:
                    commands += self._make_room_below(key, decision.now)
                else:
                    switched_off.remove(room)
            self._forget_waiting(key)
            self._state.repeats.reset(key)
        return commands

    def _step_above_is_on(self, key: StepKey) -> bool:
        """Whether the nearest step above that is not skipped is on, or there is none."""
        steps = self._steps()
        place = next(place for place, step in enumerate(steps) if step.key == key)
        return next((step.is_on for step in reversed(steps[:place]) if step.can_turn_on), True)

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
        """Switch off a step for power. An ampere step above the first is damped from now; the first waits its waiting time when it is turned on again."""
        if isinstance(key, AmpereStepKey) and key.index > 0:
            self._state.damped_since[key] = now
        return self._switch(key, turn_on=False, now=now)

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
            self._state.waiting = self._own_start_delay(steps)
            return []
        candidate = steps[place]
        holding_back = self._start_delay(steps, place, candidate.key) or self._damping(candidate.key)
        if holding_back is not None:
            self._state.waiting = holding_back
            return []
        held_w = _held_reserves_w(steps, place)
        if not self._may_turn_on(candidate, average_w + held_w):
            self._state.waiting = None
            return [] if forced_off else self._make_room(steps, place, average_w + held_w, now)
        if not self._has_waited(steps, place, now, average_w + held_w):
            return []
        return self._turn_on(candidate.key, now)

    def _own_start_delay(self, steps: list[Step]) -> Waiting | None:
        """Return the start delay of the first starting charger that holds back its own next ampere step only for it.

        Its car charges, but not yet with 90 % of its power at minimum current,
        which it would need only while it is starting.
        """
        for step in steps:
            key = step.key
            if not isinstance(key, AmpereStepKey) or key.index > 0 or not step.is_on:
                continue
            charger = self._chargers[key.charger_id]
            charging = self._charging_of(charger.id)
            until = charging.starting.get(charger.id)
            held_only_while_starting = charger.id in charging.held_at_min and may_step_up(charger, charging.last_readings[charger.id], starting=False)
            if until is not None and held_only_while_starting and charging.ampere_steps_on[charger.id] < ampere_step_count(charger):
                return Waiting(key, charging.activated_at[charger.id], until, WaitingReason.START_DELAY)
        return None

    def _make_room(self, steps: list[Step], place: int, average_w: float, now: datetime) -> list[Command]:
        """Switch off steps below the step at the place, as many as it is estimated to need to fit."""
        return self._free_power(_steps_on_below(steps, place), self._power_needed_w(steps[place], average_w), now)

    def _power_to_free(self, average_w: float) -> PowerToFree | None:
        """Return how far the average must drop for the next step, which is not shown while a waiting holds it back, so one row tells what holds it."""
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
        before the last switch-over, nor a charger above the group. A queued
        charger that would be activated again waits its waiting time first, as
        the next step, so nothing else is turned on meanwhile.
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
            if self._start_delay(steps, group_places[0], key):
                continue
            above_minimum = [charger_id for charger_id in charging.charging if charging.ampere_steps_on[charger_id] > 1]
            freed_w = sum(self._draw_above_minimum_w(charger_id) for charger_id in above_minimum)
            step = next(step for step in steps if step.key == key)
            average_after_w = average_w + _held_reserves_w(steps, group_places[0]) - freed_w
            if not self._may_turn_on(step, average_after_w):
                continue
            repeat = self._state.activations.upcoming_repeat(queued[0], now)
            if repeat and not self._waited(step, repeat, now, average_after_w):
                return []
            self._state.waiting = None
            commands: list[Command] = []
            for charger_id in sorted(above_minimum, key=charging.order(group).index):
                commands += self._set_ampere_steps_on(charger_id, 1, now)
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

        A step with a power reserve waits only when it is turned on again,
        since the reserve tells whether it fits, and an ampere step above the
        first never waits, since it is damped instead. Nor does a step with
        steps on below it that may be switched off for room wait: none of them
        can be turned on while it waits, so waiting changes nothing, and they
        give way if it takes the average above the limit. A charger activated
        again waits also then, since its waiting protects the relays of the
        charger and the car.
        """
        step = steps[place]
        key = step.key
        if isinstance(key, AmpereStepKey):
            repeat = self._state.activations.upcoming_repeat(key.charger_id, now)
            waits = key.index == 0 and bool(repeat)
        else:
            repeat = self._state.repeats.upcoming_repeat(key)
            waits = (step.power_reserve_w is None or bool(repeat)) and not _steps_on_below(steps, place)
        if not waits:
            self._state.waiting = None
            return True
        return self._waited(step, repeat, now, average_w)

    def _waited(self, step: Step, repeat: int, now: datetime, average_w: float) -> bool:
        """Return whether the step has waited its waiting time, which starts now unless it already waits.

        The first ampere step of a charger waits the waiting time for EV
        chargers, the charger counted as one unit for the growth on repeated
        turn-on. A step with a power reserve counts it in the curve, so it waits
        by how close it would bring the average to the limit.
        """
        is_ampere_step = isinstance(step.key, AmpereStepKey)
        waiting = self._state.waiting
        started_at = waiting.started_at if waiting is not None and waiting.key == step.key else now
        general = self._config.general
        required = waiting_time(
            average_w + (step.power_reserve_w or 0),
            general.power_limit_w,
            timedelta(seconds=self._charger_wait_at_limit_s if is_ampere_step else general.wait_at_limit_s),
            self._waiting_curve,
            repeat,
            self._charger_growth if is_ampere_step else self._appliance_growth,
        )
        self._state.waiting = Waiting(step.key, started_at, started_at + required)
        return now - started_at >= required

    def _forget_waiting(self, key: StepKey) -> None:
        if self._state.waiting is not None and self._state.waiting.key == key:
            self._state.waiting = None

    def _turn_on(self, key: StepKey, now: datetime) -> list[Command]:
        """Turn the step on, settling until the average shows it.

        A charger it activates holds back the next step from this decision, so
        its start delay shows at once.
        """
        commands = self._switch(key, turn_on=True, now=now)
        self._state.settling_since[key] = now
        steps = self._steps()
        place = _next_place(steps)
        self._state.waiting = None if place is None else self._start_delay(steps, place, steps[place].key)
        return commands

    def _switch(self, key: StepKey, turn_on: bool, now: datetime) -> list[Command]:
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

    def _set_ampere_steps_on(self, charger_id: str, count: int, now: datetime) -> list[Command]:
        charging = self._charging_of(charger_id)
        before = charging.ampere_steps_on[charger_id]
        turn_on = count > before
        for index in range(min(before, count), max(before, count)):
            self._record_switch(AmpereStepKey(charger_id, index), turn_on)
        if (before == 0) != (count == 0):
            self._state.activations.record(charger_id, activated=count > 0, now=now)
        charger = self._chargers[charger_id]
        charging.set_ampere_steps_on(charger_id, count, now, timedelta(seconds=charger.start_delay_s))
        return self._charger_commands(charger, count, activate=before == 0 and count > 0)

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
