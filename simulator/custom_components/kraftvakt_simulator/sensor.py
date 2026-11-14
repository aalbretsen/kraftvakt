"""Power sensors of the simulated devices and the house total of the HAN."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from . import SimulatorConfigEntry, kind_of
from .const import DeviceKind
from .devices import Observable, SimulatedDevice, async_get_power_board
from .entity import SimulatorEntity


def power_description(key: str) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
    )


DESCRIPTIONS: Final = {
    DeviceKind.HAN: power_description("house_power"),
    DeviceKind.HEATER: power_description("power"),
    DeviceKind.THERMOSTAT: power_description("power"),
    DeviceKind.CHARGER: power_description("charging_power"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the power sensor of the device, or the house total for the HAN."""
    kind = kind_of(entry)
    sensor_class = HousePowerSensor if kind is DeviceKind.HAN else PowerSensor
    async_add_entities([sensor_class(entry, entry.runtime_data, DESCRIPTIONS[kind])])


class PowerSensor(SimulatorEntity[SimulatedDevice], SensorEntity):
    """The power the simulated device consumes."""

    @property
    def native_value(self) -> float:
        return self.device.power_w


class HousePowerSensor(SimulatorEntity[SimulatedDevice], SensorEntity):
    """The power of the whole house: background plus every simulated device.

    It reports every 10 seconds also when the power has not changed, as a HAN
    reader does, so Kraftvakt's power sensor timeout does not run out.
    """

    async def async_added_to_hass(self) -> None:
        """Report at a fixed interval as well as on every change."""
        await super().async_added_to_hass()
        self.async_on_remove(async_track_time_interval(self.hass, self._async_report, timedelta(seconds=10)))

    @callback
    def _async_report(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def observed(self) -> Observable:
        """Follow the power board, which changes with every device."""
        return async_get_power_board(self.hass)

    @property
    def native_value(self) -> float:
        return async_get_power_board(self.hass).total_w
