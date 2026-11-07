"""Runs Kraftvakt inside Home Assistant."""

from __future__ import annotations

from collections.abc import Callable
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
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .config_model import KraftvaktConfig
from .measurement import PowerAverager, WindowAverages, power_kw

type KraftvaktConfigEntry = ConfigEntry[KraftvaktRuntime]
type WindowListener = Callable[[WindowAverages], None]


class KraftvaktRuntime:
    """Measures the power sensor and closes the regulation windows.

    The windows keep their own cadence from the start of the runtime, also
    while the regulation is stopped (MAL-001, T1, T20). Every closed window is
    passed to the window listeners.
    """

    def __init__(self, hass: HomeAssistant, config: KraftvaktConfig) -> None:
        """Create the runtime for the given configuration."""
        self._hass = hass
        self._config = config
        self._averager = PowerAverager(
            timedelta(seconds=config.general.regulation_window_s), dt_util.utcnow()
        )
        self._latest_averages: WindowAverages | None = None
        self._window_listeners: list[WindowListener] = []
        self._unsubscribers: list[CALLBACK_TYPE] = []
        self._cancel_window_timer: CALLBACK_TYPE | None = None

    @property
    def latest_averages(self) -> WindowAverages | None:
        """Return the averages of the last closed window, if any."""
        return self._latest_averages

    @callback
    def async_start(self) -> None:
        """Start measuring the power sensor and closing windows."""
        power_sensor = self._config.general.power_sensor
        if power_sensor:
            self._record_power(dt_util.utcnow(), self._hass.states.get(power_sensor))
            self._unsubscribers.append(
                async_track_state_change_event(
                    self._hass, power_sensor, self._async_power_changed
                )
            )
        self._schedule_window_close()

    @callback
    def async_shutdown(self) -> None:
        """Stop listening to the power sensor and cancel the window timer."""
        if self._cancel_window_timer:
            self._cancel_window_timer()
            self._cancel_window_timer = None
        while self._unsubscribers:
            self._unsubscribers.pop()()

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        self._window_listeners.append(listener)
        return lambda: self._window_listeners.remove(listener)

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
        self._latest_averages = self._averager.close_window()
        self._schedule_window_close()
        for listener in list(self._window_listeners):
            listener(self._latest_averages)
