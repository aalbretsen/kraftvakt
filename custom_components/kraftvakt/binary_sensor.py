"""Binary sensors for the safe state and the penalty period."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import KraftvaktEntity
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime


@dataclass(frozen=True, kw_only=True)
class RegulationBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a binary sensor that shows a state of the regulation."""

    is_on_fn: Callable[[KraftvaktRuntime], bool]
    device_class: BinarySensorDeviceClass = BinarySensorDeviceClass.PROBLEM


BINARY_SENSORS: tuple[RegulationBinarySensorDescription, ...] = (
    RegulationBinarySensorDescription(
        key="safe_state",
        is_on_fn=lambda runtime: runtime.safe_state,
    ),
    RegulationBinarySensorDescription(
        key="penalty",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda runtime: runtime.penalty.active,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the binary sensors for the config entry."""
    async_add_entities(
        RegulationBinarySensor(entry, entry.runtime_data, description)
        for description in BINARY_SENSORS
    )


class RegulationBinarySensor(KraftvaktEntity, BinarySensorEntity):
    """Is on while the regulation is in the described state."""

    entity_description: RegulationBinarySensorDescription

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        runtime: KraftvaktRuntime,
        description: RegulationBinarySensorDescription,
    ) -> None:
        """Create the sensor described by `description`."""
        super().__init__(entry, description.key)
        self.entity_description = description
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Update the sensor each time the status of the regulation may change."""
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return whether the regulation is in the state."""
        return self.entity_description.is_on_fn(self._runtime)
