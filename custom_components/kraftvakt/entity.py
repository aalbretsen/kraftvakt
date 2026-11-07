"""Common base for the entities of Kraftvakt."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME


class KraftvaktEntity(Entity):
    """An entity that belongs to the Kraftvakt service device (3.7)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        """Identify the entity by `key`, which is also its translation key."""
        self._attr_unique_id = key
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )
