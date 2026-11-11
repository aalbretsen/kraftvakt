"""The climate entity of a simulated thermostat."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import SimulatorConfigEntry
from .const import MAX_TARGET_TEMPERATURE, MIN_TARGET_TEMPERATURE
from .devices import SimulatedThermostat
from .entity import SimulatorEntity

THERMOSTAT = EntityDescription(key="thermostat", name=None)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SimulatorConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the thermostat."""
    async_add_entities([SimulatorThermostat(entry, entry.runtime_data, THERMOSTAT)])


class SimulatorThermostat(
    SimulatorEntity[SimulatedThermostat], ClimateEntity, RestoreEntity
):
    """A thermostat with the HVAC modes chosen in the settings.

    It gets back its mode and target temperature after a restart. It can be
    turned off only when off is one of its modes.
    """

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = MIN_TARGET_TEMPERATURE
    _attr_max_temp = MAX_TARGET_TEMPERATURE

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the features, with turning off only when off is a mode."""
        features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_ON
        )
        if HVACMode.OFF in self.hvac_modes:
            features |= ClimateEntityFeature.TURN_OFF
        return features

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the modes chosen in the settings."""
        return self.device.hvac_modes

    @property
    def current_temperature(self) -> float:
        """Return the room temperature."""
        return self.device.room_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the mode."""
        return self.device.hvac_mode

    @property
    def hvac_action(self) -> HVACAction:
        """Return heating while the device draws power, idle while it waits."""
        if self.device.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        return HVACAction.HEATING if self.device.power_w > 0 else HVACAction.IDLE

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self.device.target_temperature

    async def async_added_to_hass(self) -> None:
        """Restore the mode and target temperature from before the restart."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return
        if (temperature := last_state.attributes.get(ATTR_TEMPERATURE)) is not None:
            self.device.async_set_target_temperature(temperature)
        if last_state.state in self.hvac_modes:
            self.device.async_set_hvac_mode(HVACMode(last_state.state))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Change the mode."""
        self.device.async_set_hvac_mode(hvac_mode)

    async def async_turn_on(self) -> None:
        """Return to the last mode the thermostat heated in."""
        self.device.async_turn_on()

    async def async_turn_off(self) -> None:
        """Turn the thermostat off."""
        self.device.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Change the target temperature, and the mode when it is given."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self.device.async_set_target_temperature(temperature)
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            self.device.async_set_hvac_mode(hvac_mode)
