"""Kraftvakt simulator: simulated HAN, heating devices, thermostats and EV chargers.

Only for testing Kraftvakt against a local Home Assistant. It is not part of
the Kraftvakt integration that users install.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import timedelta
from functools import partial
from typing import Any, Final

from homeassistant.components.climate import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_BACKGROUND_W,
    CONF_DUTY_CYCLE_PCT,
    CONF_HVAC_MODES,
    CONF_KIND,
    CONF_MAX_CURRENT_A,
    CONF_MIN_CURRENT_A,
    CONF_PERIOD_MIN,
    CONF_POWER_W,
    CONF_ROOM_TEMPERATURE,
    DeviceKind,
)
from .devices import (
    SimulatedCharger,
    SimulatedDevice,
    SimulatedHan,
    SimulatedHeater,
    SimulatedThermostat,
)
from .model import DutyCycle

type SimulatorConfigEntry = ConfigEntry[SimulatedDevice]

PLATFORMS: Final = {
    DeviceKind.HAN: [Platform.NUMBER, Platform.SENSOR],
    DeviceKind.HEATER: [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH],
    DeviceKind.THERMOSTAT: [
        Platform.CLIMATE,
        Platform.NUMBER,
        Platform.SENSOR,
        Platform.SWITCH,
    ],
    DeviceKind.CHARGER: [
        Platform.BINARY_SENSOR,
        Platform.NUMBER,
        Platform.SENSOR,
        Platform.SWITCH,
    ],
}


async def async_setup_entry(hass: HomeAssistant, entry: SimulatorConfigEntry) -> bool:
    """Set up one simulated device."""
    device = create_device(hass, entry)
    entry.runtime_data = device
    device.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, platforms_of(entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SimulatorConfigEntry) -> bool:
    """Unload one simulated device. It then consumes nothing."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, platforms_of(entry)
    )
    if unloaded:
        entry.runtime_data.async_stop()
    return unloaded


def kind_of(entry: ConfigEntry) -> DeviceKind:
    """Return which kind of device the config entry simulates."""
    return DeviceKind(entry.data[CONF_KIND])


def platforms_of(entry: ConfigEntry) -> list[Platform]:
    """Return the platforms with entities for the config entry's device."""
    return PLATFORMS[kind_of(entry)]


@callback
def create_device(hass: HomeAssistant, entry: ConfigEntry) -> SimulatedDevice:
    """Create the simulated device from the config entry's settings."""
    data = entry.data
    store_setting = partial(_store_setting, hass, entry)
    match kind_of(entry):
        case DeviceKind.HAN:
            return SimulatedHan(
                hass, entry.entry_id, data[CONF_BACKGROUND_W], store_setting
            )
        case DeviceKind.HEATER:
            return SimulatedHeater(
                hass, entry.entry_id, _duty_cycle(data), store_setting
            )
        case DeviceKind.THERMOSTAT:
            return SimulatedThermostat(
                hass,
                entry.entry_id,
                _duty_cycle(data),
                store_setting,
                [HVACMode(mode) for mode in data[CONF_HVAC_MODES]],
                data[CONF_ROOM_TEMPERATURE],
            )
        case DeviceKind.CHARGER:
            return SimulatedCharger(
                hass,
                entry.entry_id,
                data[CONF_MIN_CURRENT_A],
                data[CONF_MAX_CURRENT_A],
            )


def _duty_cycle(data: Mapping[str, Any]) -> DutyCycle:
    return DutyCycle(
        power_w=data[CONF_POWER_W],
        duty_cycle_pct=data[CONF_DUTY_CYCLE_PCT],
        period=timedelta(minutes=data[CONF_PERIOD_MIN]),
    )


def _store_setting(
    hass: HomeAssistant, entry: ConfigEntry, key: str, value: float
) -> None:
    hass.config_entries.async_update_entry(entry, data={**entry.data, key: value})
