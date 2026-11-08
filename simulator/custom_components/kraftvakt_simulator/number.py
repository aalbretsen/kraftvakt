"""The HAN's background power and the EV charger's charging current."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SimulatorConfigEntry, kind_of
from .const import MAX_BACKGROUND_W, DeviceKind
from .devices import SimulatedCharger, SimulatedHan
from .entity import SimulatorEntity

BACKGROUND_POWER = NumberEntityDescription(
    key="background_power",
    translation_key="background_power",
    device_class=NumberDeviceClass.POWER,
    native_unit_of_measurement=UnitOfPower.WATT,
    native_min_value=0,
    native_max_value=MAX_BACKGROUND_W,
    native_step=100,
    mode=NumberMode.BOX,
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
    """Add the background power of the HAN or the current of an EV charger."""
    device = entry.runtime_data
    if kind_of(entry) is DeviceKind.HAN:
        async_add_entities([BackgroundPowerNumber(entry, device, BACKGROUND_POWER)])
    else:
        async_add_entities(
            [ChargingCurrentNumber(entry, device, charging_current(device))]
        )


class BackgroundPowerNumber(SimulatorEntity[SimulatedHan], NumberEntity):
    """The background power of the house, changeable while Home Assistant runs.

    The value is kept in the config entry, so reconfiguring the HAN changes it.
    """

    @property
    def native_value(self) -> float:
        """Return the background power in W."""
        return self.device.background_w

    async def async_set_native_value(self, value: float) -> None:
        """Change the background power."""
        self.device.async_set_background(value)


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
