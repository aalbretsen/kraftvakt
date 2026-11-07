"""Tests for the measurement part of the runtime (GEN-003, MAL-001, MAL-006)."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.kraftvakt.charger_switches import ChargerSwitchBoard
from custom_components.kraftvakt.config_model import GeneralConfig, KraftvaktConfig
from custom_components.kraftvakt.measurement import WindowAverages
from custom_components.kraftvakt.runtime import KraftvaktRuntime
from custom_components.kraftvakt.storage import KraftvaktStorage, StoredData

POWER_SENSOR = "sensor.han_power"
WINDOW = timedelta(seconds=30)


def config_with(power_sensor: str | None = POWER_SENSOR) -> KraftvaktConfig:
    return KraftvaktConfig(
        general=GeneralConfig(power_sensor=power_sensor, regulation_window_s=30)
    )


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta
) -> None:
    freezer.tick(delta)
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
        board = ChargerSwitchBoard(hass, storage, StoredData(config))
        runtime = KraftvaktRuntime(hass, config, board)
        runtime.async_add_window_listener(closed_windows.append)
        runtime.async_start()
        runtimes.append(runtime)
        return runtime

    yield start
    for runtime in runtimes:
        runtime.async_shutdown()


async def test_windows_close_at_absolute_times_from_start(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    """Windows follow each other from the start without drifting (R4, T20)."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    started = dt_util.utcnow()
    runtime = start_runtime(config_with())

    await advance(hass, freezer, timedelta(seconds=31))
    await advance(hass, freezer, timedelta(seconds=31))

    assert [(w.start, w.end) for w in closed_windows] == [
        (started, started + WINDOW),
        (started + WINDOW, started + 2 * WINDOW),
    ]
    assert runtime.latest_averages == closed_windows[-1]


async def test_power_sensor_state_feeds_the_averages(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    """The power sensor is read in W or kW (GEN-003, MAL-007)."""
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    start_runtime(config_with())

    await advance(hass, freezer, timedelta(seconds=10))
    hass.states.async_set(POWER_SENSOR, "5", {"unit_of_measurement": "kW"})
    await advance(hass, freezer, timedelta(seconds=20))

    averages = closed_windows[-1]
    assert averages.regulation_average_kw == pytest.approx((2 * 10 + 5 * 20) / 30)
    assert averages.sensor_valid


async def test_unavailable_power_sensor_makes_the_window_invalid(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    """An unavailable or removed sensor counts as no valid measurement (MAL-006)."""
    hass.states.async_set(POWER_SENSOR, "3000", {"unit_of_measurement": "W"})
    start_runtime(config_with())

    hass.states.async_set(POWER_SENSOR, "unavailable")
    await advance(hass, freezer, WINDOW)
    hass.states.async_remove(POWER_SENSOR)
    await advance(hass, freezer, WINDOW)

    first, second = closed_windows
    assert (first.regulation_average_kw, first.sensor_valid) == (3.0, False)
    assert (second.regulation_average_kw, second.sensor_valid) == (None, False)


async def test_windows_close_without_power_sensor(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    """Without a configured power sensor there are no averages (T2)."""
    start_runtime(config_with(power_sensor=None))

    await advance(hass, freezer, WINDOW)

    assert closed_windows[0].regulation_average_kw is None
    assert not closed_windows[0].sensor_valid


async def test_shutdown_stops_measuring_and_closing_windows(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    hass.states.async_set(POWER_SENSOR, "2000", {"unit_of_measurement": "W"})
    runtime = start_runtime(config_with())

    runtime.async_shutdown()
    hass.states.async_set(POWER_SENSOR, "4000", {"unit_of_measurement": "W"})
    await advance(hass, freezer, 3 * WINDOW)

    assert closed_windows == []


async def test_removed_listener_is_not_called(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, start_runtime, closed_windows
) -> None:
    runtime = start_runtime(config_with())
    calls: list[WindowAverages] = []
    remove = runtime.async_add_window_listener(calls.append)

    remove()
    await advance(hass, freezer, WINDOW)

    assert calls == []
    assert len(closed_windows) == 1
