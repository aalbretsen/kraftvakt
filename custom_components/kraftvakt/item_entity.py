"""Entities of the appliances and chargers, which follow the configuration."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import ClassVar

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .config_model import Appliance, Charger, KraftvaktConfig
from .const import DOMAIN
from .entity import KraftvaktEntity, item_name
from .runtime import KraftvaktConfigEntry
from .settings import Settings


def item_entity_key(kind: str, item_id: str, setting: str) -> str:
    return f"{kind}_{item_id}_{setting}"


class ItemEntity(KraftvaktEntity):
    """An entity for a setting of an appliance or a charger.

    It is named after the item when it is created, and updated each time the
    switches or the configuration in the settings change.
    """

    kind: ClassVar[str]
    settings: ClassVar[tuple[str, ...]]

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        settings: Settings,
        item_id: str,
        name: str,
        setting: str,
    ) -> None:
        super().__init__(
            entry,
            item_entity_key(self.kind, item_id, setting),
            f"{self.kind}_{setting}",
            f"{self.kind}_{slugify(name)}_{setting}",
        )
        self._attr_translation_placeholders = {self.kind: name}
        self._settings = settings
        self._runtime = entry.runtime_data
        self._item_id = item_id
        self._setting = setting

    async def async_added_to_hass(self) -> None:
        """Follow the switches and the configuration on the settings."""
        self.async_on_remove(
            self._settings.async_add_listener(self.async_write_ha_state)
        )

    @staticmethod
    @abstractmethod
    def items(config: KraftvaktConfig) -> Sequence[Appliance | Charger]:
        """Return the items in the configuration that have these entities."""


class ChargerEntity(ItemEntity):
    kind = "charger"

    @staticmethod
    def items(config: KraftvaktConfig) -> Sequence[Charger]:
        return config.chargers

    def _charger(self) -> Charger | None:
        """Return the charger, None for a moment after it was removed."""
        return next(
            (
                charger
                for charger in self._settings.config.chargers
                if charger.id == self._item_id
            ),
            None,
        )


@callback
def async_setup_item_entities(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    platform: str,
    entity_types: Sequence[type[ItemEntity]],
) -> None:
    """Add the entities of the configured items and follow the configuration.

    They follow the configuration without a reload of the config entry, which
    would start the regulation again. Registry entries of removed items are
    removed.
    """
    settings = entry.runtime_data.settings
    _remove_orphaned_item_entities(hass, entry, settings.config, platform, entity_types)
    for entity_type in entity_types:
        item_entities = ItemEntities(hass, entry, async_add_entities, entity_type)
        item_entities.async_follow_items()
        entry.async_on_unload(
            settings.async_add_listener(item_entities.async_follow_items)
        )


class ItemEntities:
    """Adds and removes the entities of one kind of item when the configuration changes.

    An item is an appliance or a charger.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: KraftvaktConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
        entity_type: type[ItemEntity],
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._settings = entry.runtime_data.settings
        self._async_add_entities = async_add_entities
        self._entity_type = entity_type
        self._added: dict[str, list[ItemEntity]] = {}

    @callback
    def async_follow_items(self) -> None:
        configured = {
            item.id: item for item in self._entity_type.items(self._settings.config)
        }
        for item_id in [key for key in self._added if key not in configured]:
            self._remove(self._added.pop(item_id))
        new_entities: list[ItemEntity] = []
        for item_id, item in configured.items():
            if item_id not in self._added:
                name = item_name(self._hass, item)
                self._added[item_id] = [
                    self._entity_type(
                        self._entry, self._settings, item_id, name, setting
                    )
                    for setting in self._entity_type.settings
                ]
                new_entities += self._added[item_id]
        if new_entities:
            self._async_add_entities(new_entities)

    def _remove(self, entities: list[ItemEntity]) -> None:
        registry = er.async_get(self._hass)
        for entity in entities:
            if entity.entity_id and registry.async_get(entity.entity_id):
                registry.async_remove(entity.entity_id)


def _remove_orphaned_item_entities(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    config: KraftvaktConfig,
    platform: str,
    entity_types: Sequence[type[ItemEntity]],
) -> None:
    wanted = {
        item_entity_key(entity_type.kind, item.id, setting)
        for entity_type in entity_types
        for item in entity_type.items(config)
        for setting in entity_type.settings
    }
    prefixes = tuple(f"{entity_type.kind}_" for entity_type in entity_types)
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            registry_entry.domain == platform
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id.startswith(prefixes)
            and registry_entry.unique_id not in wanted
        ):
            registry.async_remove(registry_entry.entity_id)
