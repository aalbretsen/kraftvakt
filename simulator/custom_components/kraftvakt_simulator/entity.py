"""Common base for the entities of the simulated devices."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from . import SimulatorConfigEntry
from .const import DOMAIN
from .devices import Observable, SimulatedDevice


class SimulatorEntity[DeviceT: SimulatedDevice](Entity):
    """An entity of a simulated device, updated when the device changes."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: SimulatorConfigEntry,
        device: DeviceT,
        description: EntityDescription,
    ) -> None:
        """Belong to the config entry's device, one per description key."""
        self.device = device
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Kraftvakt simulator",
        )

    @property
    def observed(self) -> Observable:
        """Return what the entity follows: its device, unless overridden."""
        return self.device

    async def async_added_to_hass(self) -> None:
        """Write the state each time the observed object changes."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.observed.async_add_listener(self.async_write_ha_state)
        )
