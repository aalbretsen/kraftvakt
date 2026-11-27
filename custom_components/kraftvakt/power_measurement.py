"""Measures the power sensor in Home Assistant and closes the windows."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
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

from .config_model import SETTING_RANGES, GeneralConfig
from .measurement import (
    CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN,
    TARIFF_WINDOW,
    MissedWindows,
    PowerAverager,
    WindowAverages,
    WindowClock,
    power_w,
)
from .repairs import async_clear_silence_near_timeout, async_report_silence_near_timeout
from .report_analysis import ANALYSED_PERIOD, ReportAnalysis, ReportLog, analyse_reports, suggested_timeout_s

_LOGGER = logging.getLogger(__name__)

type WindowListener = Callable[[WindowAverages], None]


@dataclass(frozen=True, slots=True)
class _ClosedWindow:
    end: datetime
    by_update: bool


@dataclass(frozen=True, slots=True)
class WindowCloses:
    """How the windows of the last hour closed."""

    by_update: int
    by_clock: int


class PowerMeasurement:
    """Follows the power sensor, with the hour before from the recorder.

    The windows close by Kraftvakt's own clock in step with the updates of the
    power sensor (see `WindowClock`), and every listener gets the averages.
    The update interval is learned from the updates of the last hour, and a
    silence of at least half the power sensor timeout is reported as a repair
    issue. `general` gives the settings in use, so a saved configuration
    applies without a new instance. `windows_skipped` is called when missed
    windows are skipped, since the next window end has then moved without a
    window closing.
    """

    def __init__(self, hass: HomeAssistant, general: Callable[[], GeneralConfig], windows_skipped: Callable[[], None]) -> None:
        self._hass = hass
        self._general = general
        self._windows_skipped = windows_skipped
        self._started_at = dt_util.utcnow()
        self._averager = PowerAverager(self._started_at)
        self._clock = WindowClock(self.window_length, self._started_at)
        self._report_log = ReportLog()
        self._closed_windows: deque[_ClosedWindow] = deque()
        self._reported_silence: timedelta | None = None
        self._latest_averages: WindowAverages | None = None
        self._recent_windows: deque[WindowAverages] = deque(maxlen=CONSECUTIVE_INVALID_CLOSES_BEFORE_UNKNOWN)
        self._listeners: list[WindowListener] = []
        self._followed_sensor: str | None = None
        self._last_update_at: datetime | None = None
        self._silent = False
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
        return timedelta(seconds=self._general().regulation_window_s)

    @property
    def window_end(self) -> datetime:
        """Return the update expected to close the current window."""
        return self._clock.expected_end

    @property
    def sensor_valid(self) -> bool:
        return self._averager.sensor_valid

    @property
    def sensor_silent(self) -> bool:
        """Return whether the power sensor has not reported for the power sensor timeout."""
        return self._silent

    @property
    def followed_sensor(self) -> str | None:
        return self._followed_sensor

    @property
    def last_update_at(self) -> datetime | None:
        return self._last_update_at

    @property
    def last_missed_windows(self) -> MissedWindows | None:
        return self._averager.last_missed_windows

    @property
    def measurements(self) -> list[tuple[datetime, float]]:
        return self._averager.measurements

    @property
    def sensor_lost(self) -> bool:
        """Return whether the power sensor was invalid at each of the last window closes."""
        return len(self._recent_windows) == self._recent_windows.maxlen and not any(window.sensor_valid for window in self._recent_windows)

    def report_analysis(self) -> ReportAnalysis:
        """Return how the power sensor has reported over the last hour."""
        return self._report_log.analysis(dt_util.utcnow())

    def window_closes(self) -> WindowCloses:
        """Return how the windows of the last hour closed."""
        self._forget_closed_windows(dt_util.utcnow())
        by_update = sum(window.by_update for window in self._closed_windows)
        return WindowCloses(by_update, len(self._closed_windows) - by_update)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "started_at": self._started_at,
            "power_sensor": self._followed_sensor,
            "following_power_sensor": bool(self._cancel_sensor_listeners),
            "last_update_at": self._last_update_at,
            "silent": self._silent,
            "silence_timer_set": self._cancel_silence_timer is not None,
            "clock_close_scheduled": self._cancel_clock_timer is not None,
            "reading_history": self._history_task is not None and not self._history_task.done(),
            "latest_averages": self._latest_averages,
            "recent_windows": self._recent_windows,
            "window_closes": self.window_closes(),
            "reported_silence": self._reported_silence,
            "averager": self._averager.diagnostics(),
            "window_clock": self._clock.diagnostics(),
            "report_log": self._report_log.diagnostics(),
        }

    @callback
    def async_add_window_listener(self, listener: WindowListener) -> CALLBACK_TYPE:
        """Call `listener` with the averages each time a window closes."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def async_start(self) -> None:
        self._follow_power_sensor(self._started_at)
        self._schedule_clock()
        self._history_task = self._hass.async_create_background_task(self._async_add_power_history(), "kraftvakt power history")

    @callback
    def async_shutdown(self) -> None:
        if self._history_task:
            self._history_task.cancel()
            self._history_task = None
        self._clear_silence_issue()
        self._stop_silence_timer()
        self._stop_clock()
        self._stop_following_power_sensor()

    @callback
    def async_settings_changed(self) -> None:
        """Follow a new power sensor from now, with its update interval learned anew, and use a new timeout.

        The averages go on, and a new regulation window applies from the next window.
        """
        general = self._general()
        self._clear_silence_issue()
        now = dt_util.utcnow()
        if general.power_sensor != self._followed_sensor:
            self._follow_power_sensor(now)
        elif self._cancel_silence_timer is not None:
            state = self._hass.states.get(general.power_sensor) if general.power_sensor else None
            self._restart_silence_timer(now if state is None else state.last_reported)

    def _follow_power_sensor(self, now: datetime) -> None:
        self._stop_following_power_sensor()
        self._report_log.clear()
        self._closed_windows.clear()
        self._last_update_at = None
        self._silent = False
        self._averager.set_update_interval(None)
        power_sensor = self._followed_sensor = self._general().power_sensor
        state = self._hass.states.get(power_sensor) if power_sensor else None
        self._averager.add_measurement(now, None if state is None else _power_of(state))
        if power_sensor:
            self._cancel_sensor_listeners = [
                async_track_state_change_event(self._hass, power_sensor, self._async_power_reported),
                async_track_state_report_event(self._hass, power_sensor, self._async_power_reported),
            ]
        self._restart_silence_timer(now if state is None else min(state.last_reported, now))

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
        self._last_update_at = now
        self._silent = False
        self._report_log.add(now)
        self._averager.add_measurement(now, None if state is None else _power_of(state))
        self._restart_silence_timer(now)
        if self._clock.update(now):
            self._close_window(now, by_update=True)
        else:
            self._schedule_clock()

    def _restart_silence_timer(self, reported_at: datetime) -> None:
        """Start the timeout from the last report, or count the sensor as silent at once when the timeout has already passed, as for one silent before it was followed."""
        self._stop_silence_timer()
        timeout_at = reported_at + timedelta(seconds=self._general().power_sensor_timeout_s)
        now = dt_util.utcnow()
        if timeout_at <= now:
            self._silent = True
            self._averager.add_measurement(now, None)
            return
        self._cancel_silence_timer = async_track_point_in_utc_time(self._hass, self._async_sensor_silent, timeout_at)

    @callback
    def _async_sensor_silent(self, timeout_at: datetime) -> None:
        """Count the power sensor as invalid, since it has not reported for the timeout.

        A report of an unchanged value counts, since a HAN reader reports often
        also when the power does not change. A timeout noticed a whole window or
        more late comes after the event loop was paused, when the reports could
        not be received, so the timeout starts again, and the windows are
        skipped unless the clock has skipped them already.
        """
        self._cancel_silence_timer = None
        now = dt_util.utcnow()
        if now - timeout_at >= self.window_length:
            if self._clock.close_at <= now:
                self._skip_windows(now, now)
            self._restart_silence_timer(now)
            return
        self._silent = True
        self._averager.add_measurement(timeout_at, None)

    def _schedule_clock(self) -> None:
        self._stop_clock()
        self._cancel_clock_timer = async_track_point_in_utc_time(self._hass, self._async_clock_close, self._clock.close_at)

    @callback
    def _async_clock_close(self, scheduled: datetime) -> None:
        """Close the window by the clock, or skip it and the windows after it when it closes a whole window or more late.

        A late close comes after the event loop of Home Assistant was paused,
        and closing the missed windows one by one would replay their decisions
        at once. The cadence is kept, so the window running now is next.
        """
        self._cancel_clock_timer = None
        now = dt_util.utcnow()
        length = self._clock.length
        if missed := (now - scheduled) // length:
            anchor = self._clock.expected_end + missed * length
            self._skip_windows(anchor, anchor)
            return
        self._close_window(scheduled, by_update=False)

    def _skip_windows(self, until: datetime, anchor: datetime) -> None:
        skipped = self._averager.skip_windows(until)
        self._start_clock(anchor)
        _LOGGER.warning(
            "Skipped the windows from %s to %s, missed while the event loop of Home Assistant was paused",
            dt_util.as_local(skipped.start).isoformat(timespec="seconds"),
            dt_util.as_local(skipped.end).isoformat(timespec="seconds"),
        )
        self._windows_skipped()

    def _close_window(self, end: datetime, *, by_update: bool) -> None:
        averages = self._averager.close_window(end)
        self._latest_averages = averages
        self._recent_windows.append(averages)
        self._closed_windows.append(_ClosedWindow(end, by_update))
        self._forget_closed_windows(end)
        analysis = self._report_log.analysis(end)
        self._averager.set_update_interval(analysis.update_interval)
        self._start_clock(end if by_update else self._clock.expected_end, analysis)
        self._check_silence(analysis)
        for listener in list(self._listeners):
            listener(averages)

    def _start_clock(self, anchor: datetime, analysis: ReportAnalysis | None = None) -> None:
        update_interval = (analysis or self._report_log.analysis(anchor)).update_interval
        self._clock.start(anchor, self.window_length, update_interval)
        self._schedule_clock()

    def _forget_closed_windows(self, now: datetime) -> None:
        while self._closed_windows and self._closed_windows[0].end < now - ANALYSED_PERIOD:
            self._closed_windows.popleft()

    def _check_silence(self, analysis: ReportAnalysis) -> None:
        """Report a longest silence of at least half the power sensor timeout, and remove the report when it is shorter again."""
        general = self._general()
        silence = analysis.longest_silence
        if silence is None or silence * 2 < timedelta(seconds=general.power_sensor_timeout_s):
            self._clear_silence_issue()
            return
        if silence == self._reported_silence:
            return
        if self._reported_silence is None:
            _LOGGER.warning(
                "The power sensor %s has been silent for up to %.0f s, at least half its timeout of %d s",
                self._followed_sensor,
                silence.total_seconds(),
                general.power_sensor_timeout_s,
            )
        self._reported_silence = silence
        async_report_silence_near_timeout(self._hass, self._followed_sensor or "", silence.total_seconds(), general.power_sensor_timeout_s)

    def _clear_silence_issue(self) -> None:
        if self._reported_silence is not None:
            self._reported_silence = None
            async_clear_silence_near_timeout(self._hass)

    def _stop_silence_timer(self) -> None:
        if self._cancel_silence_timer:
            self._cancel_silence_timer()
            self._cancel_silence_timer = None

    def _stop_clock(self) -> None:
        if self._cancel_clock_timer:
            self._cancel_clock_timer()
            self._cancel_clock_timer = None


