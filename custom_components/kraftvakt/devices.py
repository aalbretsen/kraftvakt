"""The devices of chargers, which every entity a charger uses belongs to."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .config_model import Issue, IssueLocation, KraftvaktConfig


def device_of_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Return the id of the device the entity belongs to, if any."""
    registry_entry = er.async_get(hass).async_get(entity_id)
    return None if registry_entry is None else registry_entry.device_id


def device_name(hass: HomeAssistant, device_id: str | None) -> str | None:
    """Return the name of the device, the user's name for it first."""
    if device_id is None:
        return None
    device = dr.async_get(hass).async_get(device_id)
    return None if device is None else device.name_by_user or device.name


def device_issues(hass: HomeAssistant, config: KraftvaktConfig) -> list[Issue]:
    """Return devices that do not exist and entities outside their charger's device."""
    devices = dr.async_get(hass)
    issues = []
    for charger in config.chargers:
        if charger.device_id is None:
            continue
        location = IssueLocation("chargers", charger.id)
        if devices.async_get(charger.device_id) is None:
            issues.append(location.issue("unknown_device", "device_id"))
            continue
        issues += [
            location.issue("entity_not_on_device", field_name)
            for field_name, entity_id in charger.device_entities()
            if device_of_entity(hass, entity_id) != charger.device_id
        ]
    return issues
