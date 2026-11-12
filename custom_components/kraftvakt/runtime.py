"""Runs Kraftvakt inside Home Assistant."""

from __future__ import annotations

import asyncio
import logging
import math
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from functools import partial

from homeassistant.components.recorder import get_instance, history
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import (
    CALLBACK_TYPE,
    CoreState,
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from .actions import ActionRunner
from .conditions import evaluate_actively_charging, evaluate_condition
from .config_model import (
    Charger,
    Issue,
    KraftvaktConfig,
)
from .config_validation import (
    missing_items,
)
from .measurement import (
    CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN,
    TARIFF_WINDOW,
    PowerAverager,
    WindowAverages,
    power_w,
)
from .regulation.charging import ChargerReading, ChargerStatus
from .regulation.engine import RegulationEngine
from .regulation.model import Command, DecisionInput, ResetWindowOverride, Waiting
from .regulation.penalty import PenaltyState
from .switch_board import SwitchBoard

_LOGGER = logging.getLogger(__name__)

type KraftvaktConfigEntry = ConfigEntry[KraftvaktRuntime]
type WindowListener = Callable[[WindowAverages], None]
type StatusListener = Callable[[], None]


class ConfigIncompleteError(HomeAssistantError):
    """Raised when the regulation is started before the configuration is complete."""

    def __init__(self, missing: Sequence[Issue]) -> None:
        """Create the error from what is missing."""
        super().__init__(
            "The configuration is not complete: "
            + ", ".join(issue.code for issue in missing)
        )
        self.missing = list(missing)


class RegulationRunningError(HomeAssistantError):
    """Raised when the configuration is changed while the regulation runs."""

    def __init__(self) -> None:
        """Create the error."""
        super().__init__("The regulation must be stopped to change the configuration")


class KraftvaktRuntime:
    """Measures the power sensor and runs the regulation.

    The windows keep their own cadence, also while the regulation is stopped. A
    decision is made when the N-th window that started after the start or the
    last decision has closed, where N is the regulation interval.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: KraftvaktConfig,
        switch_board: SwitchBoard,
        action_lock: asyncio.Lock | None = None,
    ) -> None:
        """Create the runtime for the configuration and the user's switches.

        Runtimes that share `action_lock` carry out their actions one at a
        time, so a new runtime after a reload waits for the actions of the old.
        """
        self._hass = hass
        self._config = config
        self._switch_board = switch_board
        self._missing = missing_items(config)
        self._config_version = 0
        self._engine = RegulationEngine(config)
        self._action_lock = action_lock or asyncio.Lock()
        self._actions = ActionRunner(hass, config, self._action_lock)
        self._created_at = dt_util.utcnow()
        self._averager = PowerAverager(
            timedelta(seconds=config.general.regulation_window_s), self._created_at
        )
        self._latest_averages: WindowAverages | None = None
        self._recent_windows: deque[WindowAverages] = deque(
            maxlen=CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN
        )
        self._windows_since_decision: list[WindowAverages] = []
        self._window_listeners: list[WindowListener] = []
        self._status_listeners: list[StatusListener] = []
        self._cancel_power_listener: CALLBACK_TYPE | None = None
        self._cancel_window_timer: CALLBACK_TYPE | None = None
        self._cancel_start_when_started: CALLBACK_TYPE | None = None
        self._history_task: asyncio.Task[None] | None = None

    @property
    def latest_averages(self) -> WindowAverages | None:
        """Return the averages of the last closed window, if any."""
        return self._latest_averages

    @property
    def config(self) -> KraftvaktConfig:
        """Return the configuration the regulation uses."""
        return self._config

    @property
    def missing(self) -> list[Issue]:
        """Return what is missing before the regulation can start."""
        return list(self._missing)

    @property
    def running(self) -> bool:
        """Return whether the regulation runs."""
        return self._engine.running

    @property
    def safe_state(self) -> bool:
        """Return whether the regulation is in the safe state."""
        return self._engine.safe_state

    @property
    def penalty(self) -> PenaltyState:
        """Return the overconsumption state and the penalty period."""
        return self._engine.penalty

    @property
    def config_version(self) -> int:
        """Return a number that changes each time the stored configuration changes."""
        return self._config_version

    @property
    def power_limit_w(self) -> int:
        """Return the power limit the regulation uses now.

        After the power limit is changed while the regulation runs, this is
        the previous limit until the next decision.
        """
        return self._engine.power_limit_w

    @property
    def steps_on(self) -> int:
        """Return how many appliances and amperes of the chargers are on."""
        return self._engine.steps_on

    @property
    def appliances_on(self) -> frozenset[str]:
        """Return the ids of the appliances the regulation has turned on."""
        return self._engine.appliances_on

    @property
    def excluded_appliances(self) -> frozenset[str]:
        """Return the ids of the appliances excluded at the last decision."""
        return self._engine.excluded_appliances

    @property
    def current_variants(self) -> Mapping[str, str | None]:
        """Return the current variant id of each appliance, None for none."""
        return self._engine.current_variants

    @property
    def waiting(self) -> Waiting | None:
        """Return the waiting time that runs for the next step, if any."""
        return self._engine.waiting

    @property
    def next_decision_at(self) -> datetime | None:
        """Return when the next decision is made, or None while stopped."""
        started_at = self._engine.started_at
        if started_at is None:
            return None
        current_window_counts = self._averager.window_start >= started_at
        windows_left = (
            self._config.general.regulation_interval
            - self._windows_counted_since_decision()
            - current_window_counts
        )
        return self._averager.window_end + windows_left * timedelta(
            seconds=self._config.general.regulation_window_s
        )

    @property
    def decision_interval(self) -> timedelta:
        """Return the time between two decisions."""
        general = self._config.general
        return timedelta(
            seconds=general.regulation_window_s * general.regulation_interval
        )

    @property
    def waiting_ends_at(self) -> datetime | None:
        """Return the first decision at or after the end of the waiting time, if any."""
        waiting = self._engine.waiting
        next_decision_at = self.next_decision_at
        if waiting is None or next_decision_at is None:
            return None
        return first_decision_from(
            waiting.until, next_decision_at, self.decision_interval
        )

    @property
    def curve_waiting_time(self) -> timedelta | None:
        """Return the waiting time from the curve for the last regulation average."""
        averages = self._latest_averages
        if averages is None or averages.regulation_average_w is None:
            return None
        return self._engine.curve_waiting_time(averages.regulation_average_w)

    @property
    def switch_board(self) -> SwitchBoard:
        """Return the user's switches for the appliances and the chargers."""
        return self._switch_board

    @property
    def chargers(self) -> Mapping[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return self._engine.chargers

    @property
    def charging_priorities(self) -> Mapping[str, list[str]]:
        """Return the current charging priority of each group, highest first."""
        return self._engine.charging_priorities

    @callback
    def async_start(self) -> None:
        """Start measuring, and start the regulation if it can.

        While Home Assistant starts, the regulation waits until it has started, so
        that the integrations of the appliances are loaded before they are turned
        off.
        """
        self._follow_power_sensor(self._created_at)
        self._history_task = self._hass.async_create_background_task(
            self._async_add_power_history(), "kraftvakt power history"
        )
        self._schedule_window_close()
        if self._hass.state is CoreState.running:
            self._start_regulation_if_complete(self._created_at)
        else:
            self._cancel_start_when_started = async_at_started(
                self._hass, self._async_home_assistant_started
            )

    @callback
    def _async_home_assistant_started(self, _hass: HomeAssistant) -> None:
        self._cancel_start_when_started = None
        self._start_regulation_if_complete(dt_util.utcnow())

    def _start_regulation_if_complete(self, now: datetime) -> None:
        if not self._missing:
            self._start_regulation(now)

    def _forget_start_when_started(self) -> None:
        if self._cancel_start_when_started:
            self._cancel_start_when_started()
            self._cancel_start_when_started = None

    @callback
    def async_shutdown(self) -> None:
        """Stop listening to the power sensor and cancel the window timer."""
        self._forget_start_when_started()
        if self._history_task:
            self._history_task.cancel()
            self._history_task = None
        if self._cancel_window_timer:
            self._cancel_window_timer()
            self._cancel_window_timer = None
        if self._cancel_power_listener:
            self._cancel_power_listener()
            self._cancel_power_listener = None

    @callback
    def async_start_regulation(self) -> None:
        """Start the regulation with everything off, if it does not run.

        Raises ConfigIncompleteError if the configuration is not complete.
        """
        if self._engine.running:
            return
        if self._missing:
            raise ConfigIncompleteError(self._missing)
        self._forget_start_when_started()
        self._start_regulation(dt_util.utcnow())

    @callback
    def async_stop_regulation(self) -> None:
        """Stop the regulation and turn everything off at once.

        The new engine picks up a power limit changed while the regulation ran.
        """
        self._forget_start_when_started()
        if not self._engine.running:
            return
        self._windows_since_decision.clear()
        self._execute(self._engine.stop())
        self._engine = RegulationEngine(self._config)
        self._notify_status()

    async def async_save_config(self, config: KraftvaktConfig) -> None:
        """Save a new configuration and use it from the next start.

        The averages go on, also with a new power sensor or window length. Raises
        RegulationRunningError while the regulation runs.
        """
        if self._engine.running:
            raise RegulationRunningError
        previous = self._config
        self._config = config
        self._config_version += 1
        self._missing = missing_items(config)
        self._engine = RegulationEngine(config)
        self._actions = ActionRunner(self._hass, config, self._action_lock)
        self._averager.change_window_length(
            timedelta(seconds=config.general.regulation_window_s)
        )
        if config.general.power_sensor != previous.general.power_sensor:
            self._follow_power_sensor(dt_util.utcnow())
        self._notify_status()
        await self._switch_board.async_update_config(config)

    async def async_set_power_limit(self, power_limit_w: int) -> None:
        """Save a new power limit, also while the regulation runs.

        While it runs, the regulation starts again with the new limit at the
        next decision, so several changes give one restart and a limit changed
        back to the one in use gives none.
        """
        general = self._config.general
        if power_limit_w == general.power_limit_w:
            return
        await self._async_change_config(
            replace(self._config, general=replace(general, power_limit_w=power_limit_w))
        )

    async def async_set_finish_after_window(
        self, charger_id: str, finish_after_window: bool
    ) -> None:
        """Save whether the charger finishes ongoing charging after its window.

        It can be changed while the regulation runs, and applies from the next
        decision without a restart.
        """
        charger = next(
            charger for charger in self._config.chargers if charger.id == charger_id
        )
        if charger.finish_after_window == finish_after_window:
            return
        await self._async_change_config(
            self._config.with_charger(
                replace(charger, finish_after_window=finish_after_window)
            )
        )

    async def _async_change_config(self, config: KraftvaktConfig) -> None:
        """Save a change made by an entity, also while the regulation runs."""
        if not self._engine.running:
            await self.async_save_config(config)
            return
        self._config = config
        self._config_version += 1
        self._notify_status()
        await self._switch_board.async_update_config(config)

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        self._window_listeners.append(listener)
        return lambda: self._window_listeners.remove(listener)

    @callback
    def async_add_status_listener(self, listener: StatusListener) -> CALLBACK_TYPE:
        """Call `listener` each time the status of the regulation may have changed."""
        self._status_listeners.append(listener)
        return lambda: self._status_listeners.remove(listener)

    def _start_regulation(self, now: datetime) -> None:
        self._windows_since_decision.clear()
        self._switch_board.async_regulation_started(now)
        self._execute(self._engine.start(now))
        self._notify_status()

    def _follow_power_sensor(self, now: datetime) -> None:
        if self._cancel_power_listener:
            self._cancel_power_listener()
            self._cancel_power_listener = None
        power_sensor = self._config.general.power_sensor
        self._record_power(
            now, self._hass.states.get(power_sensor) if power_sensor else None
        )
        if power_sensor:
            self._cancel_power_listener = async_track_state_change_event(
                self._hass, power_sensor, self._async_power_changed
            )

    async def _async_add_power_history(self) -> None:
        power_sensor = self._config.general.power_sensor
        if not power_sensor or "recorder" not in self._hass.config.components:
            return
        states = await get_instance(self._hass).async_add_executor_job(
            partial(
                history.state_changes_during_period,
                self._hass,
                self._created_at - TARIFF_WINDOW,
                self._created_at,
                power_sensor,
            )
        )
        if power_sensor == self._config.general.power_sensor:
            self._averager.add_history(
                (state.last_changed, _power_of(state))
                for state in states.get(power_sensor, [])
            )

    @callback
    def _async_power_changed(self, event: Event[EventStateChangedData]) -> None:
        self._record_power(event.time_fired, event.data["new_state"])

    def _record_power(self, when: datetime, state: State | None) -> None:
        self._averager.add_measurement(
            when, None if state is None else _power_of(state)
        )

    def _schedule_window_close(self) -> None:
        # Absolute times keep the windows from drifting.
        self._cancel_window_timer = async_track_point_in_utc_time(
            self._hass, self._async_window_ended, self._averager.window_end
        )

    @callback
    def _async_window_ended(self, _now: datetime) -> None:
        averages = self._averager.close_window()
        self._latest_averages = averages
        self._recent_windows.append(averages)
        self._schedule_window_close()
        for listener in list(self._window_listeners):
            listener(averages)
        if self._engine.running:
            self._windows_since_decision.append(averages)
            if self._decision_is_due():
                self._decide_or_restart(averages)
            self._repeat_commands(averages.end)
        self._notify_status()

    def _decision_is_due(self) -> bool:
        """Return whether enough windows have closed since the start.

        Windows that started before the start do not count, also when the engine
        starts again itself at a decision after the safe state or a penalty.
        """
        return (
            self._windows_counted_since_decision()
            >= self._config.general.regulation_interval
        )

    def _windows_counted_since_decision(self) -> int:
        started_at = self._engine.started_at
        return sum(
            1
            for window in self._windows_since_decision
            if started_at is not None and window.start >= started_at
        )

    def _decide_or_restart(self, averages: WindowAverages) -> None:
        if self._engine.power_limit_w == self._config.general.power_limit_w:
            self._decide(averages)
        else:
            self._restart_with_new_power_limit(averages.end)

    def _restart_with_new_power_limit(self, now: datetime) -> None:
        _LOGGER.info(
            "The power limit changed from %s W to %s W, the regulation starts again",
            self._engine.power_limit_w,
            self._config.general.power_limit_w,
        )
        self._engine = RegulationEngine(self._config)
        self._start_regulation(now)

    def _decide(self, averages: WindowAverages) -> None:
        decision = DecisionInput(
            now=averages.end,
            regulation_average_w=averages.regulation_average_w,
            tariff_average_w=averages.tariff_average_w,
            regulation_averages_w=[
                window.regulation_average_w
                for window in self._windows_since_decision
                if window.regulation_average_w is not None
            ],
            power_sensor_valid=averages.sensor_valid,
            power_sensor_lost=self._power_sensor_lost(),
            variant_conditions=self._variant_conditions(),
            chargers=self._charger_readings(),
            excluded_appliances=self._excluded_appliances(),
            time_zone=dt_util.get_default_time_zone(),
        )
        self._windows_since_decision.clear()
        commands = self._engine.decide(decision)
        self._log_decision(decision, commands)
        self._execute(commands)

    def _log_decision(self, decision: DecisionInput, commands: list[Command]) -> None:
        if not _LOGGER.isEnabledFor(logging.DEBUG):
            return
        penalty = self._engine.penalty
        waiting = self._engine.waiting
        _LOGGER.debug(
            "Decision at %s: regulation average %s W, average consumption %s W, "
            "sensor valid %s, safe state %s, penalty %s (%.1f Wh), waiting %s, "
            "commands %s",
            dt_util.as_local(decision.now).isoformat(timespec="seconds"),
            _rounded(decision.regulation_average_w),
            _rounded(decision.tariff_average_w),
            decision.power_sensor_valid,
            self._engine.safe_state,
            penalty.active,
            penalty.overconsumption_wh,
            None
            if waiting is None
            else f"{waiting.key} until {waiting.until.isoformat(timespec='seconds')}",
            commands or "none",
        )

    def _repeat_commands(self, now: datetime) -> None:
        commands = self._engine.repeat_commands(
            now, self._excluded_appliances(), self._excluded_chargers()
        )
        if commands:
            _LOGGER.debug(
                "Commands repeated at %s: %s",
                dt_util.as_local(now).isoformat(timespec="seconds"),
                commands,
            )
            self._execute(commands)

    def _power_sensor_lost(self) -> bool:
        return len(self._recent_windows) == self._recent_windows.maxlen and not any(
            window.sensor_valid for window in self._recent_windows
        )

    def _variant_conditions(self) -> dict[str, bool]:
        return {
            variant.id: evaluate_condition(
                self._hass, variant.condition, appliance.entity_id
            )
            for appliance in self._config.appliances
            for variant in appliance.variants
        }

    def _excluded_appliances(self) -> frozenset[str]:
        return frozenset(
            appliance.id
            for appliance in self._config.appliances
            if self._switch_board.appliance_switches(appliance.id).excluded
        )

    def _excluded_chargers(self) -> frozenset[str]:
        return frozenset(
            charger.id
            for charger in self._config.chargers
            if self._switch_board.charger_switches(charger.id).excluded
        )

    def _charger_readings(self) -> dict[str, ChargerReading]:
        return {
            charger.id: self._charger_reading(charger)
            for group in self._config.charger_groups
            for charger in group.chargers
        }

    def _charger_reading(self, charger: Charger) -> ChargerReading:
        switches = self._switch_board.charger_switches(charger.id)
        return ChargerReading(
            actively_charging=(
                charger.actively_charging is None
                or evaluate_actively_charging(
                    self._hass, charger.actively_charging, charger.entity_id
                )
            ),
            car_connected=(
                None
                if charger.car_connected is None
                else evaluate_condition(
                    self._hass, charger.car_connected, charger.entity_id
                )
            ),
            excluded=switches.excluded,
            window_override=switches.window_override,
            override_switched_on_at=self._switch_board.override_switched_on_at(
                charger.id
            ),
            finish_after_window=charger.finish_after_window,
        )

    def _execute(self, commands: Sequence[Command]) -> None:
        actions = []
        for command in commands:
            if isinstance(command, ResetWindowOverride):
                self._switch_board.async_reset_window_override(command.charger_id)
            else:
                actions.append(command)
        if actions:
            self._hass.async_create_background_task(
                self._actions.async_execute(actions), "kraftvakt actions"
            )

    def _notify_status(self) -> None:
        for listener in list(self._status_listeners):
            listener()


def first_decision_from(
    moment: datetime, next_decision_at: datetime, interval: timedelta
) -> datetime:
    """Return the first decision at or after `moment`."""
    if moment <= next_decision_at:
        return next_decision_at
    return next_decision_at + interval * math.ceil(
        (moment - next_decision_at) / interval
    )


def _rounded(power_w: float | None) -> int | None:
    return None if power_w is None else round(power_w)


def _power_of(state: State) -> float | None:
    return power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
