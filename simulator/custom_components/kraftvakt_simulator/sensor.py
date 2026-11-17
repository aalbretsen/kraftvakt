"""Power sensors of the simulated devices, the house total of the HAN, and the temperature of a heating device."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from . import SimulatorConfigEntry, kind_of
from .const import DeviceKind
from .devices import Observable, SimulatedCharger, SimulatedDevice, SimulatedHeater, async_get_power_board
from .entity import SimulatorEntity
from .model import ChargerStatus


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

TEMPERATURE_KEYS: Final = {DeviceKind.HEATER: "temperature", DeviceKind.THERMOSTAT: "floor_temperature"}

CHARGER_STATUS: Final = SensorEntityDescription(
    key="status",
    translation_key="status",
    device_class=SensorDeviceClass.ENUM,
    options=[status.value for status in ChargerStatus],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the power sensor of the device, or the house total for the HAN."""
    kind = kind_of(entry)
    sensor_class = HousePowerSensor if kind is DeviceKind.HAN else PowerSensor
    sensors: list[SensorEntity] = [sensor_class(entry, entry.runtime_data, DESCRIPTIONS[kind])]
    if isinstance(entry.runtime_data, SimulatedCharger):
        sensors.append(ChargerStatusSensor(entry, entry.runtime_data, CHARGER_STATUS))
    if isinstance(entry.runtime_data, SimulatedHeater):
        sensors.append(TemperatureSensor(entry, entry.runtime_data, temperature_description(TEMPERATURE_KEYS[kind])))
    async_add_entities(sensors)


def temperature_description(translation_key: str) -> SensorEntityDescription:
    return SensorEntityDescription(
        key="temperature",
        translation_key=translation_key,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    )


class TemperatureSensor(SimulatorEntity[SimulatedHeater], SensorEntity):
    """The temperature of a heating device, as set by its setting."""

    @property
    def native_value(self) -> float:
        return self.device.temperature


class PowerSensor(SimulatorEntity[SimulatedDevice], SensorEntity):
    """The power the simulated device consumes."""

    @property
    def native_value(self) -> float:
        return self.device.power_w


class ChargerStatusSensor(SimulatorEntity[SimulatedCharger], SensorEntity):
    """The status of the simulated EV charger, unavailable while it is unplugged, as a charger without power is."""

    @property
    def available(self) -> bool:
        return not self.device.unplugged

    @property
    def native_value(self) -> str:
        return self.device.state.status.value


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
