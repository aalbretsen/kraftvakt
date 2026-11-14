"""Black box tests of the simulated heating devices."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_OFF, STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.kraftvakt_simulator.const import DeviceKind

from .conftest import AddDevice, advance, call, power, state

SWITCH = "switch.heating_cable"
UNPLUGGED = "switch.heating_cable_unplugged"
POWER = "sensor.heating_cable_power"
HOUSE_POWER = "sensor.han_power"


async def test_heater_starts_switched_off_and_consumes_nothing(hass: HomeAssistant, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")

    assert state(hass, SWITCH) == STATE_OFF
    assert state(hass, UNPLUGGED) == STATE_OFF
    assert power(hass, POWER) == 0
    sensor = hass.states.get(POWER)
    assert sensor is not None
    assert sensor.attributes["device_class"] == "power"
    assert sensor.attributes["unit_of_measurement"] == "W"


async def test_heater_follows_its_duty_cycle_while_switched_on(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    """750 W at 25 % of an hour: on 15 minutes, then off 45, again and again."""
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)

    assert state(hass, SWITCH) == STATE_ON
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=14))
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=1))
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=45))
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=15))
    assert power(hass, POWER) == 0


async def test_switching_off_stops_heating_and_on_restarts_the_cycle(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=10))
    assert power(hass, POWER) == 750

    await call(hass, "switch", "turn_off", SWITCH)
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=60))
    assert power(hass, POWER) == 0

    await call(hass, "switch", "turn_on", SWITCH)
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=15))
    assert power(hass, POWER) == 0


async def test_turning_on_a_heater_that_is_on_keeps_the_cycle(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=50))

    await call(hass, "switch", "turn_on", SWITCH)

    assert power(hass, POWER) == 0


async def test_heater_with_full_duty_cycle_heats_at_once(hass: HomeAssistant, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable", duty_cycle_pct=100)

    await call(hass, "switch", "turn_on", SWITCH)

    assert power(hass, POWER) == 750


async def test_heater_switch_is_restored_with_the_cycle_in_its_on_part(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    mock_restore_cache(hass, [State(SWITCH, STATE_ON)])

    await add_device(DeviceKind.HEATER, "Heating cable")

    assert state(hass, SWITCH) == STATE_ON
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=15))
    assert power(hass, POWER) == 0


async def test_heater_switch_has_the_icon_of_its_type(hass: HomeAssistant, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Water heater", heater_type="water_heater", power_w=2000)

    registry_entry = er.async_get(hass).async_get("switch.water_heater")
    assert registry_entry is not None
    assert registry_entry.translation_key == "water_heater"
    assert registry_entry.original_name is None


async def test_unplugged_heater_consumes_nothing_while_its_cycle_runs_on(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HAN, "HAN", background_w=1000)
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=10))
    assert power(hass, HOUSE_POWER) == 1750

    await call(hass, "switch", "turn_on", UNPLUGGED)
    assert power(hass, POWER) == 0
    assert power(hass, HOUSE_POWER) == 1000
    await advance(hass, freezer, timedelta(minutes=60))
    assert power(hass, POWER) == 0

    await call(hass, "switch", "turn_off", UNPLUGGED)
    assert state(hass, SWITCH) == STATE_ON
    assert power(hass, POWER) == 750
    assert power(hass, HOUSE_POWER) == 1750


async def test_cycle_can_be_changed_and_restarts_in_its_on_part(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    """2000 W at 50 % of 10 minutes: on 5 minutes, then off 5."""
    entry = await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=50))
    assert power(hass, POWER) == 0

    await call(hass, "number", "set_value", "number.heating_cable_period", value=10)
    assert power(hass, POWER) == 750
    await call(hass, "number", "set_value", "number.heating_cable_duty_cycle", value=50)
    await call(hass, "number", "set_value", "number.heating_cable_heating_power", value=2000)
    await advance(hass, freezer, timedelta(minutes=4))
    assert power(hass, POWER) == 2000
    await advance(hass, freezer, timedelta(minutes=1))
    assert power(hass, POWER) == 0

    assert entry.data["power_w"] == 2000
    assert entry.data["duty_cycle_pct"] == 50
    assert entry.data["period_min"] == 10
    assert state(hass, "number.heating_cable_period") == "10"


async def test_unchanged_cycle_keeps_running(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=50))

    await call(hass, "number", "set_value", "number.heating_cable_period", value=60)

    assert power(hass, POWER) == 0


async def test_changing_the_cycle_of_a_switched_off_heater_keeps_it_off(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")

    await call(hass, "number", "set_value", "number.heating_cable_duty_cycle", value=100)

    assert state(hass, SWITCH) == STATE_OFF
    assert power(hass, POWER) == 0


@pytest.mark.parametrize(
    ("kind", "title", "entity_ids"),
    [
        (DeviceKind.HAN, "HAN", ["number.han_background_power"]),
        (
            DeviceKind.HEATER,
            "Heating cable",
            [
                "number.heating_cable_heating_power",
                "number.heating_cable_duty_cycle",
                "number.heating_cable_period",
                UNPLUGGED,
            ],
        ),
        (
            DeviceKind.THERMOSTAT,
            "Thermostat",
            [
                "number.thermostat_heating_power",
                "number.thermostat_duty_cycle",
                "number.thermostat_period",
                "number.thermostat_room_temperature",
                "switch.thermostat_unplugged",
            ],
        ),
        (
            DeviceKind.CHARGER,
            "Charger",
            [
                "switch.charger_car_connected",
                "switch.charger_car_fully_charged",
                "switch.charger_unplugged",
            ],
        ),
    ],
)
async def test_simulation_controls_are_in_the_configuration_category(
    hass: HomeAssistant,
    add_device: AddDevice,
    kind: DeviceKind,
    title: str,
    entity_ids: list[str],
) -> None:
    """The device's own controls stay main controls."""
    entry = await add_device(kind, title)

    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        expected = EntityCategory.CONFIG if registry_entry.entity_id in entity_ids else None
        assert registry_entry.entity_category is expected, registry_entry.entity_id
