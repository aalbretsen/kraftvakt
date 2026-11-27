"""Black box tests of the average sensors."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
INTERVAL = timedelta(seconds=10)
WINDOW = 6 * INTERVAL


@pytest.fixture
def stored_general(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a configuration with a power sensor that reports every 10 seconds and windows of six updates; tests may change it first."""
    general = {"power_sensor": POWER_SENSOR, "regulation_window_s": int(WINDOW.total_seconds())}
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": {"general": general},
    }
    return general


@pytest.fixture
async def setup_kraftvakt(hass: HomeAssistant, stored_general: dict[str, Any]):
    async def setup() -> MockConfigEntry:
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry

    return setup


def set_power(hass: HomeAssistant, value: str, unit: str | None = "W") -> None:
    attributes = {ATTR_UNIT_OF_MEASUREMENT: unit} if unit else {}
    hass.states.async_set(POWER_SENSOR, value, attributes)


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta) -> None:
    """Move time on, with the power sensor reporting as a HAN reader does."""
    freezer.tick(delta)
    if state := hass.states.get(POWER_SENSOR):
        hass.states.async_set(POWER_SENSOR, state.state, state.attributes)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def report(hass: HomeAssistant, freezer: FrozenDateTimeFactory, value: str, unit: str | None = "W", count: int = 1) -> None:
    """Let the power sensor report the value `count` times, one interval apart."""
    for _ in range(count):
        freezer.tick(INTERVAL)
        set_power(hass, value, unit)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta) -> None:
    """Move time on without reports from the power sensor, a second at a time, so the windows close by the clock as they would."""
    for _ in range(int(delta.total_seconds())):
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


def entity_id(hass: HomeAssistant, key: str) -> str:
    found = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, key)
    assert found is not None
    return found


def state_of(hass: HomeAssistant, key: str) -> str:
    state = hass.states.get(entity_id(hass, key))
    assert state is not None
    return state.state


async def test_sensors_are_unavailable_before_the_first_average(hass: HomeAssistant, setup_kraftvakt) -> None:
    """There is no average before the first window has closed."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE
    assert state_of(hass, "power_tariff_average") == STATE_UNAVAILABLE


async def test_sensors_show_the_averages_in_w(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    """Both averages are power sensors in W."""
    set_power(hass, "1000")
    await setup_kraftvakt()

    await report(hass, freezer, "2000")
    await report(hass, freezer, "6", unit="kW", count=5)

    for key in ("power_regulation_average", "power_tariff_average"):
        state = hass.states.get(entity_id(hass, key))
        assert state is not None
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "W"
        assert state.attributes[ATTR_DEVICE_CLASS] == "power"
        assert state.attributes["state_class"] == "measurement"
    assert float(state_of(hass, "power_regulation_average")) == pytest.approx((2000 * 10 + 6000 * 50) / 60)
    assert float(state_of(hass, "power_tariff_average")) == pytest.approx((2000 * 3550 + 6000 * 50) / 3600)


async def test_sensors_belong_to_the_service_device(hass: HomeAssistant, setup_kraftvakt) -> None:
    entry = await setup_kraftvakt()

    device = dr.async_get(hass).async_get_device_by_identifier((DOMAIN, entry.entry_id), entry.entry_id)
    assert device is not None
    assert device.name == "Kraftvakt"
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    for key in ("power_regulation_average", "power_tariff_average"):
        registry_entry = er.async_get(hass).async_get(entity_id(hass, key))
        assert registry_entry is not None
        assert registry_entry.device_id == device.id
        assert registry_entry.translation_key == key


async def test_sensors_are_updated_once_per_window(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    """The sensors change only when a window closes."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await report(hass, freezer, "2000", count=9)

    await report(hass, freezer, "8000", count=2)
    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(2000)

    await report(hass, freezer, "8000")
    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(5000)


async def test_tariff_average_over_a_whole_hour_of_updates(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    """The tariff average is right through the whole hour when the sensor
    updates every 10 seconds."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    for step in range(360):
        await report(hass, freezer, "4000" if step % 2 else "2000")

    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(3000)
    assert float(state_of(hass, "power_tariff_average")) == pytest.approx(3000)


async def test_sensors_follow_an_outage_of_the_power_sensor(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    """One invalid close keeps the last value, two make the sensors unavailable,
    and when a valid value comes the last valid value fills the gap."""
    set_power(hass, "3000")
    await setup_kraftvakt()
    await report(hass, freezer, "3000", count=6)

    await report(hass, freezer, "unavailable", unit=None)
    await tick(hass, freezer, WINDOW)
    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(3000)

    await tick(hass, freezer, WINDOW)
    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE
    assert state_of(hass, "power_tariff_average") == STATE_UNAVAILABLE

    await tick(hass, freezer, timedelta(seconds=30))
    await report(hass, freezer, "1500", count=12)
    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(1500)
    assert float(state_of(hass, "power_tariff_average")) == pytest.approx((3000 * 3520 + 1500 * 80) / 3600)


async def test_power_sensor_without_unit_is_read_as_watt(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    set_power(hass, "2500", unit=None)
    await setup_kraftvakt()

    await report(hass, freezer, "2500", unit=None, count=6)

    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(2500)


async def test_sensors_are_unavailable_without_power_sensor(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    stored_general: dict[str, Any],
    setup_kraftvakt,
) -> None:
    """An incomplete configuration gives no averages."""
    stored_general["power_sensor"] = None
    await setup_kraftvakt()

    await advance(hass, freezer, 3 * WINDOW)

    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE


async def test_number_of_updates_comes_from_the_configuration(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    stored_general: dict[str, Any],
    setup_kraftvakt,
) -> None:
    stored_general["regulation_window_s"] = 20
    set_power(hass, "1000")
    await setup_kraftvakt()

    await report(hass, freezer, "1000")
    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE
    await report(hass, freezer, "1000")

    assert float(state_of(hass, "power_regulation_average")) == pytest.approx(1000)


async def test_sensor_names_are_translated(hass: HomeAssistant, setup_kraftvakt) -> None:
    """Norwegian names come from the translation files."""
    hass.config.language = "nb"
    await setup_kraftvakt()

    names = {key: hass.states.get(entity_id(hass, key)).attributes[ATTR_FRIENDLY_NAME] for key in ("power_regulation_average", "power_tariff_average")}
    assert names == {
        "power_regulation_average": "Kraftvakt Effekt reguleringssnitt",
        "power_tariff_average": "Kraftvakt Effekt tariffsnitt",
    }


async def test_unload_stops_the_sensors(hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt) -> None:
    set_power(hass, "2000")
    entry = await setup_kraftvakt()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await advance(hass, freezer, WINDOW)

    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE


async def test_power_sensor_that_stops_reporting_makes_the_averages_unknown(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    stored_general: dict[str, Any],
    setup_kraftvakt,
) -> None:
    """A report of an unchanged value counts, and makes the sensor valid again."""
    stored_general["power_sensor_timeout_s"] = 90
    set_power(hass, "2000")
    await setup_kraftvakt()

    await tick(hass, freezer, timedelta(seconds=90))
    assert state_of(hass, "power_regulation_average") == "2000.0"
    await tick(hass, freezer, 2 * WINDOW)
    assert state_of(hass, "power_regulation_average") == STATE_UNAVAILABLE

    await report(hass, freezer, "2000", count=6)
    assert state_of(hass, "power_regulation_average") == "2000.0"
