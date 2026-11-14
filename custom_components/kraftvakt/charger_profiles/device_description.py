"""What the device of a charger offers, as a profile for it would be written from it."""

from __future__ import annotations

from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .recognition import charger_profile_fields, device_integrations

# Only the attributes that tell what an entity's values are. Others may hold serial numbers, keys or names of people.
DESCRIBING_ATTRIBUTES: Final = frozenset({"device_class", "unit_of_measurement", "state_class", "options", "min", "max", "step", "mode"})


def device_description(hass: HomeAssistant, device_id: str) -> dict[str, Any] | None:
    """Return the device's integrations, manufacturer and model, its entities as they are registered with their values, the services of its integrations and its profile.

    Identifiers and unique IDs are left out, since they often hold serial numbers.
    """
    device = dr.async_get(hass).async_get(device_id)
    if not isinstance(device, dr.DeviceEntry):
        return None
    integrations = sorted(device_integrations(hass, device))
    profile, _ = charger_profile_fields(hass, device_id)
    return {
        "profile": None if profile is None else profile.name,
        "integrations": integrations,
        "manufacturer": device.manufacturer,
        "model": device.model,
        "model_id": device.model_id,
        "hw_version": device.hw_version,
        "sw_version": device.sw_version,
        "entities": [_entity(hass, entry) for entry in er.async_entries_for_device(er.async_get(hass), device_id, include_disabled_entities=True)],
        "services": {integration: sorted(hass.services.async_services_for_domain(integration)) for integration in integrations},
    }


def _entity(hass: HomeAssistant, entry: er.RegistryEntry) -> dict[str, Any]:
    state = hass.states.get(entry.entity_id)
    return {
        "entity_id": entry.entity_id,
        "platform": entry.platform,
        "translation_key": entry.translation_key,
        "original_name": entry.original_name,
        "has_entity_name": entry.has_entity_name,
        "original_device_class": entry.original_device_class,
        "entity_category": entry.entity_category,
        "disabled_by": entry.disabled_by,
        "state": None if state is None else state.state,
        "attributes": {} if state is None else {name: value for name, value in state.attributes.items() if name in DESCRIBING_ATTRIBUTES},
    }
