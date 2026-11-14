"""Runs Kraftvakt inside Home Assistant."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, CoreState, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.start import async_at_started
from homeassistant.util import dt as dt_util

from .actions import ActionRunner
from .config_model import Issue, KraftvaktConfig
from .config_validation import missing_items
from .decision_clock import DecisionClock, first_decision_from
from .decision_input import excluded_appliances, excluded_chargers, read_decision_input
from .measurement import WindowAverages
from .power_measurement import PowerMeasurement, WindowListener
from .regulation.charging import ChargerStatus
from .regulation.engine import RegulationEngine
from .regulation.model import Command, DecisionInput, Waiting
from .regulation.penalty import PenaltyState
from .repairs import (
    async_check_entities,
    async_clear_not_started,
    async_report_not_started,
)
from .settings import Settings

_LOGGER = logging.getLogger(__name__)

type KraftvaktConfigEntry = ConfigEntry[KraftvaktRuntime]
type StatusListener = Callable[[], None]


class ConfigIncompleteError(HomeAssistantError):
    """Raised when the regulation is started before the configuration is complete."""

    def __init__(self, missing: Sequence[Issue]) -> None:
        super().__init__("The configuration is not complete: " + ", ".join(issue.code for issue in missing))
        self.missing = list(missing)


class RegulationRunningError(HomeAssistantError):
    def __init__(self) -> None:
        super().__init__("The regulation must be stopped to change the configuration")


class KraftvaktRuntime:
    """Runs the regulation on the windows of the power measurement.

    The windows keep their own cadence, also while the regulation is stopped.
    The decision clock tells at which window close a decision is made.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        settings: Settings,
        action_lock: asyncio.Lock | None = None,
    ) -> None:
        """Create the runtime for the stored settings.

        Runtimes that share `action_lock` carry out their actions one at a
        time, so a new runtime after a reload waits for the actions of the old.
        """
        self._hass = hass
        self._settings = settings
        config = settings.config
        self._missing = missing_items(config)
        self._config_version = 0
        self._engine = RegulationEngine(config)
        self._action_lock = action_lock or asyncio.Lock()
        self._actions = self._action_runner(config)
        self._recent_decisions: deque[dict[str, Any]] = deque(maxlen=100)
        self._failed_actions: deque[dict[str, Any]] = deque(maxlen=20)
        self._measurement = PowerMeasurement(hass, lambda: self.config.general)
        self._decisions = DecisionClock()
        self._status_listeners: list[StatusListener] = []
        self._cancel_start_when_started: CALLBACK_TYPE | None = None

    @property
    def latest_averages(self) -> WindowAverages | None:
        return self._measurement.latest_averages

    @property
    def config(self) -> KraftvaktConfig:
        return self._settings.config

    @property
    def missing(self) -> list[Issue]:
        return list(self._missing)

    @property
    def running(self) -> bool:
        return self._engine.running

    @property
    def safe_state(self) -> bool:
        return self._engine.safe_state

    @property
    def penalty(self) -> PenaltyState:
        return self._engine.penalty

    @property
    def config_version(self) -> int:
        """Return a number that changes each time the stored configuration changes."""
        return self._config_version

    @property
    def steps_on(self) -> int:
        """Return how many appliances and amperes of the chargers are on."""
        return self._engine.steps_on

    @property
    def appliances_on(self) -> frozenset[str]:
        return self._engine.appliances_on

    @property
    def excluded_appliances(self) -> frozenset[str]:
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
        general = self.config.general
        return self._decisions.next_decision_at(
            started_at,
            general.regulation_interval,
            self._measurement.window_start,
            self._measurement.window_end,
            timedelta(seconds=general.regulation_window_s),
        )

    @property
    def decision_interval(self) -> timedelta:
        general = self.config.general
        return timedelta(seconds=general.regulation_window_s * general.regulation_interval)

    @property
    def waiting_ends_at(self) -> datetime | None:
        """Return the first decision at or after the end of the waiting time, if any."""
        waiting = self._engine.waiting
        next_decision_at = self.next_decision_at
        if waiting is None or next_decision_at is None:
            return None
        return first_decision_from(waiting.until, next_decision_at, self.decision_interval)

    @property
    def curve_waiting_time(self) -> timedelta | None:
        averages = self._measurement.latest_averages
        if averages is None or averages.regulation_average_w is None:
            return None
        return self._engine.curve_waiting_time(averages.regulation_average_w)

    @property
    def settings(self) -> Settings:
        """Return the stored configuration and the user's switches."""
        return self._settings

    @property
    def recent_decisions(self) -> list[dict[str, Any]]:
        """Return the last decisions, oldest first, for the diagnostics."""
        return list(self._recent_decisions)

    @property
    def failed_actions(self) -> list[dict[str, Any]]:
        """Return the last failed actions, oldest first, for the diagnostics."""
        return list(self._failed_actions)

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
        self._measurement.async_add_window_listener(self._async_window_closed)
        self._measurement.async_start()
        if self._hass.state is CoreState.running:
            self._start_regulation_if_complete(self._measurement.started_at)
        else:
            self._cancel_start_when_started = async_at_started(self._hass, self._async_home_assistant_started)

    @callback
    def _async_home_assistant_started(self, _hass: HomeAssistant) -> None:
        self._cancel_start_when_started = None
        self._start_regulation_if_complete(dt_util.utcnow())

    def _start_regulation_if_complete(self, now: datetime) -> None:
        if self._missing:
            async_report_not_started(self._hass)
        else:
            self._start_regulation(now)

    def _forget_start_when_started(self) -> None:
        if self._cancel_start_when_started:
            self._cancel_start_when_started()
            self._cancel_start_when_started = None

    @callback
    def async_shutdown(self) -> None:
        self._forget_start_when_started()
        self._measurement.async_shutdown()

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
        self._forget_start_when_started()
        if not self._engine.running:
            return
        self._decisions.restart()
        self._execute(self._engine.stop())
        self._engine = RegulationEngine(self.config)
        self._notify_status()

    async def async_save_config(self, config: KraftvaktConfig) -> None:
        """Save a new configuration and use it from the next start.

        The averages go on, also with a new power sensor or window length. Raises
        RegulationRunningError while the regulation runs.
        """
        if self._engine.running:
            raise RegulationRunningError
        self._settings.async_use_config(config)
        self._config_version += 1
        self._missing = missing_items(config)
        self._engine = RegulationEngine(config)
        self._actions = self._action_runner(config)
        self._measurement.async_settings_changed()
        self._notify_status()
        await self._settings.async_save()

    async def async_set_power_limit(self, power_limit_w: int) -> None:
        """Save a new power limit, used from the next decision also while running."""
        general = self.config.general
        if power_limit_w == general.power_limit_w:
            return
        await self._async_change_config(replace(self.config, general=replace(general, power_limit_w=power_limit_w)))

    async def async_set_finish_after_window(self, charger_id: str, finish_after_window: bool) -> None:
        """Save whether the charger finishes ongoing charging after its window.

        It can be changed while the regulation runs, and applies from the next
        decision without a restart.
        """
        charger = next(
            (charger for charger in self.config.chargers if charger.id == charger_id),
            None,
        )
        if charger is None or charger.finish_after_window == finish_after_window:
            return
        await self._async_change_config(self.config.with_charger(replace(charger, finish_after_window=finish_after_window)))

    async def _async_change_config(self, config: KraftvaktConfig) -> None:
        """Save a change made by an entity, also while the regulation runs."""
        if not self._engine.running:
            await self.async_save_config(config)
            return
        self._settings.async_use_config(config)
        self._config_version += 1
        self._engine.use_power_limit(config.general.power_limit_w)
        self._notify_status()
        await self._settings.async_save()

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        return self._measurement.async_add_window_listener(listener)

    @callback
    def async_add_status_listener(self, listener: StatusListener) -> CALLBACK_TYPE:
        """Call `listener` each time the status of the regulation may have changed."""
        self._status_listeners.append(listener)
        return lambda: self._status_listeners.remove(listener)

    def _start_regulation(self, now: datetime) -> None:
        async_clear_not_started(self._hass)
        async_check_entities(self._hass, self.config)
        self._decisions.restart()
        self._execute(self._engine.start(now))
        self._notify_status()

    @callback
    def _async_window_closed(self, averages: WindowAverages) -> None:
        if self._engine.running:
            self._decisions.add(averages)
            if self._decisions.is_due(self._engine.started_at, self.config.general.regulation_interval):
                self._decide(averages)
            self._repeat_commands(averages.end)
        self._notify_status()

    def _decide(self, averages: WindowAverages) -> None:
        decision = read_decision_input(
            self._hass,
            self._settings,
            averages,
            self._decisions.take_windows(),
            self._measurement.sensor_lost,
        )
        result = self._engine.decide(decision)
        for charger_id in result.overrides.ended:
            self._settings.async_reset_window_override(charger_id)
        self._settings.async_arm_overrides(result.overrides.armed)
        self._record_decision(decision, result.commands)
        self._execute(result.commands)

    def _record_decision(self, decision: DecisionInput, commands: list[Command]) -> None:
        penalty = self._engine.penalty
        waiting = self._engine.waiting
        record = {
            "time": dt_util.as_local(decision.now).isoformat(timespec="seconds"),
            "regulation_average_w": _rounded(decision.regulation_average_w),
            "tariff_average_w": _rounded(decision.tariff_average_w),
            "power_sensor_valid": decision.power_sensor_valid,
            "safe_state": self._engine.safe_state,
            "penalty_active": penalty.active,
            "overconsumption_wh": round(penalty.overconsumption_wh, 1),
            "waiting": None if waiting is None else f"{waiting.key} until {waiting.until.isoformat(timespec='seconds')}",
            "commands": [str(command) for command in commands],
        }
        self._recent_decisions.append(record)
        _LOGGER.debug("Decision: %s", record)

    def _action_runner(self, config: KraftvaktConfig) -> ActionRunner:
        return ActionRunner(self._hass, config, self._action_lock, self._action_failed)

    def _action_failed(self, action: str, error: str) -> None:
        """Remember the failure for the diagnostics, and look for removed entities."""
        self._failed_actions.append(
            {
                "time": dt_util.now().isoformat(timespec="seconds"),
                "action": action,
                "error": error,
            }
        )
        async_check_entities(self._hass, self.config)

    def _repeat_commands(self, now: datetime) -> None:
        commands = self._engine.repeat_commands(now, excluded_appliances(self._settings), excluded_chargers(self._settings))
        if commands:
            _LOGGER.debug(
                "Commands repeated at %s: %s",
                dt_util.as_local(now).isoformat(timespec="seconds"),
                commands,
            )
            self._execute(commands)

    def _execute(self, commands: Sequence[Command]) -> None:
        if commands:
            self._hass.async_create_background_task(self._actions.async_execute(commands), "kraftvakt actions")

    def _notify_status(self) -> None:
        for listener in list(self._status_listeners):
            listener()


def _rounded(power_w: float | None) -> int | None:
    return None if power_w is None else round(power_w)
