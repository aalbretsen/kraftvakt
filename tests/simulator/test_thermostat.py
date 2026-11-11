"""Black box tests of the simulated thermostats."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.climate import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.kraftvakt_simulator.const import DeviceKind

from .conftest import AddDevice, advance, call, power, state

CLIMATE = "climate.living_room"
POWER = "sensor.living_room_power"
HOUSE_POWER = "sensor.han_power"
ROOM_TEMPERATURE = "number.living_room_room_temperature"


def attribute(hass: HomeAssistant, name: str) -> object:
    """Return an attribute of the thermostat."""
    found = hass.states.get(CLIMATE)
    assert found is not None
    return found.attributes[name]


async def test_thermostat_starts_off_and_consumes_nothing(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")

    assert state(hass, CLIMATE) == HVACMode.OFF
    assert attribute(hass, "hvac_modes") == ["off", "heat", "auto"]
    assert attribute(hass, "hvac_action") == HVACAction.OFF
    assert attribute(hass, "temperature") == 21
    assert power(hass, POWER) == 0


@pytest.mark.parametrize("mode", [HVACMode.HEAT, HVACMode.AUTO])
async def test_thermostat_follows_its_duty_cycle_in_a_heating_mode(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    add_device: AddDevice,
    mode: HVACMode,
) -> None:
    """750 W at 25 % of an hour: on 15 minutes, then off 45."""
    await add_device(DeviceKind.HAN, "HAN", background_w=1000)
    await add_device(DeviceKind.THERMOSTAT, "Living room")

    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=mode)

    assert state(hass, CLIMATE) == mode
    assert attribute(hass, "hvac_action") == HVACAction.HEATING
    assert power(hass, POWER) == 750
    assert power(hass, HOUSE_POWER) == 1750
    await advance(hass, freezer, timedelta(minutes=15))
    assert attribute(hass, "hvac_action") == HVACAction.IDLE
    assert power(hass, POWER) == 0


async def test_turning_off_stops_heating_and_on_returns_to_the_last_mode(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.AUTO)
    await advance(hass, freezer, timedelta(minutes=20))

    await call(hass, "climate", "turn_off", CLIMATE)
    assert state(hass, CLIMATE) == HVACMode.OFF
    assert power(hass, POWER) == 0

    await call(hass, "climate", "turn_on", CLIMATE)
    assert state(hass, CLIMATE) == HVACMode.AUTO
    assert power(hass, POWER) == 750


async def test_turning_on_the_first_time_heats(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")

    await call(hass, "climate", "turn_on", CLIMATE)

    assert state(hass, CLIMATE) == HVACMode.HEAT
    assert power(hass, POWER) == 750


async def test_changing_between_heating_modes_keeps_the_cycle(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.HEAT)
    await advance(hass, freezer, timedelta(minutes=20))

    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.AUTO)
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.AUTO)

    assert state(hass, CLIMATE) == HVACMode.AUTO
    assert power(hass, POWER) == 0


async def test_target_temperature_changes_without_changing_the_power(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")

    await call(hass, "climate", "set_temperature", CLIMATE, temperature=23.5)
    assert attribute(hass, "temperature") == 23.5
    assert power(hass, POWER) == 0

    await call(
        hass,
        "climate",
        "set_temperature",
        CLIMATE,
        temperature=19,
        hvac_mode=HVACMode.HEAT,
    )
    assert attribute(hass, "temperature") == 19
    assert state(hass, CLIMATE) == HVACMode.HEAT
    assert power(hass, POWER) == 750


async def test_thermostat_is_restored_with_the_cycle_in_its_on_part(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    mock_restore_cache(hass, [State(CLIMATE, HVACMode.AUTO, {"temperature": 18})])

    await add_device(DeviceKind.THERMOSTAT, "Living room")

    assert state(hass, CLIMATE) == HVACMode.AUTO
    assert attribute(hass, "temperature") == 18
    assert power(hass, POWER) == 750
    await advance(hass, freezer, timedelta(minutes=15))
    assert power(hass, POWER) == 0


async def test_thermostat_ignores_an_unknown_restored_state(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    mock_restore_cache(hass, [State(CLIMATE, "unavailable")])

    await add_device(DeviceKind.THERMOSTAT, "Living room")

    assert state(hass, CLIMATE) == HVACMode.OFF
    assert attribute(hass, "temperature") == 21


async def test_unplugged_thermostat_consumes_nothing(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room")
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.HEAT)

    await call(hass, "switch", "turn_on", "switch.living_room_unplugged")

    assert state(hass, CLIMATE) == HVACMode.HEAT
    assert attribute(hass, "hvac_action") == HVACAction.IDLE
    assert power(hass, POWER) == 0


async def test_non_heating_modes_consume_nothing(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(
        DeviceKind.THERMOSTAT, "Living room", hvac_modes=["off", "heat", "cool"]
    )

    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.COOL)

    assert state(hass, CLIMATE) == HVACMode.COOL
    assert attribute(hass, "hvac_action") == HVACAction.IDLE
    assert power(hass, POWER) == 0


async def test_thermostat_without_off_starts_in_its_first_mode(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    """It cannot be turned off, and turning on goes to its first heating mode."""
    await add_device(DeviceKind.THERMOSTAT, "Living room", hvac_modes=["cool", "auto"])

    assert state(hass, CLIMATE) == HVACMode.COOL
    assert attribute(hass, "hvac_modes") == ["cool", "auto"]
    assert attribute(hass, "supported_features") == (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON
    )
    await call(hass, "climate", "turn_on", CLIMATE)
    assert state(hass, CLIMATE) == HVACMode.AUTO
    assert power(hass, POWER) == 750


async def test_thermostat_that_starts_in_a_heating_mode_heats(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.THERMOSTAT, "Living room", hvac_modes=["heat"])

    assert state(hass, CLIMATE) == HVACMode.HEAT
    assert power(hass, POWER) == 750


async def test_thermostat_heats_only_below_the_target_temperature(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice
) -> None:
    """A target at or below the room temperature stops heating, above it heats."""
    entry = await add_device(DeviceKind.THERMOSTAT, "Living room")
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode=HVACMode.HEAT)
    assert attribute(hass, "current_temperature") == 5

    await call(hass, "climate", "set_temperature", CLIMATE, temperature=5)
    assert attribute(hass, "hvac_action") == HVACAction.IDLE
    assert power(hass, POWER) == 0

    await advance(hass, freezer, timedelta(minutes=20))
    await call(hass, "climate", "set_temperature", CLIMATE, temperature=22)
    assert power(hass, POWER) == 750

    await call(hass, "number", "set_value", ROOM_TEMPERATURE, value=22)
    assert attribute(hass, "current_temperature") == 22
    assert power(hass, POWER) == 0
    assert entry.data["room_temperature"] == 22
