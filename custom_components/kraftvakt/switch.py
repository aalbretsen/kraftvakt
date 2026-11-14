"""The regulation switch, and the user's switches for appliances and chargers."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .config_model import Appliance, ItemSwitches, KraftvaktConfig
from .const import DOMAIN
from .entity import KraftvaktEntity
from .item_entity import ChargerEntity, ItemEntity, async_setup_item_entities
from .runtime import ConfigIncompleteError, KraftvaktConfigEntry, KraftvaktRuntime

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([RegulationSwitch(entry, entry.runtime_data)])
    async_setup_item_entities(
        hass,
        entry,
        async_add_entities,
        "switch",
        (ApplianceSwitch, ChargerSwitch, ChargerConfigSwitch),
    )


class RegulationSwitch(KraftvaktEntity, SwitchEntity):
    """Is on while the regulation runs, and starts and stops it.

    The switch has no stored state: the regulation runs after every start of
    Home Assistant or the integration when the configuration is complete.
    """

    def __init__(self, entry: KraftvaktConfigEntry, runtime: KraftvaktRuntime) -> None:
        super().__init__(entry, "regulation")
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Follow the regulation, also when it is started or stopped elsewhere."""
        self.async_on_remove(self._runtime.async_add_status_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        return self._runtime.running

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start the regulation; it cannot start with an incomplete configuration."""
        try:
            self._runtime.async_start_regulation()
        except ConfigIncompleteError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="config_incomplete",
                translation_placeholders={"count": str(len(err.missing))},
            ) from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._runtime.async_stop_regulation()


class ItemSwitch(ItemEntity, SwitchEntity):
    """A user's switch for an appliance or a charger, kept over any restart."""

    @property
    def is_on(self) -> bool:
        return bool(getattr(self._positions(), self._setting))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch on and save at once."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch off and save at once."""
        await self._async_set(False)

    @abstractmethod
    def _positions(self) -> ItemSwitches:
        """Return the positions of the switches of the item."""

    @abstractmethod
    async def _async_set(self, position: bool) -> None:
        """Set the position of this switch and save it at once."""


class ApplianceSwitch(ItemSwitch):
    kind = "appliance"
    settings = ("excluded",)

    @staticmethod
    def items(config: KraftvaktConfig) -> Sequence[Appliance]:
        return config.appliances

    def _positions(self) -> ItemSwitches:
        return self._settings.appliance_switches(self._item_id)

    async def _async_set(self, position: bool) -> None:
        await self._settings.async_set_appliance(self._item_id, **{self._setting: position})


class ChargerSwitch(ItemSwitch, ChargerEntity):
    settings = ("excluded", "window_override")

    def _positions(self) -> ItemSwitches:
        return self._settings.charger_switches(self._item_id)

    async def _async_set(self, position: bool) -> None:
        await self._settings.async_set_charger(self._item_id, **{self._setting: position})


class ChargerConfigSwitch(ChargerEntity, SwitchEntity):
    """A setting of a charger in the configuration, also shown in the panel."""

    settings = ("finish_after_window",)

    @property
    def is_on(self) -> bool | None:
        """Return the stored setting, None just after the charger was removed."""
        charger = self._charger()
        return None if charger is None else getattr(charger, self._setting)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Save the setting on, also while the regulation runs."""
        await self._runtime.async_set_finish_after_window(self._item_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Save the setting off, also while the regulation runs."""
        await self._runtime.async_set_finish_after_window(self._item_id, False)
