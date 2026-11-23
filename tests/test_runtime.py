"""Tests for the measurement part of the runtime."""

import logging
from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.kraftvakt.config_model import GeneralConfig, KraftvaktConfig
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.measurement import WindowAverages
from custom_components.kraftvakt.runtime import KraftvaktRuntime
from custom_components.kraftvakt.settings import Settings
from custom_components.kraftvakt.storage import KraftvaktStorage, StoredData

POWER_SENSOR = "sensor.han_power"
INTERVAL = timedelta(seconds=10)
WINDOW = 3 * INTERVAL


def config_with(power_sensor: str | None = POWER_SENSOR, updates: int = 3) -> KraftvaktConfig:
    return KraftvaktConfig(general=GeneralConfig(power_sensor=power_sensor, regulation_window_updates=updates, power_sensor_interval_s=INTERVAL.total_seconds()))


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta) -> None:
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def report(hass: HomeAssistant, freezer: FrozenDateTimeFactory, state: str, unit: str = "W", after: timedelta = INTERVAL) -> None:
    """Move time on and let the power sensor report, also an unchanged value, as a HAN reader does."""
    freezer.tick(after)
    hass.states.async_set(POWER_SENSOR, state, {"unit_of_measurement": unit})
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


@pytest.fixture
def closed_windows() -> list[WindowAverages]:
    return []


@pytest.fixture
def start_runtime(hass: HomeAssistant, closed_windows: list[WindowAverages]):
    runtimes: list[KraftvaktRuntime] = []

    def start(config: KraftvaktConfig) -> KraftvaktRuntime:
        storage = KraftvaktStorage(hass)
        settings = Settings(hass, storage, StoredData(config))
        runtime = KraftvaktRuntime(hass, settings)
        runtime.async_add_window_listener(closed_windows.append)
        runtime.async_start()
        runtimes.append(runtime)
        return runtime

    yield start
    for runtime in runtimes:
        runtime.async_shutdown()


