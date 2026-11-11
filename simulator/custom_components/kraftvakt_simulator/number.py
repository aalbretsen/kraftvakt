"""Numbers of the simulated devices: settings that can change while HA runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Final

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SimulatorConfigEntry, kind_of
from .const import MAX_BACKGROUND_W, MAX_HEATER_POWER_W, MAX_PERIOD_MIN, DeviceKind
from .devices import SimulatedCharger, SimulatedDevice, SimulatedHan, SimulatedHeater
from .entity import SimulatorEntity


@dataclass(frozen=True, kw_only=True)
class SimulatorNumberDescription[DeviceT: SimulatedDevice](NumberEntityDescription):
    """A setting of a device, kept in its config entry, so reconfiguring changes it."""

    value_fn: Callable[[DeviceT], float]
    set_fn: Callable[[DeviceT, float], None]
    entity_category: EntityCategory | None = EntityCategory.CONFIG
    mode: NumberMode = NumberMode.BOX


BACKGROUND_POWER: Final[SimulatorNumberDescription[SimulatedHan]] = (
    SimulatorNumberDescription(
        key="background_power",
        translation_key="background_power",
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=MAX_BACKGROUND_W,
        native_step=100,
        value_fn=lambda han: han.background_w,
        set_fn=lambda han, value: han.async_set_background(value),
    )
)

HEATER_NUMBERS: Final[tuple[SimulatorNumberDescription[SimulatedHeater], ...]] = (
    SimulatorNumberDescription(
        key="heating_power",
        translation_key="heating_power",
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=1,
        native_max_value=MAX_HEATER_POWER_W,
        native_step=1,
        value_fn=lambda heater: heater.cycle.power_w,
        set_fn=lambda heater, value: heater.async_set_power(value),
    ),
    SimulatorNumberDescription(
        key="duty_cycle",
        translation_key="duty_cycle",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        value_fn=lambda heater: heater.cycle.duty_cycle_pct,
        set_fn=lambda heater, value: heater.async_set_duty_cycle(value),
    ),
    SimulatorNumberDescription(
        key="period",
        translation_key="period",
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=1,
        native_max_value=MAX_PERIOD_MIN,
        native_step=1,
        value_fn=lambda heater: heater.cycle.period // timedelta(minutes=1),
        set_fn=lambda heater, value: heater.async_set_period(value),
    ),
)


def charging_current(charger: SimulatedCharger) -> NumberEntityDescription:
    """Return the description of the charging current, within the charger's range."""
    return NumberEntityDescription(
        key="charging_current",
        translation_key="charging_current",
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=charger.min_current_a,
        native_max_value=charger.max_current_a,
        native_step=1,
        mode=NumberMode.SLIDER,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the settings of the HAN or a heating device, or a charger's current."""
    device = entry.runtime_data
    match kind_of(entry):
        case DeviceKind.HAN:
            descriptions: tuple[SimulatorNumberDescription, ...] = (BACKGROUND_POWER,)
        case DeviceKind.HEATER | DeviceKind.THERMOSTAT:
            descriptions = HEATER_NUMBERS
        case DeviceKind.CHARGER:
            async_add_entities(
                [ChargingCurrentNumber(entry, device, charging_current(device))]
            )
            return
    async_add_entities(
        SettingNumber(entry, device, description) for description in descriptions
    )


class SettingNumber(SimulatorEntity, NumberEntity):
    """A setting of a simulated device, changeable while Home Assistant runs."""

    entity_description: SimulatorNumberDescription

    @property
    def native_value(self) -> float:
        """Return the value of the setting."""
        return self.entity_description.value_fn(self.device)

    async def async_set_native_value(self, value: float) -> None:
        """Change the setting."""
        self.entity_description.set_fn(self.device, value)


class ChargingCurrentNumber(SimulatorEntity[SimulatedCharger], RestoreNumber):
    """The charging current. It gets back its value after a restart."""

    @property
    def native_value(self) -> float:
        """Return the charging current in A."""
        return self.device.state.current_a

    async def async_added_to_hass(self) -> None:
        """Restore the current from before the restart."""
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last is not None and last.native_value is not None:
            self.device.async_set_current(last.native_value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the charging current."""
        self.device.async_set_current(value)
