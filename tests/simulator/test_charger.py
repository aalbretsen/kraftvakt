"""Black box tests of the simulated EV chargers."""

from typing import Any

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, State
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache_with_extra_data,
)

from custom_components.kraftvakt_simulator.const import DeviceKind
from custom_components.kraftvakt_simulator.model import three_phase_power_w

from .conftest import AddDevice, call, power, state

ALLOWED = "switch.charger_charging_allowed"
CONNECTED = "switch.charger_car_connected"
FULLY_CHARGED = "switch.charger_car_fully_charged"
UNPLUGGED = "switch.charger_unplugged"
CURRENT = "number.charger_charging_current"
CHARGING_POWER = "sensor.charger_charging_power"


def restored_current(value: float) -> dict[str, Any]:
    """Return the stored data of the current number from before a restart."""
    return {
        "native_value": value,
        "native_unit_of_measurement": "A",
        "native_min_value": 6,
        "native_max_value": 16,
        "native_step": 1,
    }


async def test_charger_starts_without_car_and_charging_not_allowed(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.CHARGER, "Charger")

    for switch in (ALLOWED, CONNECTED, FULLY_CHARGED, UNPLUGGED):
        assert state(hass, switch) == STATE_OFF
    assert float(state(hass, CURRENT)) == 6
    assert power(hass, CHARGING_POWER) == 0
    current = hass.states.get(CURRENT)
    assert current is not None
    assert current.attributes["min"] == 6
    assert current.attributes["max"] == 16
    assert current.attributes["step"] == 1
    assert current.attributes["unit_of_measurement"] == "A"


async def test_charger_draws_three_phase_power_for_a_charging_car(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.CHARGER, "Charger")

    await call(hass, "switch", "turn_on", ALLOWED)
    assert power(hass, CHARGING_POWER) == 0
    await call(hass, "switch", "turn_on", CONNECTED)
    assert power(hass, CHARGING_POWER) == pytest.approx(4156.9, abs=0.1)

    await call(hass, "number", "set_value", CURRENT, value=10)
    assert power(hass, CHARGING_POWER) == pytest.approx(three_phase_power_w(10))

    await call(hass, "switch", "turn_on", FULLY_CHARGED)
    assert power(hass, CHARGING_POWER) == 0
    await call(hass, "switch", "turn_off", FULLY_CHARGED)
    await call(hass, "switch", "turn_off", ALLOWED)
    assert power(hass, CHARGING_POWER) == 0


async def test_unplugged_charger_draws_nothing_for_a_charging_car(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.CHARGER, "Charger")
    await call(hass, "switch", "turn_on", ALLOWED)
    await call(hass, "switch", "turn_on", CONNECTED)

    await call(hass, "switch", "turn_on", UNPLUGGED)
    assert power(hass, CHARGING_POWER) == 0

    await call(hass, "switch", "turn_off", UNPLUGGED)
    assert power(hass, CHARGING_POWER) == pytest.approx(three_phase_power_w(6))


async def test_current_outside_the_charger_range_is_refused(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.CHARGER, "Charger")

    with pytest.raises(ServiceValidationError):
        await call(hass, "number", "set_value", CURRENT, value=20)

    assert float(state(hass, CURRENT)) == 6


async def test_charger_states_are_restored(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    mock_restore_cache_with_extra_data(
        hass,
        [
            (State(ALLOWED, STATE_ON), {}),
            (State(CONNECTED, STATE_ON), {}),
            (State(CURRENT, "12"), restored_current(12)),
            (State(UNPLUGGED, STATE_ON), {}),
        ],
    )

    await add_device(DeviceKind.CHARGER, "Charger")

    assert state(hass, ALLOWED) == STATE_ON
    assert state(hass, CONNECTED) == STATE_ON
    assert state(hass, FULLY_CHARGED) == STATE_OFF
    assert float(state(hass, CURRENT)) == 12
    assert state(hass, UNPLUGGED) == STATE_ON
    assert power(hass, CHARGING_POWER) == 0


async def test_restored_current_is_kept_within_a_changed_range(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    mock_restore_cache_with_extra_data(
        hass, [(State(CURRENT, "16"), restored_current(16))]
    )

    await add_device(DeviceKind.CHARGER, "Charger", max_current_a=10)

    assert float(state(hass, CURRENT)) == 10
