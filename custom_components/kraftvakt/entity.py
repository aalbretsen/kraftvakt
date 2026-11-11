"""Common base for the entities of Kraftvakt."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .config_model import Appliance, Charger
from .const import DOMAIN, NAME


class KraftvaktEntity(Entity):
    """An entity that belongs to the Kraftvakt service device.

    Settled with the owner: the entity id comes from `object_id`, not from
    the translated name, so it is the same in every language and groups the
    entities, like `sensor.kraftvakt_waiting_time_remaining`.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        key: str,
        translation_key: str | None = None,
        object_id: str | None = None,
    ) -> None:
        """Identify the entity by `key`, also its translation key and object id."""
        self._attr_unique_id = key
        self._attr_translation_key = translation_key or key
        self._object_id = object_id or key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def suggested_object_id(self) -> str:
        """Return the object id, prefixed with the device name by Home Assistant."""
        return self._object_id


def entity_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return the name of the entity in Home Assistant, or else its id."""
    if state := hass.states.get(entity_id):
        return state.name
    registry_entry = er.async_get(hass).async_get(entity_id)
    if registry_entry is None:
        return entity_id
    return registry_entry.name or registry_entry.original_name or entity_id


def charger_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return the name of a charger: its device's, or else its entity's.

    Settled with the owner: the entity that allows charging often has a name
    like «Garage Charging allowed».
    """
    registry_entry = er.async_get(hass).async_get(entity_id)
    if registry_entry is not None and registry_entry.device_id is not None:
        device = dr.async_get(hass).async_get(registry_entry.device_id)
        if device is not None and (name := device.name_by_user or device.name):
            return name
    return entity_name(hass, entity_id)


def item_name(hass: HomeAssistant, item: Appliance | Charger) -> str:
    """Return the name of an appliance or charger, its id until it has an entity."""
    if item.entity_id is None:
        return item.id
    if isinstance(item, Charger):
        return charger_name(hass, item.entity_id)
    return entity_name(hass, item.entity_id)
