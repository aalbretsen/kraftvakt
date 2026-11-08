"""Black box tests of the simulated heating devices."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.kraftvakt_simulator.const import DeviceKind

from .conftest import AddDevice, advance, call, power, state

SWITCH = "switch.heating_cable"
POWER = "sensor.heating_cable_power"


async def test_heater_starts_switched_off_and_consumes_nothing(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")

    assert state(hass, SWITCH) == STATE_OFF
    assert power(hass, POWER) == 0
    sensor = hass.states.get(POWER)
    assert sensor is not None
    assert sensor.attributes["device_class"] == "power"
    assert sensor.attributes["unit_of_measurement"] == "W"


async def test_heater_follows_its_duty_cycle_while_switched_on(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    """750 W at 25 % of an hour: off 45 minutes, then on 15, again and again."""
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)

    assert state(hass, SWITCH) == STATE_ON
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=44))
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=1))
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=15))
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=45))
    assert power(hass, POWER) == 750


async def test_switching_off_stops_heating_and_on_restarts_the_cycle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=50))
    assert power(hass, POWER) == 750

    await call(hass, "switch", "turn_off", SWITCH)
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=60))
    assert power(hass, POWER) == 0

    await call(hass, "switch", "turn_on", SWITCH)
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=45))
    assert power(hass, POWER) == 750


async def test_turning_on_a_heater_that_is_on_keeps_the_cycle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", SWITCH)
    await advance(hass, freezer, timedelta(minutes=50))

    await call(hass, "switch", "turn_on", SWITCH)

    assert power(hass, POWER) == 750


async def test_heater_with_full_duty_cycle_heats_at_once(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable", duty_cycle_pct=100)

    await call(hass, "switch", "turn_on", SWITCH)

    assert power(hass, POWER) == 750


async def test_heater_switch_is_restored_with_the_cycle_in_its_off_part(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    mock_restore_cache(hass, [State(SWITCH, STATE_ON)])

    await add_device(DeviceKind.HEATER, "Heating cable")

    assert state(hass, SWITCH) == STATE_ON
    assert power(hass, POWER) == 0
    await advance(hass, freezer, timedelta(minutes=45))
    assert power(hass, POWER) == 750


async def test_heater_switch_has_the_icon_of_its_type(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(
        DeviceKind.HEATER, "Water heater", heater_type="water_heater", power_w=2000
    )

    registry_entry = er.async_get(hass).async_get("switch.water_heater")
    assert registry_entry is not None
    assert registry_entry.translation_key == "water_heater"
    assert registry_entry.original_name is None
