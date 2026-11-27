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


def config_with(power_sensor: str | None = POWER_SENSOR, window: timedelta = WINDOW, timeout_s: int = 300) -> KraftvaktConfig:
    general = GeneralConfig(power_sensor=power_sensor, regulation_window_s=int(window.total_seconds()), power_sensor_timeout_s=timeout_s)
    return KraftvaktConfig(general=general)


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


async def test_windows_close_by_the_clock_in_step_with_the_updates(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """At the update at the end of the window, also before the update interval is known, and by the clock after the update expected when one is lost."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    runtime = start_runtime(config_with())

    for after in (INTERVAL, INTERVAL, INTERVAL, INTERVAL, 2 * INTERVAL, *[INTERVAL] * 5):
        await report(hass, freezer, "2000", after=after)
    await advance(hass, freezer, timedelta(seconds=12))
    for _ in range(3):
        await report(hass, freezer, "2000", after=INTERVAL if _ else timedelta(seconds=8))

    assert [((window.start - started).total_seconds(), (window.end - started).total_seconds()) for window in closed_windows] == [
        (0, 30),
        (30, 60),
        (60, 90),
        (90, 122),
        (122, 150),
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
    start_runtime(config_with(window=INTERVAL))

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
    for _ in range(2):
        await report(hass, freezer, "2000", after=timedelta(seconds=15))

    assert [(window.end, window.sensor_valid) for window in closed_windows] == [(started + WINDOW, False), (started + 2 * WINDOW, True)]


async def test_silent_power_sensor_is_invalid_after_the_timeout(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows) -> None:
    """A report of an unchanged value counts, but a sensor that does not report at all is lost, and its last value holds until then."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    runtime = start_runtime(config_with())

    for _ in range(12):
        await advance(hass, freezer, WINDOW)
    assert runtime.power_sensor_silent

    first_invalid = next(index for index, window in enumerate(closed_windows) if not window.sensor_valid)
    assert closed_windows[first_invalid].end == dt_util.utcnow() - 2 * WINDOW
    assert [(window.regulation_average_w, window.sensor_valid) for window in closed_windows[:first_invalid]] == [(2000, True)] * first_invalid
    assert [(window.regulation_average_w, window.sensor_valid) for window in closed_windows[first_invalid : first_invalid + 2]] == [(2000, False), (None, False)]
    await report(hass, freezer, "2000")
    assert not runtime.power_sensor_silent


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


async def test_a_timeout_noticed_late_skips_the_windows_once(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows, caplog: pytest.LogCaptureFixture
) -> None:
    """With a timeout shorter than the window, the timeout notices the paused event loop first, and the clock does not skip the windows again."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    start_runtime(config_with(timeout_s=10))

    with caplog.at_level(logging.WARNING):
        await advance(hass, freezer, 5 * WINDOW)
        await advance(hass, freezer, timedelta(seconds=1))

    assert closed_windows == []
    assert caplog.text.count("Skipped the windows") == 1


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
    start_runtime(config_with(window=INTERVAL))

    await report(hass, freezer, "2000")
    await report(hass, freezer, "4000", after=timedelta(seconds=5))
    await report(hass, freezer, "2000", after=timedelta(seconds=5))

    assert [(window.end, window.regulation_average_w) for window in closed_windows] == [
        (started + INTERVAL, 2000),
        (started + 2 * INTERVAL, 3000),
    ]


def silence_issue(hass: HomeAssistant) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(DOMAIN, "power_sensor_silence_near_timeout")


async def report_steadily_then_be_silent(hass: HomeAssistant, freezer: FrozenDateTimeFactory, silence: timedelta) -> None:
    for _ in range(4):
        await report(hass, freezer, "2000")
    await report(hass, freezer, "2000", after=silence)
    await report(hass, freezer, "2000")


async def test_a_silence_of_half_the_timeout_is_a_repair_issue(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, caplog: pytest.LogCaptureFixture) -> None:
    """As from a reader that reports only when the power changes, and it is removed when the silence has left the last hour."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    start_runtime(config_with(window=INTERVAL, timeout_s=60))

    await report_steadily_then_be_silent(hass, freezer, timedelta(seconds=29))
    assert silence_issue(hass) is None
    await report_steadily_then_be_silent(hass, freezer, timedelta(seconds=40))

    issue = silence_issue(hass)
    assert issue is not None
    assert issue.translation_placeholders == {"power_sensor": POWER_SENSOR, "silence": "40", "timeout": "60"}
    assert "silent for up to 40 s, at least half its timeout of 60 s" in caplog.text

    for _ in range(360):
        await report(hass, freezer, "2000")
    assert silence_issue(hass) is None


async def test_another_timeout_and_a_shutdown_remove_the_silence_issue(hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime) -> None:
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    runtime = start_runtime(config_with(window=INTERVAL, timeout_s=60))
    await report_steadily_then_be_silent(hass, freezer, timedelta(seconds=40))
    assert silence_issue(hass) is not None

    runtime.async_stop_regulation()
    await runtime.async_save_config(config_with(window=INTERVAL, timeout_s=120))
    assert silence_issue(hass) is None
    await report(hass, freezer, "2000")
    assert silence_issue(hass) is None

    await runtime.async_save_config(config_with(window=INTERVAL, timeout_s=60))
    await report(hass, freezer, "2000")
    assert silence_issue(hass) is not None
    runtime.async_shutdown()
    assert silence_issue(hass) is None
