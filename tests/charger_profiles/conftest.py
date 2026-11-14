"""Devices as integrations register them, and the panel's commands for charger profiles."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.kraftvakt.const import DOMAIN


@dataclass(frozen=True)
class DeviceEntity:
    """An entity as its integration registers it. The name is the integration's own, None for the main entity of the device."""

    domain: str
    name: str | None
    translation_key: str | None = None
    disabled: bool = False


@dataclass(frozen=True)
class Device:
    integration: str
    name: str
    entities: Sequence[DeviceEntity]
    manufacturer: str | None = None
    model_id: str | None = None


def register(hass: HomeAssistant, device: Device) -> str:
    """Register the device and its entities, with entity IDs from the device name and the entity names, and return the device ID."""
    config_entry = MockConfigEntry(domain=device.integration)
    config_entry.add_to_hass(hass)
    device_entry = dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(device.integration, device.name)},
        name=device.name,
        manufacturer=device.manufacturer,
        model_id=device.model_id,
    )
    for index, entity in enumerate(device.entities):
        er.async_get(hass).async_get_or_create(
            entity.domain,
            device.integration,
            f"{device.name}_{index}",
            config_entry=config_entry,
            device_id=device_entry.id,
            suggested_object_id=slugify(" ".join(filter(None, (device.name, entity.name)))),
            has_entity_name=True,
            original_name=entity.name,
            translation_key=entity.translation_key,
            disabled_by=er.RegistryEntryDisabler.INTEGRATION if entity.disabled else None,
        )
    return device_entry.id


type Command = Callable[..., Awaitable[dict[str, Any]]]


@pytest.fixture
async def command(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> Command:
    """Set up Kraftvakt without a configuration, so the regulation is stopped, and return a function that sends a command and gives its result."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    client = await hass_ws_client(hass)

    async def send(message_type: str, **data: Any) -> dict[str, Any]:
        await client.send_json_auto_id({"type": message_type, **data})
        response = await client.receive_json()
        assert response["success"], response
        return response["result"]

    return send


async def charger_profile(command: Command, device_id: str) -> dict[str, Any]:
    return await command("kraftvakt/charger_profile/get", device_id=device_id)


async def save_charger(command: Command, device_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Save a configuration with one charger made from the fields, and return the result."""
    charger = {"id": "c1", "device_id": device_id, **fields}
    config = {
        "general": {"power_sensor": "sensor.house_power"},
        "charger_groups": [{"id": "g1", "name": "EV chargers", "one_at_a_time": True, "chargers": [charger]}],
    }
    return await command("kraftvakt/config/save", config=config)
