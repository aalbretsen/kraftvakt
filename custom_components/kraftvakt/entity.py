"""Common base for the entities of Kraftvakt."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .config_model import Appliance, Charger
from .const import DOMAIN, NAME


class KraftvaktEntity(Entity):
    """An entity that belongs to the Kraftvakt service device."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, entry: ConfigEntry, key: str, translation_key: str | None = None
    ) -> None:
        """Identify the entity by `key`, also its translation key unless given."""
        self._attr_unique_id = key
        self._attr_translation_key = translation_key or key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )


def entity_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return the name of the entity in Home Assistant.

    Falls back to the name in the entity registry when the entity has no state,
    and to the entity id when it is not known at all.
    """
    if state := hass.states.get(entity_id):
        return state.name
    registry_entry = er.async_get(hass).async_get(entity_id)
    if registry_entry is None:
        return entity_id
    return registry_entry.name or registry_entry.original_name or entity_id


def item_name(hass: HomeAssistant, item: Appliance | Charger) -> str:
    """Return the name of an appliance or charger, its id until it has an entity."""
    if item.entity_id is None:
        return item.id
    return entity_name(hass, item.entity_id)
