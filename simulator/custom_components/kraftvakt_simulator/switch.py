"""Switches of the simulated heating devices and EV chargers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import SimulatorConfigEntry, kind_of
from .const import CONF_HEATER_TYPE, DeviceKind
from .devices import (
    PluggedInDevice,
    SimulatedCharger,
    SimulatedDevice,
    SimulatedHeater,
)
from .entity import SimulatorEntity


@dataclass(frozen=True, kw_only=True)
class SimulatorSwitchDescription[DeviceT: SimulatedDevice](SwitchEntityDescription):
    """How a switch reads and changes its device."""

    is_on_fn: Callable[[DeviceT], bool]
    set_fn: Callable[[DeviceT, bool], None]


def heater_switch(heater_type: str) -> SimulatorSwitchDescription[SimulatedHeater]:
    """Return the main switch of a heating device, with the icon of its type."""
    return SimulatorSwitchDescription(
        key="switch",
        translation_key=heater_type,
        name=None,
        is_on_fn=lambda heater: heater.is_on,
        set_fn=lambda heater, on: heater.async_set_on(on),
    )


UNPLUGGED_SWITCH: Final[SimulatorSwitchDescription[PluggedInDevice]] = (
    SimulatorSwitchDescription(
        key="unplugged",
        translation_key="unplugged",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda device: device.unplugged,
        set_fn=lambda device, unplugged: device.async_set_unplugged(unplugged),
    )
)

CHARGER_SWITCHES: Final[tuple[SimulatorSwitchDescription[SimulatedCharger], ...]] = (
    SimulatorSwitchDescription(
        key="charging_allowed",
        translation_key="charging_allowed",
        is_on_fn=lambda charger: charger.state.charging_allowed,
        set_fn=lambda charger, on: charger.async_set_charging_allowed(on),
    ),
    SimulatorSwitchDescription(
        key="car_connected",
        translation_key="car_connected",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda charger: charger.state.car_connected,
        set_fn=lambda charger, on: charger.async_set_car_connected(on),
    ),
    SimulatorSwitchDescription(
        key="car_fully_charged",
        translation_key="car_fully_charged",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda charger: charger.state.car_fully_charged,
        set_fn=lambda charger, on: charger.async_set_car_fully_charged(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the switches of a heating device or an EV charger."""
    if kind_of(entry) is DeviceKind.HEATER:
        descriptions = (heater_switch(entry.data[CONF_HEATER_TYPE]),)
    else:
        descriptions = CHARGER_SWITCHES
    async_add_entities(
        SimulatorSwitch(entry, entry.runtime_data, description)
        for description in (*descriptions, UNPLUGGED_SWITCH)
    )


class SimulatorSwitch(SimulatorEntity, SwitchEntity, RestoreEntity):
    """A switch of a simulated device. It gets back its state after a restart."""

    entity_description: SimulatorSwitchDescription

    @property
    def is_on(self) -> bool:
        """Return whether the switch is on."""
        return self.entity_description.is_on_fn(self.device)

    async def async_added_to_hass(self) -> None:
        """Restore the state from before the restart."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.entity_description.set_fn(self.device, last_state.state == STATE_ON)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.entity_description.set_fn(self.device, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self.entity_description.set_fn(self.device, False)
