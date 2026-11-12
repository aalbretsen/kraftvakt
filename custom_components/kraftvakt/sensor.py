"""Sensors for the averages and the diagnostics of the regulation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import KraftvaktEntity
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime


@dataclass(frozen=True, kw_only=True)
class RegulationSensorDescription(SensorEntityDescription):
    """Describes a sensor that shows a value of the regulation."""

    value_fn: Callable[[KraftvaktRuntime], float | None]


@dataclass(frozen=True, kw_only=True)
class PowerSensorDescription(RegulationSensorDescription):
    """Describes a sensor that shows a power in W."""

    device_class: SensorDeviceClass = SensorDeviceClass.POWER
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    native_unit_of_measurement: str = UnitOfPower.WATT
    suggested_display_precision: int = 0


def _regulation_average_w(runtime: KraftvaktRuntime) -> float | None:
    averages = runtime.latest_averages
    return None if averages is None else averages.regulation_average_w


def _capacity_average_w(runtime: KraftvaktRuntime) -> float | None:
    averages = runtime.latest_averages
    return None if averages is None else averages.capacity_average_w


def _power_free_w(runtime: KraftvaktRuntime) -> float | None:
    average_w = _regulation_average_w(runtime)
    return None if average_w is None else runtime.power_limit_w - average_w


def _overconsumption_wh(runtime: KraftvaktRuntime) -> float:
    penalty = runtime.penalty
    return penalty.overconsumption_wh if penalty.overconsuming else 0.0


def _waiting_time_remaining_s(runtime: KraftvaktRuntime) -> int:
    """Return the seconds until the decision that ends the waiting time, or 0.

    It counts to the decision, since the slot is turned on at the first
    decision after the waiting time.
    """
    ends_at = runtime.waiting_ends_at
    if ends_at is None:
        return 0
    return max(0, round((ends_at - dt_util.utcnow()).total_seconds()))


def _waiting_time_next_turn_on_s(runtime: KraftvaktRuntime) -> float | None:
    waiting_time = runtime.curve_waiting_time
    return None if waiting_time is None else waiting_time.total_seconds()


@dataclass(frozen=True, kw_only=True)
class DurationSensorDescription(RegulationSensorDescription):
    """Describes a diagnostic sensor that shows a duration in seconds."""

    entity_category: EntityCategory = EntityCategory.DIAGNOSTIC
    device_class: SensorDeviceClass = SensorDeviceClass.DURATION
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    native_unit_of_measurement: str = UnitOfTime.SECONDS
    suggested_display_precision: int = 0


SENSORS: tuple[RegulationSensorDescription, ...] = (
    PowerSensorDescription(
        key="power_regulation_average", value_fn=_regulation_average_w
    ),
    PowerSensorDescription(key="power_hourly_average", value_fn=_capacity_average_w),
    PowerSensorDescription(
        key="power_free",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_power_free_w,
    ),
    RegulationSensorDescription(
        key="penalty_overconsumption",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        value_fn=_overconsumption_wh,
    ),
    RegulationSensorDescription(
        key="regulation_steps_on",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda runtime: runtime.slots_on,
    ),
    DurationSensorDescription(
        key="waiting_time_remaining", value_fn=_waiting_time_remaining_s
    ),
    DurationSensorDescription(
        key="waiting_time_next_turn_on", value_fn=_waiting_time_next_turn_on_s
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors for the config entry."""
    async_add_entities(
        RegulationSensor(entry, entry.runtime_data, description)
        for description in SENSORS
    )


class RegulationSensor(KraftvaktEntity, SensorEntity):
    """Shows a value of the regulation."""

    entity_description: RegulationSensorDescription

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        runtime: KraftvaktRuntime,
        description: RegulationSensorDescription,
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
    def native_value(self) -> float | None:
        """Return the value of the regulation."""
        return self.entity_description.value_fn(self._runtime)

    @property
    def available(self) -> bool:
        """Return whether there is a value to show."""
        return self.native_value is not None
