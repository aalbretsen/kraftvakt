"""A diagnostics file downloaded from Kraftvakt in the test harness, with an EV charger filled in by hand.

The fixtures of the charger profile tests are here too, since the tests here run the drafted profile tests.
"""

import json
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.components.diagnostics import _get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN

from ..charger_profiles.conftest import Command, Device, DeviceEntity, command, register

__all__ = ["command"]

DRIVEWAY = Device(
    integration="example_charger",
    name="Driveway",
    manufacturer="Example",
    model_id="EX-1",
    entities=[
        DeviceEntity("switch", "Charging allowed", "charging_allowed"),
        DeviceEntity("number", "Charging current"),
        DeviceEntity("binary_sensor", "Car connected", "car_connected"),
        DeviceEntity("sensor", None),
        DeviceEntity("sensor", "Status", "status"),
        DeviceEntity("sensor", "Voltage", "voltage", disabled=True),
    ],
)


def driveway_charger(device_id: str) -> dict:
    return {
        "id": "c1",
        "device_id": device_id,
        "entity_id": "switch.driveway_charging_allowed",
        "activate": {"mode": "default"},
        "deactivate": {
            "mode": "custom",
            "action": [
                {"action": "example_charger.pause", "data": {"device_id": device_id}},
                {"action": "switch.turn_off", "target": {"entity_id": "switch.driveway_charging_allowed"}},
            ],
        },
        "set_current": {"mode": "entity", "entity_id": "number.driveway_charging_current"},
        "car_connected": {
            "type": "template",
            "value": "{{ is_state('binary_sensor.driveway_car_connected', 'on') or states('sensor.driveway_status') == 'charging' and is_state('sun.sun', 'above_horizon') }}",
        },
        "charging_power": {"type": "power_sensor", "value": "sensor.driveway"},
        "cloud_controlled": True,
    }


@pytest.fixture
async def diagnostics_file(hass: HomeAssistant, hass_client: ClientSessionGenerator, command: Command, tmp_path: Path) -> Path:
    """Return the file Download diagnostics gives, Home Assistant's wrapper included, with a charger on a device that has no profile."""
    assert await async_setup_component(hass, "diagnostics", {})
    device_id = register(hass, DRIVEWAY)
    hass.states.async_set("sensor.driveway_status", "charging", {"options": ["charging", "disconnected"]})
    config = {
        "general": {"power_sensor": "sensor.house_power"},
        "appliances": [{"id": "a1", "entity_id": "light.water_heater", "turn_on": {"mode": "default"}, "turn_off": {"mode": "default"}}],
        "charger_groups": [{"id": "g1", "name": "<b>Garage</b> & more", "one_at_a_time": True, "chargers": [driveway_charger(device_id)]}],
    }
    assert (await command("kraftvakt/config/save", config=config))["saved"]
    content = await _get_diagnostics_for_config_entry(hass, hass_client, hass.config_entries.async_entries(DOMAIN)[0])
    path = tmp_path / "kraftvakt-diagnostics.json"
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return path
