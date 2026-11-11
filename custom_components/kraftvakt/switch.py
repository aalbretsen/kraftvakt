"""The regulation switch, and the user's switches for appliances and chargers."""

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Sequence
from typing import Any, ClassVar

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .config_model import Appliance, Charger, ItemSwitches, KraftvaktConfig
from .const import DOMAIN
from .entity import KraftvaktEntity, item_name
from .runtime import ConfigIncompleteError, KraftvaktConfigEntry, KraftvaktRuntime
from .switch_board import SwitchBoard

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the regulation switch and the switches of the configured items.

    The switches of the appliances and chargers follow the configuration
    without a reload of the config entry, which would start the regulation
    again.
    """
    runtime = entry.runtime_data
    async_add_entities([RegulationSwitch(entry, runtime)])
    board = runtime.switch_board
    _remove_orphaned_item_switches(hass, entry, board.config)
    for switch_type in ITEM_SWITCH_TYPES:
        item_switches = ItemSwitchEntities(hass, entry, async_add_entities, switch_type)
        item_switches.async_follow_items()
        entry.async_on_unload(
            board.async_add_listener(item_switches.async_follow_items)
        )


class ItemSwitchEntities:
    """Adds and removes the switches of one kind of item when the configuration changes.

    An item is an appliance or a charger.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: KraftvaktConfigEntry,
        async_add_entities: AddConfigEntryEntitiesCallback,
        switch_type: type[ItemSwitch],
    ) -> None:
        """Create the switches of `switch_type` for the items on the board."""
        self._hass = hass
        self._entry = entry
        self._board = entry.runtime_data.switch_board
        self._async_add_entities = async_add_entities
        self._switch_type = switch_type
        self._added: dict[str, list[ItemSwitch]] = {}

    @callback
    def async_follow_items(self) -> None:
        """Remove the switches of removed items and add those of new ones."""
        configured = {
            item.id: item for item in self._switch_type.items(self._board.config)
        }
        for item_id in [key for key in self._added if key not in configured]:
            self._remove(self._added.pop(item_id))
        new_entities: list[ItemSwitch] = []
        for item_id, item in configured.items():
            if item_id not in self._added:
                name = item_name(self._hass, item)
                self._added[item_id] = [
                    self._switch_type(self._entry, self._board, item_id, name, setting)
                    for setting in self._switch_type.settings
                ]
                new_entities += self._added[item_id]
        if new_entities:
            self._async_add_entities(new_entities)

    def _remove(self, entities: list[ItemSwitch]) -> None:
        registry = er.async_get(self._hass)
        for entity in entities:
            if entity.entity_id and registry.async_get(entity.entity_id):
                registry.async_remove(entity.entity_id)


def _remove_orphaned_item_switches(
    hass: HomeAssistant, entry: KraftvaktConfigEntry, config: KraftvaktConfig
) -> None:
    wanted = {
        item_switch_key(switch_type.kind, item.id, setting)
        for switch_type in ITEM_SWITCH_TYPES
        for item in switch_type.items(config)
        for setting in switch_type.settings
    }
    prefixes = tuple(f"{switch_type.kind}_" for switch_type in ITEM_SWITCH_TYPES)
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            registry_entry.domain == "switch"
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id.startswith(prefixes)
            and registry_entry.unique_id not in wanted
        ):
            registry.async_remove(registry_entry.entity_id)


def item_switch_key(kind: str, item_id: str, setting: str) -> str:
    """Return the unique id of the switch of an appliance or charger."""
    return f"{kind}_{item_id}_{setting}"


class RegulationSwitch(KraftvaktEntity, SwitchEntity):
    """Is on while the regulation runs, and starts and stops it.

    The switch has no stored state: the regulation runs after every start of
    Home Assistant or the integration when the configuration is complete.
    """

    def __init__(self, entry: KraftvaktConfigEntry, runtime: KraftvaktRuntime) -> None:
        """Create the switch for the runtime."""
        super().__init__(entry, "regulation")
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Follow the regulation, also when it is started or stopped elsewhere."""
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return whether the regulation runs."""
        return self._runtime.running

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the regulation, or log why it cannot start and stay off."""
        try:
            self._runtime.async_start_regulation()
        except ConfigIncompleteError as err:
            _LOGGER.warning("The regulation cannot start. %s", err)
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the regulation."""
        self._runtime.async_stop_regulation()


class ItemSwitch(KraftvaktEntity, SwitchEntity):
    """A user's switch for an appliance or a charger, kept over any restart.

    It is named after the item when it is created.
    """

    kind: ClassVar[str]
    settings: ClassVar[tuple[str, ...]]

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        board: SwitchBoard,
        item_id: str,
        name: str,
        setting: str,
    ) -> None:
        """Create the switch for the setting of the item."""
        super().__init__(
            entry,
            item_switch_key(self.kind, item_id, setting),
            f"{self.kind}_{setting}",
            f"{self.kind}_{slugify(name)}_{setting}",
        )
        self._attr_translation_placeholders = {self.kind: name}
        self._board = board
        self._item_id = item_id
        self._setting = setting

    async def async_added_to_hass(self) -> None:
        """Follow the switches and the configuration on the board."""
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        """Return the position of the switch."""
        return getattr(self._positions(), self._setting)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on and save at once."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off and save at once."""
        await self._async_set(False)

    @staticmethod
    @abstractmethod
    def items(config: KraftvaktConfig) -> Sequence[Appliance | Charger]:
        """Return the items in the configuration that have these switches."""

    @abstractmethod
    def _positions(self) -> ItemSwitches:
        """Return the positions of the switches of the item."""

    @abstractmethod
    async def _async_set(self, position: bool) -> None:
        """Set the position of this switch and save it at once."""


class ApplianceSwitch(ItemSwitch):
    """A user's switch for an appliance."""

    kind = "appliance"
    settings = ("excluded",)

    @staticmethod
    def items(config: KraftvaktConfig) -> Sequence[Appliance]:
        """Return the appliances in the configuration."""
        return config.appliances

    def _positions(self) -> ItemSwitches:
        return self._board.appliance_switches(self._item_id)

    async def _async_set(self, position: bool) -> None:
        await self._board.async_set_appliance(
            self._item_id, **{self._setting: position}
        )


class ChargerSwitch(ItemSwitch):
    """A user's switch for a charger, unavailable while charging is disabled."""

    kind = "charger"
    settings = ("excluded", "window_override")

    @staticmethod
    def items(config: KraftvaktConfig) -> Sequence[Charger]:
        """Return the chargers in the configuration."""
        return config.charging.chargers

    @property
    def available(self) -> bool:
        """Return whether charging is enabled."""
        return self._board.config.charging.enabled

    def _positions(self) -> ItemSwitches:
        return self._board.charger_switches(self._item_id)

    async def _async_set(self, position: bool) -> None:
        await self._board.async_set_charger(self._item_id, **{self._setting: position})


ITEM_SWITCH_TYPES: tuple[type[ItemSwitch], ...] = (ApplianceSwitch, ChargerSwitch)
