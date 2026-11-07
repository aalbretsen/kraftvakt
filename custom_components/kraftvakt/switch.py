"""Switch that starts and stops the regulation (ENT-006)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import KraftvaktEntity
from .runtime import ConfigIncompleteError, KraftvaktConfigEntry, KraftvaktRuntime

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the regulation switch for the config entry."""
    async_add_entities([RegulationSwitch(entry, entry.runtime_data)])


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
