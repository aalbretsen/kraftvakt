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
WINDOW = timedelta(seconds=60)


@pytest.fixture
def stored_general(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a configuration with a power sensor; tests may change it first."""
    general = {"power_sensor": POWER_SENSOR, "regulation_window_s": 60}
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


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta
) -> None:
    freezer.tick(delta)
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


async def test_sensors_are_unavailable_before_the_first_average(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    """There is no average before the first window has closed."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    assert state_of(hass, "regulation_average") == STATE_UNAVAILABLE
    assert state_of(hass, "capacity_average") == STATE_UNAVAILABLE


async def test_sensors_show_the_averages_in_w(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    """Both averages are power sensors in kW."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    await advance(hass, freezer, timedelta(seconds=15))
    set_power(hass, "6", unit="kW")
    await advance(hass, freezer, timedelta(seconds=45))

    for key in ("regulation_average", "capacity_average"):
        state = hass.states.get(entity_id(hass, key))
        assert state is not None
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "kW"
        assert state.attributes[ATTR_DEVICE_CLASS] == "power"
        assert state.attributes["state_class"] == "measurement"
    assert float(state_of(hass, "regulation_average")) == pytest.approx(5.0)
    assert float(state_of(hass, "capacity_average")) == pytest.approx(
        (2.0 * 3555 + 6.0 * 45) / 3600
    )


async def test_sensors_belong_to_the_service_device(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    entry = await setup_kraftvakt()

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, entry.entry_id), entry.entry_id
    )
    assert device is not None
    assert device.name == "Kraftvakt"
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    for key in ("regulation_average", "capacity_average"):
        registry_entry = er.async_get(hass).async_get(entity_id(hass, key))
        assert registry_entry is not None
        assert registry_entry.device_id == device.id
        assert registry_entry.translation_key == key


async def test_sensors_are_updated_once_per_window(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    """The sensors change only when a window closes."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer, WINDOW)
    await advance(hass, freezer, timedelta(seconds=30))

    set_power(hass, "8000")
    await advance(hass, freezer, timedelta(seconds=15))
    assert float(state_of(hass, "regulation_average")) == pytest.approx(2.0)

    await advance(hass, freezer, timedelta(seconds=15))
    assert float(state_of(hass, "regulation_average")) == pytest.approx(5.0)


async def test_capacity_average_over_a_whole_hour_of_updates(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    """The capacity average is right through the whole hour when the sensor
    updates every 10 seconds."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    for step in range(1, 360):
        await advance(hass, freezer, timedelta(seconds=10))
        set_power(hass, "4000" if step % 2 else "2000")
    await advance(hass, freezer, timedelta(seconds=10))

    assert float(state_of(hass, "regulation_average")) == pytest.approx(3.0)
    assert float(state_of(hass, "capacity_average")) == pytest.approx(3.0)


async def test_sensors_follow_an_outage_of_the_power_sensor(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    """One invalid close keeps the last value, two make the sensors unavailable,
    and when a valid value comes the last valid value fills the gap."""
    set_power(hass, "3000")
    await setup_kraftvakt()
    await advance(hass, freezer, WINDOW)

    set_power(hass, "unavailable")
    await advance(hass, freezer, WINDOW)
    assert float(state_of(hass, "regulation_average")) == pytest.approx(3.0)

    await advance(hass, freezer, WINDOW)
    assert state_of(hass, "regulation_average") == STATE_UNAVAILABLE
    assert state_of(hass, "capacity_average") == STATE_UNAVAILABLE

    await advance(hass, freezer, timedelta(seconds=40))
    set_power(hass, "1500")
    await advance(hass, freezer, timedelta(seconds=20))
    assert float(state_of(hass, "regulation_average")) == pytest.approx(
        (3.0 * 40 + 1.5 * 20) / 60
    )
    assert float(state_of(hass, "capacity_average")) == pytest.approx(
        (3.0 * 3580 + 1.5 * 20) / 3600
    )


async def test_power_sensor_without_unit_is_read_as_watt(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    """A power sensor without unit reports watt."""
    set_power(hass, "2500", unit=None)
    await setup_kraftvakt()

    await advance(hass, freezer, WINDOW)

    assert float(state_of(hass, "regulation_average")) == pytest.approx(2.5)


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

    assert state_of(hass, "regulation_average") == STATE_UNAVAILABLE


async def test_window_length_comes_from_the_configuration(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    stored_general: dict[str, Any],
    setup_kraftvakt,
) -> None:
    """The regulation window is the configured one."""
    stored_general["regulation_window_s"] = 20
    set_power(hass, "1000")
    await setup_kraftvakt()

    await advance(hass, freezer, timedelta(seconds=20))

    assert float(state_of(hass, "regulation_average")) == pytest.approx(1.0)


async def test_sensor_names_are_translated(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    """Norwegian names come from the translation files."""
    hass.config.language = "nb"
    await setup_kraftvakt()

    names = {
        key: hass.states.get(entity_id(hass, key)).attributes[ATTR_FRIENDLY_NAME]
        for key in ("regulation_average", "capacity_average")
    }
    assert names == {
        "regulation_average": "Kraftvakt Reguleringssnitt",
        "capacity_average": "Kraftvakt Snittforbruk",
    }


async def test_unload_stops_the_sensors(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    entry = await setup_kraftvakt()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await advance(hass, freezer, WINDOW)

    assert state_of(hass, "regulation_average") == STATE_UNAVAILABLE
