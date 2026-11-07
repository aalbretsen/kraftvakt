"""Runs Kraftvakt inside Home Assistant."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import (
    CALLBACK_TYPE,
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
from homeassistant.util import dt as dt_util

from .actions import ActionRunner
from .charger_switches import ChargerSwitchBoard
from .conditions import evaluate_condition
from .config_model import (
    Charger,
    Issue,
    KraftvaktConfig,
    missing_items,
)
from .measurement import (
    CONSECUTIVE_INVALID_CLOSES_BEFORE_RESET,
    PowerAverager,
    WindowAverages,
    power_kw,
)
from .regulation.charging import ChargerReading, ChargerStatus
from .regulation.engine import RegulationEngine
from .regulation.model import Command, DecisionInput, ResetWindowOverride

type KraftvaktConfigEntry = ConfigEntry[KraftvaktRuntime]
type WindowListener = Callable[[WindowAverages], None]
type StatusListener = Callable[[], None]


class ConfigIncompleteError(HomeAssistantError):
    """Raised when the regulation is started before the configuration is complete."""

    def __init__(self, missing: Sequence[Issue]) -> None:
        """Create the error from what is missing (REG-016)."""
        super().__init__(
            "The configuration is not complete: "
            + ", ".join(issue.code for issue in missing)
        )
        self.missing = list(missing)


class RegulationRunningError(HomeAssistantError):
    """Raised when the configuration is changed while the regulation runs."""

    def __init__(self) -> None:
        """Create the error (REG-010)."""
        super().__init__("The regulation must be stopped to change the configuration")


class KraftvaktRuntime:
    """Measures the power sensor and runs the regulation.

    The windows keep their own cadence from the start of the runtime, also
    while the regulation is stopped (MAL-001, T1, T20). Every closed window is
    passed to the window listeners. While the regulation runs, a decision is
    made each time the N-th window that started after the start or the last
    decision has closed, where N is the regulation interval (REG-002, T1).
    Decisions are made only then (REG-005), also for the charging power, the
    car connected and the charger switches. The status listeners are called
    after every window, decision, start and stop.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: KraftvaktConfig,
        charger_switches: ChargerSwitchBoard,
    ) -> None:
        """Create the runtime for the configuration and the charger switches."""
        self._hass = hass
        self._config = config
        self._charger_switches = charger_switches
        self._missing = missing_items(config)
        self._engine = RegulationEngine(config)
        self._action_lock = asyncio.Lock()
        self._actions = ActionRunner(hass, config, self._action_lock)
        self._created_at = dt_util.utcnow()
        self._averager = PowerAverager(
            timedelta(seconds=config.general.regulation_window_s), self._created_at
        )
        self._latest_averages: WindowAverages | None = None
        self._recent_windows: deque[WindowAverages] = deque(
            maxlen=CONSECUTIVE_INVALID_CLOSES_BEFORE_RESET
        )
        self._windows_since_decision: list[WindowAverages] = []
        self._window_listeners: list[WindowListener] = []
        self._status_listeners: list[StatusListener] = []
        self._cancel_power_listener: CALLBACK_TYPE | None = None
        self._cancel_window_timer: CALLBACK_TYPE | None = None

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
        """Return what is missing before the regulation can start (REG-016)."""
        return list(self._missing)

    @property
    def running(self) -> bool:
        """Return whether the regulation runs (REG-016)."""
        return self._engine.running

    @property
    def safe_state(self) -> bool:
        """Return whether the regulation is in the safe state (REG-011)."""
        return self._engine.safe_state

    @property
    def charger_switches(self) -> ChargerSwitchBoard:
        """Return the user's switches for the chargers (ENT-003, ENT-004)."""
        return self._charger_switches

    @property
    def chargers(self) -> Mapping[str, ChargerStatus]:
        """Return how each charger stands after the last decision."""
        return self._engine.chargers

    @callback
    def async_start(self) -> None:
        """Start measuring, and start the regulation if it can (REG-009, REG-016).

        The regulation starts at the same moment as the first window, so the
        first decision comes after one whole regulation interval.
        """
        self._follow_power_sensor(self._created_at)
        self._schedule_window_close()
        if not self._missing:
            self._start_regulation(self._created_at)

    @callback
    def async_shutdown(self) -> None:
        """Stop listening to the power sensor and cancel the window timer."""
        if self._cancel_window_timer:
            self._cancel_window_timer()
            self._cancel_window_timer = None
        if self._cancel_power_listener:
            self._cancel_power_listener()
            self._cancel_power_listener = None

    @callback
    def async_start_regulation(self) -> None:
        """Turn everything off at once and start the regulation (REG-016, REG-009).

        Does nothing if the regulation already runs. Raises
        ConfigIncompleteError if the configuration is not complete.
        """
        if self._engine.running:
            return
        if self._missing:
            raise ConfigIncompleteError(self._missing)
        self._start_regulation(dt_util.utcnow())

    @callback
    def async_stop_regulation(self) -> None:
        """Stop the regulation and turn everything off at once (REG-016)."""
        if not self._engine.running:
            return
        self._windows_since_decision.clear()
        self._execute(self._engine.stop())
        self._notify_status()

    async def async_save_config(self, config: KraftvaktConfig) -> None:
        """Save a new configuration and use it from the next start (REG-010, B9).

        Only while the regulation is stopped, so nothing is on and nothing is
        lost from the state of the regulation. The averages go on (GEN-007): a
        new power sensor is followed from now, and a new regulation window
        applies from the next window. Raises RegulationRunningError while the
        regulation runs.
        """
        if self._engine.running:
            raise RegulationRunningError
        previous = self._config
        self._config = config
        self._missing = missing_items(config)
        self._engine = RegulationEngine(config)
        self._actions = ActionRunner(self._hass, config, self._action_lock)
        self._averager.change_window_length(
            timedelta(seconds=config.general.regulation_window_s)
        )
        if config.general.power_sensor != previous.general.power_sensor:
            self._follow_power_sensor(dt_util.utcnow())
        self._notify_status()
        await self._charger_switches.async_update_config(config)

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
        self._execute(self._engine.start(now))
        self._notify_status()

    def _follow_power_sensor(self, now: datetime) -> None:
        """Measure the configured power sensor from `now` on (GEN-003)."""
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

    @callback
    def _async_power_changed(self, event: Event[EventStateChangedData]) -> None:
        self._record_power(event.time_fired, event.data["new_state"])

    def _record_power(self, when: datetime, state: State | None) -> None:
        power = (
            None
            if state is None
            else power_kw(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
        )
        self._averager.add_measurement(when, power)

    def _schedule_window_close(self) -> None:
        # Absolute times keep the windows from drifting (R4).
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
                self._decide(averages)
        self._notify_status()

    def _decision_is_due(self) -> bool:
        """Return whether enough windows have closed since the start (T1).

        Windows that started before the start of the regulation do not count.
        The engine may start the regulation again itself at a decision, after
        the safe state or a penalty. It then starts at the end of the last
        window, so the windows after it count from the next one.
        """
        started_at = self._engine.started_at
        counted = sum(
            1
            for window in self._windows_since_decision
            if started_at is not None and window.start >= started_at
        )
        return counted >= self._config.general.regulation_interval

    def _decide(self, averages: WindowAverages) -> None:
        """Make a decision based on the windows closed since the previous one."""
        decision = DecisionInput(
            now=averages.end,
            regulation_average_kw=averages.regulation_average_kw,
            capacity_average_kw=averages.capacity_average_kw,
            regulation_averages_kw=[
                window.regulation_average_kw
                for window in self._windows_since_decision
                if window.regulation_average_kw is not None
            ],
            power_sensor_valid=averages.sensor_valid,
            power_sensor_lost=self._power_sensor_lost(),
            variant_conditions=self._variant_conditions(),
            chargers=self._charger_readings(),
            time_zone=dt_util.get_default_time_zone(),
        )
        self._windows_since_decision.clear()
        self._execute(self._engine.decide(decision))

    def _power_sensor_lost(self) -> bool:
        """Return whether the sensor was invalid at the last two closes (T21)."""
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

    def _charger_readings(self) -> dict[str, ChargerReading]:
        """Read the chargers at a decision (LAD-008, LAD-010, ENT-003, ENT-004)."""
        if not self._config.charging.enabled:
            return {}
        return {
            charger.id: self._charger_reading(charger)
            for charger in self._config.charging.chargers
        }

    def _charger_reading(self, charger: Charger) -> ChargerReading:
        switches = self._charger_switches.switches(charger.id)
        power_state = (
            self._hass.states.get(charger.charge_power_sensor)
            if charger.charge_power_sensor
            else None
        )
        return ChargerReading(
            charge_power_kw=(
                None
                if power_state is None
                else power_kw(
                    power_state.state,
                    power_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT),
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
            override_switched_on_at=self._charger_switches.override_switched_on_at(
                charger.id
            ),
        )

    def _execute(self, commands: Sequence[Command]) -> None:
        """Carry out the commands, the actions in the background after earlier ones.

        A window override that has ended is switched off at once (LAD-027).
        """
        actions = []
        for command in commands:
            if isinstance(command, ResetWindowOverride):
                self._charger_switches.async_reset_window_override(command.charger_id)
            else:
                actions.append(command)
        if actions:
            self._hass.async_create_background_task(
                self._actions.async_execute(actions), "kraftvakt actions"
            )

    def _notify_status(self) -> None:
        for listener in list(self._status_listeners):
            listener()
