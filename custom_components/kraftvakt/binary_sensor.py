"""Binary sensor that tells when the regulation is in the safe state."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import KraftvaktEntity
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the safe state sensor for the config entry."""
    async_add_entities([SafeStateBinarySensor(entry, entry.runtime_data)])


class SafeStateBinarySensor(KraftvaktEntity, BinarySensorEntity):
    """Is on while the regulation is in the safe state."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: KraftvaktConfigEntry, runtime: KraftvaktRuntime) -> None:
        """Create the sensor for the runtime."""
        super().__init__(entry, "safe_state")
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Update the sensor each time the status of the regulation may change."""
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return whether the regulation is in the safe state."""
        return self._runtime.safe_state
