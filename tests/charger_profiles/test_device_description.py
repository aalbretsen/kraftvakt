"""The diagnostics describe the device of each charger, so a charger profile can be written from them."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_mock_service
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN

from .conftest import Command, Device, DeviceEntity, register, save_charger
from .profiles.test_easee import EASEE


async def test_diagnostics_describe_the_device_of_each_charger(hass: HomeAssistant, hass_client: ClientSessionGenerator, command: Command) -> None:
    assert await async_setup_component(hass, "diagnostics", {})
    async_mock_service(hass, "easee", "set_charger_access")
    easee = Device(
        integration=EASEE.integration,
        name="Garage",
        manufacturer="Easee",
        model_id="Easee Home",
        entities=[DeviceEntity("sensor", "Status", "easee_status"), DeviceEntity("sensor", "Voltage", "voltage", disabled=True)],
    )
    device_id = register(hass, easee)
    hass.states.async_set("sensor.garage_status", "charging", {"options": ["charging", "disconnected"], "site_key": "secret", "friendly_name": "Garage Status"})
    await save_charger(command, device_id, {"entity_id": "sensor.garage_status"})
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert diagnostics["charger_devices"] == {
        "c1": {
            "profile": "Easee",
            "integrations": ["easee"],
            "manufacturer": "Easee",
            "model": None,
            "model_id": "Easee Home",
            "hw_version": None,
            "sw_version": None,
            "entities": [
                {
                    "entity_id": "sensor.garage_status",
                    "platform": "easee",
                    "translation_key": "easee_status",
                    "original_name": "Status",
                    "has_entity_name": True,
                    "original_device_class": None,
                    "entity_category": None,
                    "disabled_by": None,
                    "state": "charging",
                    "attributes": {"options": ["charging", "disconnected"]},
                },
                {
                    "entity_id": "sensor.garage_voltage",
                    "platform": "easee",
                    "translation_key": "voltage",
                    "original_name": "Voltage",
                    "has_entity_name": True,
                    "original_device_class": None,
                    "entity_category": None,
                    "disabled_by": "integration",
                    "state": None,
                    "attributes": {},
                },
            ],
            "services": {"easee": ["set_charger_access"]},
        }
    }


async def test_diagnostics_tell_when_the_device_of_a_charger_is_gone(hass: HomeAssistant, hass_client: ClientSessionGenerator, command: Command) -> None:
    assert await async_setup_component(hass, "diagnostics", {})
    device_id = register(hass, EASEE)
    await save_charger(command, device_id, {})
    dr.async_get(hass).async_remove_device(device_id)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, hass.config_entries.async_entries(DOMAIN)[0])

    assert diagnostics["charger_devices"] == {"c1": None}