async def test_window_closes_at_the_update_that_completes_it(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """A missing update makes the window longer, and the next starts where it closed."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    runtime = start_runtime(config_with())

    for after in (INTERVAL, INTERVAL, INTERVAL, INTERVAL, 2 * INTERVAL, INTERVAL):
        await report(hass, freezer, "2000", after=after)

    assert [(window.start, window.end) for window in closed_windows] == [
        (started, started + WINDOW),
        (started + WINDOW, started + 2 * WINDOW + INTERVAL),
    ]
    assert runtime.latest_averages == closed_windows[-1]
    assert runtime.window_length == WINDOW


async def test_each_update_covers_the_time_before_it(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """The power sensor is read in W or kW, and the update that closes the window counts in it."""
    hass.states.async_set(POWER_SENSOR, "1000", {"unit_of_measurement": "W"})
    start_runtime(config_with())

    await report(hass, freezer, "2000")
    await report(hass, freezer, "5", "kW")
    await report(hass, freezer, "8000")

    averages = closed_windows[-1]
    assert averages.regulation_average_w == pytest.approx((2000 + 5000 + 8000) / 3)
    assert averages.sensor_valid


async def test_window_of_one_update_is_the_value_of_that_update(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """A HAN reader that reports every 10 seconds gives a window of 10 seconds with only the newest measurement."""
    hass.states.async_set(POWER_SENSOR, "1000", {"unit_of_measurement": "W"})
    start_runtime(config_with(updates=1))

    await report(hass, freezer, "2000")
    await report(hass, freezer, "5000")

    assert [window.regulation_average_w for window in closed_windows] == [2000, 5000]


async def test_invalid_power_sensor_closes_windows_by_the_clock(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """An unavailable or removed sensor counts as no valid measurement, and the windows close when they have lasted their length."""
    hass.states.async_set(POWER_SENSOR, "3000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    start_runtime(config_with())

    await report(hass, freezer, "unavailable")
    await advance(hass, freezer, 2 * INTERVAL)
    hass.states.async_remove(POWER_SENSOR)
    await advance(hass, freezer, WINDOW)

    first, second = closed_windows
    assert (first.end, first.regulation_average_w, first.sensor_valid) == (started + WINDOW, 3000, False)
    assert (second.end, second.regulation_average_w, second.sensor_valid) == (started + 2 * WINDOW, None, False)


async def test_valid_power_sensor_closes_windows_by_its_updates_again(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    hass.states.async_set(POWER_SENSOR, "unavailable")
    started = dt_util.utcnow()
    start_runtime(config_with())

    await advance(hass, freezer, WINDOW)
    for _ in range(3):
        await report(hass, freezer, "2000", after=INTERVAL + timedelta(seconds=5))
    await advance(hass, freezer, WINDOW)

    assert [(window.end, window.sensor_valid) for window in closed_windows] == [(started + WINDOW, False), (started + WINDOW + 3 * (INTERVAL + timedelta(seconds=5)), True)]


async def test_silent_power_sensor_is_invalid_after_the_timeout(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """A report of an unchanged value counts, but a sensor that does not report at all is lost."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    start_runtime(config_with())

    await advance(hass, freezer, timedelta(seconds=300))
    await advance(hass, freezer, WINDOW)

    assert [(window.end, window.regulation_average_w, window.sensor_valid) for window in closed_windows] == [
        (started + timedelta(seconds=300), 2000, False),
        (started + timedelta(seconds=300) + WINDOW, None, False),
    ]


async def test_power_sensor_silent_for_the_timeout_before_it_is_followed_is_invalid_at_once(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows, caplog: pytest.LogCaptureFixture
) -> None:
    """As at a reload while the HAN reader is silent: no paused event loop, and the windows close by the clock."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    await advance(hass, freezer, timedelta(seconds=400))
    started = dt_util.utcnow()

    with caplog.at_level(logging.WARNING):
        start_runtime(config_with())
        await advance(hass, freezer, WINDOW)

    assert [(window.end, window.sensor_valid) for window in closed_windows] == [(started + WINDOW, False)]
    assert "Skipped the windows" not in caplog.text


async def test_windows_close_by_the_clock_without_power_sensor(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """Without a configured power sensor there are no averages."""
    start_runtime(config_with(power_sensor=None))

    await advance(hass, freezer, WINDOW)

    assert closed_windows[0].regulation_average_w is None
    assert not closed_windows[0].sensor_valid


async def test_missed_clock_windows_are_skipped(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows, caplog: pytest.LogCaptureFixture) -> None:
    """A clock close a whole window or more late, as after a paused event loop, closes nothing, and the cadence is kept."""
    hass.states.async_set(POWER_SENSOR, "unavailable")
    started = dt_util.utcnow()
    start_runtime(config_with())

    with caplog.at_level(logging.WARNING):
        await advance(hass, freezer, 3 * WINDOW + INTERVAL)

    assert closed_windows == []
    assert "Skipped the windows" in caplog.text
    await advance(hass, freezer, 2 * INTERVAL)
    assert [window.start for window in closed_windows] == [started + 3 * WINDOW]


async def test_shutdown_stops_measuring_and_closing_windows(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    runtime = start_runtime(config_with())

    runtime.async_shutdown()
    for _ in range(3):
        await report(hass, freezer, "4000")
    await advance(hass, freezer, timedelta(seconds=600))

    assert closed_windows == []


async def test_removed_listener_is_not_called(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    runtime = start_runtime(config_with(power_sensor=None))
    calls: list[WindowAverages] = []
    remove = runtime.async_add_window_listener(calls.append)

    remove()
    await advance(hass, freezer, WINDOW)

    assert calls == []
    assert len(closed_windows) == 1


async def test_extra_report_does_not_close_a_window_that_has_just_started(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """A Kamstrup meter sends its hourly list a few seconds after a report, and it counts in the window it comes in."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    start_runtime(config_with(updates=1))

    await report(hass, freezer, "2000")
    await report(hass, freezer, "4000", after=timedelta(seconds=5))
    await report(hass, freezer, "2000", after=timedelta(seconds=5))

    assert [(window.end, window.regulation_average_w) for window in closed_windows] == [
        (started + INTERVAL, 2000),
        (started + 2 * INTERVAL, 3000),
    ]


def interval_issue(hass: HomeAssistant) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(DOMAIN, "power_sensor_interval_changed")


async def test_power_sensor_that_reports_at_another_interval_is_a_repair_issue(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, caplog: pytest.LogCaptureFixture
) -> None:
    """Five windows in a row closed after another interval raise the issue, and five at the update interval clear it."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    start_runtime(config_with(updates=1))
    await report(hass, freezer, "2000")

    for _ in range(4):
        await report(hass, freezer, "2000", after=2 * INTERVAL)
    assert interval_issue(hass) is None
    await report(hass, freezer, "2000", after=2 * INTERVAL)

    issue = interval_issue(hass)
    assert issue is not None
    assert issue.translation_placeholders == {"reported_interval": "20.0", "update_interval": "10.0"}
    assert "reports about every 20.0 s, not every 10.0 s" in caplog.text

    for _ in range(5):
        await report(hass, freezer, "2000")
    assert interval_issue(hass) is None


async def test_a_new_update_interval_starts_the_check_again(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime) -> None:
    """The issue is removed when the power sensor is chosen again with its update interval measured again, and when Kraftvakt stops.

    The window running at the save keeps the old settings, and the windows after it have two of the reports every 10 seconds each.
    """
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    runtime = start_runtime(config_with(updates=1))
    await report(hass, freezer, "2000")
    for _ in range(5):
        await report(hass, freezer, "2000", after=2 * INTERVAL)
    assert interval_issue(hass) is not None

    runtime.async_stop_regulation()
    await runtime.async_save_config(KraftvaktConfig(general=GeneralConfig(power_sensor=POWER_SENSOR, regulation_window_updates=1, power_sensor_interval_s=20.0)))
    assert interval_issue(hass) is None

    for _ in range(10):
        await report(hass, freezer, "2000", after=INTERVAL)
    assert interval_issue(hass) is None
    await report(hass, freezer, "2000", after=INTERVAL)
    assert interval_issue(hass) is not None
    runtime.async_shutdown()
    assert interval_issue(hass) is None
