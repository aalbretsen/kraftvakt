"""Measures the power sensor in Home Assistant and closes the windows."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial

from homeassistant.components.recorder import get_instance, history
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    EventStateReportedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.util import dt as dt_util

from .config_model import GeneralConfig
from .measurement import (
    CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN,
    TARIFF_WINDOW,
    PowerAverager,
    WindowAverages,
    power_w,
)

type WindowListener = Callable[[WindowAverages], None]


class PowerMeasurement:
    """Follows the power sensor, with the hour before from the recorder.

    The windows keep their own cadence from the start, at absolute times, and
    every listener gets the averages when a window closes. `general` gives the
    settings in use, so a saved configuration applies without a new instance.
    """

    def __init__(self, hass: HomeAssistant, general: Callable[[], GeneralConfig]) -> None:
        self._hass = hass
        self._general = general
        self._started_at = dt_util.utcnow()
        self._averager = PowerAverager(timedelta(seconds=general().regulation_window_s), self._started_at)
        self._latest_averages: WindowAverages | None = None
        self._recent_windows: deque[WindowAverages] = deque(maxlen=CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN)
        self._listeners: list[WindowListener] = []
        self._followed_sensor: str | None = None
        self._cancel_sensor_listeners: list[CALLBACK_TYPE] = []
        self._cancel_window_timer: CALLBACK_TYPE | None = None
        self._history_task: asyncio.Task[None] | None = None

    @property
    def started_at(self) -> datetime:
        """Return when the first window started."""
        return self._started_at

    @property
    def latest_averages(self) -> WindowAverages | None:
        return self._latest_averages

    @property
    def window_start(self) -> datetime:
        return self._averager.window_start

    @property
    def window_end(self) -> datetime:
        return self._averager.window_end

    @property
    def sensor_lost(self) -> bool:
        """Return whether the power sensor was invalid at each of the last window closes."""
        return len(self._recent_windows) == self._recent_windows.maxlen and not any(window.sensor_valid for window in self._recent_windows)

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def async_start(self) -> None:
        self._follow_power_sensor(self._started_at)
        self._history_task = self._hass.async_create_background_task(self._async_add_power_history(), "kraftvakt power history")
        self._schedule_window_close()

    @callback
    def async_shutdown(self) -> None:
        if self._history_task:
            self._history_task.cancel()
            self._history_task = None
        if self._cancel_window_timer:
            self._cancel_window_timer()
            self._cancel_window_timer = None
        self._stop_following_power_sensor()

    @callback
    def async_settings_changed(self) -> None:
        """Use a new window length from the next window, and follow a new power sensor from now.

        The averages go on.
        """
        general = self._general()
        self._averager.change_window_length(timedelta(seconds=general.regulation_window_s))
        if general.power_sensor != self._followed_sensor:
            self._follow_power_sensor(dt_util.utcnow())

    def _follow_power_sensor(self, now: datetime) -> None:
        self._stop_following_power_sensor()
        power_sensor = self._followed_sensor = self._general().power_sensor
        self._record_power(now, self._hass.states.get(power_sensor) if power_sensor else None)
        if power_sensor:
            self._cancel_sensor_listeners = [
                async_track_state_change_event(self._hass, power_sensor, self._async_power_changed),
                async_track_state_report_event(self._hass, power_sensor, self._async_power_changed),
            ]

    def _stop_following_power_sensor(self) -> None:
        for cancel in self._cancel_sensor_listeners:
            cancel()
        self._cancel_sensor_listeners = []

    async def _async_add_power_history(self) -> None:
        power_sensor = self._general().power_sensor
        if not power_sensor or "recorder" not in self._hass.config.components:
            return
        states = await get_instance(self._hass).async_add_executor_job(
            partial(
                history.state_changes_during_period,
                self._hass,
                self._started_at - TARIFF_WINDOW,
                self._started_at,
                power_sensor,
            )
        )
        if power_sensor == self._followed_sensor:
            self._averager.add_history((state.last_changed, _power_of(state)) for state in states.get(power_sensor, []))

    @callback
    def _async_power_changed(self, event: Event[EventStateChangedData] | Event[EventStateReportedData]) -> None:
        self._record_power(event.time_fired, event.data["new_state"])

    def _record_power(self, when: datetime, state: State | None) -> None:
        self._averager.add_measurement(when, None if state is None else _power_of(state))

    def _invalidate_silent_power_sensor(self) -> None:
        """Count the power sensor as invalid when it has not reported for the timeout.

        A report of an unchanged value counts, since a HAN reader reports often
        also when the power does not change.
        """
        general = self._general()
        state = self._hass.states.get(general.power_sensor) if general.power_sensor else None
        window_end = self._averager.window_end
        if state is not None and window_end - state.last_reported > timedelta(seconds=general.power_sensor_timeout_s):
            self._averager.add_measurement(window_end, None)

    def _schedule_window_close(self) -> None:
        # Absolute times keep the windows from drifting.
        self._cancel_window_timer = async_track_point_in_utc_time(self._hass, self._async_window_ended, self._averager.window_end)

    @callback
    def _async_window_ended(self, _now: datetime) -> None:
        self._invalidate_silent_power_sensor()
        averages = self._averager.close_window()
        self._latest_averages = averages
        self._recent_windows.append(averages)
        self._schedule_window_close()
        for listener in list(self._listeners):
            listener(averages)


def _power_of(state: State) -> float | None:
    return power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
