"""Measures the power sensor in Home Assistant and closes the windows."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import partial
from typing import Any

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

from .config_model import REGULATION_WINDOW_S, GeneralConfig
from .measurement import (
    CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN,
    TARIFF_WINDOW,
    PowerAverager,
    WindowAverages,
    power_w,
    update_interval_s,
)

_LOGGER = logging.getLogger(__name__)

type WindowListener = Callable[[WindowAverages], None]


class PowerMeasurement:
    """Follows the power sensor, with the hour before from the recorder.

    A window closes at the update of the power sensor that completes its number
    of updates, and every listener gets the averages. While the power sensor is
    invalid, because it reported an invalid value or has not reported for the
    power sensor timeout, a window also closes by the clock when it has lasted
    its length, so the safe state comes without updates. `general` gives the
    settings in use, so a saved configuration applies without a new instance.
    `windows_skipped` is called when missed windows are skipped, since the next
    window end has then moved without a window closing.
    """

    def __init__(self, hass: HomeAssistant, general: Callable[[], GeneralConfig], windows_skipped: Callable[[], None]) -> None:
        self._hass = hass
        self._general = general
        self._windows_skipped = windows_skipped
        self._started_at = dt_util.utcnow()
        self._averager = PowerAverager(self._updates_per_window(), self._started_at)
        self._latest_averages: WindowAverages | None = None
        self._recent_windows: deque[WindowAverages] = deque(maxlen=CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN)
        self._listeners: list[WindowListener] = []
        self._followed_sensor: str | None = None
        self._cancel_sensor_listeners: list[CALLBACK_TYPE] = []
        self._cancel_silence_timer: CALLBACK_TYPE | None = None
        self._cancel_clock_timer: CALLBACK_TYPE | None = None
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
    def window_length(self) -> timedelta:
        """Return how long a window lasts when the power sensor reports at its interval, the shortest window until it is set."""
        return self._general().regulation_window_length or timedelta(seconds=REGULATION_WINDOW_S.minimum)

    @property
    def window_end(self) -> datetime:
        """Return when the current window is expected to close."""
        return self._averager.window_start + self.window_length

    @property
    def sensor_lost(self) -> bool:
        """Return whether the power sensor was invalid at each of the last window closes."""
        return len(self._recent_windows) == self._recent_windows.maxlen and not any(window.sensor_valid for window in self._recent_windows)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "started_at": self._started_at,
            "power_sensor": self._followed_sensor,
            "following_power_sensor": bool(self._cancel_sensor_listeners),
            "silence_timer_set": self._cancel_silence_timer is not None,
            "clock_close_scheduled": self._cancel_clock_timer is not None,
            "reading_history": self._history_task is not None and not self._history_task.done(),
            "latest_averages": self._latest_averages,
            "recent_windows": self._recent_windows,
            "averager": self._averager.diagnostics(),
        }

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def async_start(self) -> None:
        self._follow_power_sensor(self._started_at)
        self._history_task = self._hass.async_create_background_task(self._async_add_power_history(), "kraftvakt power history")

    @callback
    def async_shutdown(self) -> None:
        if self._history_task:
            self._history_task.cancel()
            self._history_task = None
        self._stop_silence_timer()
        self._stop_clock()
        self._stop_following_power_sensor()

    @callback
    def async_settings_changed(self) -> None:
        """Use a new number of updates from the next window, follow a new power sensor from now, and a new timeout.

        The averages go on.
        """
        general = self._general()
        self._averager.change_updates_per_window(self._updates_per_window())
        now = dt_util.utcnow()
        if general.power_sensor != self._followed_sensor:
            self._follow_power_sensor(now)
        elif self._cancel_silence_timer is not None:
            state = self._hass.states.get(general.power_sensor) if general.power_sensor else None
            self._restart_silence_timer(now if state is None else state.last_reported)

    def _updates_per_window(self) -> int:
        return self._general().regulation_window_updates or 1

    def _follow_power_sensor(self, now: datetime) -> None:
        self._stop_following_power_sensor()
        power_sensor = self._followed_sensor = self._general().power_sensor
        state = self._hass.states.get(power_sensor) if power_sensor else None
        self._averager.add_measurement(now, None if state is None else _power_of(state), update=False)
        if power_sensor:
            self._cancel_sensor_listeners = [
                async_track_state_change_event(self._hass, power_sensor, self._async_power_reported),
                async_track_state_report_event(self._hass, power_sensor, self._async_power_reported),
            ]
        self._restart_silence_timer(now if state is None else min(state.last_reported, now))
        self._follow_validity(now)

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
    def _async_power_reported(self, event: Event[EventStateChangedData] | Event[EventStateReportedData]) -> None:
        state = event.data["new_state"]
        now = event.time_fired
        self._averager.add_measurement(now, None if state is None else _power_of(state))
        self._restart_silence_timer(now)
        if self._averager.window_complete:
            self._close_window(now)
        else:
            self._follow_validity(now)

    def _restart_silence_timer(self, reported_at: datetime) -> None:
        self._stop_silence_timer()
        timeout = timedelta(seconds=self._general().power_sensor_timeout_s)
        self._cancel_silence_timer = async_track_point_in_utc_time(self._hass, self._async_sensor_silent, reported_at + timeout)

    @callback
    def _async_sensor_silent(self, timeout_at: datetime) -> None:
        """Count the power sensor as invalid, since it has not reported for the timeout.

        A report of an unchanged value counts, since a HAN reader reports often
        also when the power does not change. A timeout noticed a whole window or
        more late comes after the event loop was paused, when the reports could
        not be received, so the windows are skipped and the timeout starts again.
        """
        self._cancel_silence_timer = None
        now = dt_util.utcnow()
        if now - timeout_at >= self.window_length:
            self._skip_windows(now)
            self._restart_silence_timer(now)
            return
        self._averager.add_measurement(timeout_at, None, update=False)
        self._follow_validity(timeout_at)

    def _follow_validity(self, now: datetime) -> None:
        """Close windows by the clock while the power sensor is invalid, and by its updates again when it is valid."""
        if self._averager.sensor_valid:
            self._stop_clock()
        elif self.window_end <= now:
            self._close_window(now)
        elif self._cancel_clock_timer is None:
            self._cancel_clock_timer = async_track_point_in_utc_time(self._hass, self._async_clock_close, self.window_end)

    @callback
    def _async_clock_close(self, scheduled: datetime) -> None:
        """Close the window by the clock, or skip it and the windows after it when it closes a whole window or more late.

        A late close comes after the event loop of Home Assistant was paused,
        and closing the missed windows one by one would replay their decisions
        at once. The cadence is kept, so the window running now is next.
        """
        self._cancel_clock_timer = None
        now = dt_util.utcnow()
        length = self.window_length
        if missed := (now - scheduled) // length:
            self._skip_windows(scheduled + missed * length)
            self._follow_validity(now)
            return
        self._close_window(scheduled)

    def _skip_windows(self, until: datetime) -> None:
        skipped = self._averager.skip_windows(until)
        _LOGGER.warning(
            "Skipped the windows from %s to %s, missed while the event loop of Home Assistant was paused",
            dt_util.as_local(skipped.start).isoformat(timespec="seconds"),
            dt_util.as_local(skipped.end).isoformat(timespec="seconds"),
        )
        self._windows_skipped()

    def _close_window(self, end: datetime) -> None:
        averages = self._averager.close_window(end)
        self._latest_averages = averages
        self._recent_windows.append(averages)
        self._stop_clock()
        self._follow_validity(end)
        for listener in list(self._listeners):
            listener(averages)

    def _stop_silence_timer(self) -> None:
        if self._cancel_silence_timer:
            self._cancel_silence_timer()
            self._cancel_silence_timer = None

    def _stop_clock(self) -> None:
        if self._cancel_clock_timer:
            self._cancel_clock_timer()
            self._cancel_clock_timer = None


async def async_measure_update_interval(hass: HomeAssistant, entity_id: str) -> float | None:
    """Return how often the sensor reports, in seconds, or None when it cannot be found.

    The recorder keeps only changes, which a HAN reader has at almost every
    update, so the history of the last ten minutes is used when its changes
    are regular. Otherwise the reports of the sensor, also of unchanged values,
    are listened to for up to 30 seconds.
    """
    if "recorder" in hass.config.components:
        now = dt_util.utcnow()
        states = await get_instance(hass).async_add_executor_job(partial(history.state_changes_during_period, hass, now - timedelta(minutes=10), now, entity_id))
        changed_at = [state.last_changed for state in states.get(entity_id, [])][-31:]
        if (interval_s := update_interval_s(changed_at, fewest_intervals=10)) is not None:
            return interval_s
    return await _async_listen_for_update_interval(hass, entity_id)


async def _async_listen_for_update_interval(hass: HomeAssistant, entity_id: str) -> float | None:
    state = hass.states.get(entity_id)
    reported_at = [] if state is None else [state.last_reported]
    done = asyncio.Event()

    @callback
    def reported(event: Event[EventStateChangedData] | Event[EventStateReportedData]) -> None:
        reported_at.append(event.time_fired)
        if len(reported_at) > 4:
            done.set()

    @callback
    def listened_long_enough(_now: datetime) -> None:
        done.set()

    cancels = [
        async_track_state_change_event(hass, entity_id, reported),
        async_track_state_report_event(hass, entity_id, reported),
        async_track_point_in_utc_time(hass, listened_long_enough, dt_util.utcnow() + timedelta(seconds=30)),
    ]
    try:
        await done.wait()
    finally:
        for cancel in cancels:
            cancel()
    return update_interval_s(reported_at, fewest_intervals=2)


def _power_of(state: State) -> float | None:
    return power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
