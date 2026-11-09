"""Sensors for the regulation average and the capacity average."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import KraftvaktEntity
from .measurement import WindowAverages
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime


@dataclass(frozen=True, kw_only=True)
class AverageSensorDescription(SensorEntityDescription):
    """Describes a sensor that shows one of the averages in kW."""

    value_fn: Callable[[WindowAverages], float | None]
    device_class: SensorDeviceClass = SensorDeviceClass.POWER
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    native_unit_of_measurement: str = UnitOfPower.WATT
    suggested_unit_of_measurement: str = UnitOfPower.KILO_WATT
    suggested_display_precision: int = 2


AVERAGE_SENSORS: tuple[AverageSensorDescription, ...] = (
    AverageSensorDescription(
        key="regulation_average",
        value_fn=lambda averages: averages.regulation_average_w,
    ),
    AverageSensorDescription(
        key="capacity_average",
        value_fn=lambda averages: averages.capacity_average_w,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the average sensors for the config entry."""
    async_add_entities(
        AverageSensor(entry, entry.runtime_data, description)
        for description in AVERAGE_SENSORS
    )


class AverageSensor(KraftvaktEntity, SensorEntity):
    """Shows an average, updated each time a regulation window closes.

    The sensor is unavailable until there is an average to show.
    """

    entity_description: AverageSensorDescription

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        runtime: KraftvaktRuntime,
        description: AverageSensorDescription,
    ) -> None:
        """Create the sensor described by `description`."""
        super().__init__(entry, description.key)
        self.entity_description = description
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Update the sensor each time a window closes."""
        self.async_on_remove(
            self._runtime.async_add_window_listener(self._async_window_closed)
        )

    @property
    def native_value(self) -> float | None:
        """Return the average of the last closed window."""
        averages = self._runtime.latest_averages
        return None if averages is None else self.entity_description.value_fn(averages)

    @property
    def available(self) -> bool:
        """Return whether there is an average to show."""
        return self.native_value is not None

    @callback
    def _async_window_closed(self, _averages: WindowAverages) -> None:
        self.async_write_ha_state()
