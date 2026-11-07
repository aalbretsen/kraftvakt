"""Switches for the regulation (ENT-006) and for each charger (ENT-003, ENT-004)."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .charger_switches import ChargerSwitchBoard
from .const import DOMAIN
from .entity import KraftvaktEntity, item_name
from .runtime import ConfigIncompleteError, KraftvaktConfigEntry, KraftvaktRuntime

_LOGGER = logging.getLogger(__name__)

CHARGER_SETTINGS: Final = ("excluded", "window_override")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the regulation switch and the switches of the configured chargers.

    The charger switches follow the configuration: they are added and removed
    when the chargers change, without reloading the config entry (B9, R5).
    """
    runtime = entry.runtime_data
    async_add_entities([RegulationSwitch(entry, runtime)])
    board = runtime.charger_switches
    added: dict[str, list[ChargerSwitch]] = {}

    @callback
    def async_follow_chargers() -> None:
        configured = {charger.id: charger for charger in board.config.charging.chargers}
        registry = er.async_get(hass)
        for charger_id in [key for key in added if key not in configured]:
            for entity in added.pop(charger_id):
                if entity.entity_id and registry.async_get(entity.entity_id):
                    registry.async_remove(entity.entity_id)
        new_entities: list[ChargerSwitch] = []
        for charger_id, charger in configured.items():
            if charger_id not in added:
                name = item_name(hass, charger)
                added[charger_id] = [
                    ChargerSwitch(entry, board, charger_id, name, setting)
                    for setting in CHARGER_SETTINGS
                ]
                new_entities += added[charger_id]
        if new_entities:
            async_add_entities(new_entities)

    _remove_orphaned_charger_switches(hass, entry, board)
    async_follow_chargers()
    entry.async_on_unload(board.async_add_listener(async_follow_chargers))


def _remove_orphaned_charger_switches(
    hass: HomeAssistant, entry: KraftvaktConfigEntry, board: ChargerSwitchBoard
) -> None:
    """Remove registry entries for switches of chargers no longer configured (R5)."""
    wanted = {
        charger_switch_key(charger.id, setting)
        for charger in board.config.charging.chargers
        for setting in CHARGER_SETTINGS
    }
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            registry_entry.domain == "switch"
            and registry_entry.platform == DOMAIN
            and registry_entry.unique_id.startswith("charger_")
            and registry_entry.unique_id not in wanted
        ):
            registry.async_remove(registry_entry.entity_id)


def charger_switch_key(charger_id: str, setting: str) -> str:
    """Return the unique id of a charger switch."""
    return f"charger_{charger_id}_{setting}"


class RegulationSwitch(KraftvaktEntity, SwitchEntity):
    """Is on while the regulation runs, and starts and stops it (REG-016).

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


class ChargerSwitch(KraftvaktEntity, SwitchEntity):
    """A user's switch for a charger, kept over any restart (GEN-011).

    `excluded` takes the charger out of the regulation (ENT-003), and
    `window_override` lets it charge outside its charging window (ENT-004). The
    regulation reads the switch at its next decision (REG-005). The switch is
    unavailable while charging is disabled, but keeps its position (T10). It is
    named after the charger when it is created (LAD-003).
    """

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        board: ChargerSwitchBoard,
        charger_id: str,
        charger_name: str,
        setting: str,
    ) -> None:
        """Create the switch for the setting of the charger."""
        super().__init__(
            entry, charger_switch_key(charger_id, setting), f"charger_{setting}"
        )
        self._attr_translation_placeholders = {"charger": charger_name}
        self._board = board
        self._charger_id = charger_id
        self._setting = setting

    async def async_added_to_hass(self) -> None:
        """Follow the switches and the configuration on the board."""
        self.async_on_remove(self._board.async_add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        """Return whether charging is enabled (T10)."""
        return self._board.config.charging.enabled

    @property
    def is_on(self) -> bool:
        """Return the position of the switch."""
        return getattr(self._board.switches(self._charger_id), self._setting)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on and save at once."""
        await self._board.async_set(self._charger_id, **{self._setting: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off and save at once."""
        await self._board.async_set(self._charger_id, **{self._setting: False})
