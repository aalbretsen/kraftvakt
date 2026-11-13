"""Number entity for the power limit, so automations can change it."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .config_model import POWER_LIMIT_MAX_W, POWER_LIMIT_W
from .entity import KraftvaktEntity
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the power limit for the config entry."""
    async_add_entities([PowerLimitNumber(entry, entry.runtime_data)])


class PowerLimitNumber(KraftvaktEntity, NumberEntity):
    """The stored power limit, the same as in the panel."""

    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = POWER_LIMIT_W.minimum
    _attr_native_max_value = POWER_LIMIT_MAX_W
    _attr_native_step = POWER_LIMIT_W.resolution
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: KraftvaktConfigEntry, runtime: KraftvaktRuntime) -> None:
        """Create the power limit for the runtime."""
        super().__init__(entry, "power_limit")
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Follow the power limit, also when it is saved from the panel."""
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> int:
        """Return the stored power limit."""
        return self._runtime.config.general.power_limit_w

    async def async_set_native_value(self, value: float) -> None:
        """Save the power limit, rounded to whole watts."""
        await self._runtime.async_set_power_limit(round(value))