async def async_analyse_power_sensor(hass: HomeAssistant, entity_id: str) -> ReportAnalysis:
    """Return how a power sensor reports, from its changes in the recorder over the last hour, or by listening to it as well when they say too little.

    The recorder keeps only changes. A HAN reader that reports at a fixed
    interval has a change at almost every update, and one that reports only
    when the power changes has one at every update, so the history is enough
    when it shows an update interval. Otherwise the updates, also of unchanged
    values, are listened to for up to 30 seconds.
    """
    changed_at: list[datetime] = []
    if "recorder" in hass.config.components:
        now = dt_util.utcnow()
        states = await get_instance(hass).async_add_executor_job(partial(history.state_changes_during_period, hass, now - ANALYSED_PERIOD, now, entity_id))
        changed_at = [state.last_changed for state in states.get(entity_id, [])]
        if (analysis := analyse_reports(changed_at)).update_interval is not None:
            return analysis
    return analyse_reports(changed_at + await _async_listen_for_updates(hass, entity_id, changed_at[-1] if changed_at else None))


async def _async_listen_for_updates(hass: HomeAssistant, entity_id: str, last_changed: datetime | None) -> list[datetime]:
    state = hass.states.get(entity_id)
    reported_at = [] if state is None or state.last_reported == last_changed else [state.last_reported]
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
    return reported_at


def power_sensor_timeout_suggestion(analysis: ReportAnalysis) -> int:
    """Return the power sensor timeout suggested for how the power sensor reports, within the range of the setting."""
    timeout_range = SETTING_RANGES["general"]["power_sensor_timeout_s"]
    return suggested_timeout_s(analysis, GeneralConfig().power_sensor_timeout_s, int(timeout_range.maximum or timeout_range.minimum))


def report_analysis_dict(analysis: ReportAnalysis) -> dict[str, Any]:
    """Return how the power sensor reports, in seconds, with the power sensor timeout suggested for it, for the panel."""
    return {
        "updates": analysis.updates,
        "update_interval_s": _seconds(analysis.update_interval),
        "steady": analysis.steady,
        "shortest_s": _seconds(analysis.shortest),
        "longest_silence_s": _seconds(analysis.longest_silence),
        "lost_updates": analysis.lost_updates,
        "suggested_timeout_s": power_sensor_timeout_suggestion(analysis),
    }


def _seconds(duration: timedelta | None) -> float | None:
    return None if duration is None else round(duration.total_seconds(), 1)


def _power_of(state: State) -> float | None:
    return power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
