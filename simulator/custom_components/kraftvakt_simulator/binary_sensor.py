"""Whether a simulated EV charger is charging."""

from __future__ import annotations

from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SimulatorConfigEntry
from .devices import SimulatedCharger
from .entity import SimulatorEntity, device_of

CHARGING: Final = BinarySensorEntityDescription(
    key="charging",
    translation_key="charging",
    device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the charging sensor of the EV charger."""
    device = device_of(entry, SimulatedCharger)
    async_add_entities([ChargingSensor(entry, device, CHARGING)])


class ChargingSensor(SimulatorEntity[SimulatedCharger], BinarySensorEntity):
    """On while the EV charger draws power."""

    @property
    def is_on(self) -> bool:
        """Return whether the EV charger charges the car."""
        return self.device.power_w > 0
