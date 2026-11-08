"""Kraftvakt simulator: simulated HAN, heating devices and EV chargers.

Only for testing Kraftvakt against a local Home Assistant. It is not part of
the Kraftvakt integration that users install.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_BACKGROUND_W,
    CONF_DUTY_CYCLE_PCT,
    CONF_KIND,
    CONF_MAX_CURRENT_A,
    CONF_MIN_CURRENT_A,
    CONF_PERIOD_MIN,
    CONF_POWER_W,
    DeviceKind,
)
from .devices import SimulatedCharger, SimulatedDevice, SimulatedHan, SimulatedHeater
from .model import DutyCycle

type SimulatorConfigEntry = ConfigEntry[SimulatedDevice]

PLATFORMS: Final = {
    DeviceKind.HAN: [Platform.NUMBER, Platform.SENSOR],
    DeviceKind.HEATER: [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH],
    DeviceKind.CHARGER: [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH],
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

    def store_setting(key: str, value: float) -> None:
        hass.config_entries.async_update_entry(entry, data={**entry.data, key: value})

    match kind_of(entry):
        case DeviceKind.HAN:
            return SimulatedHan(
                hass, entry.entry_id, data[CONF_BACKGROUND_W], store_setting
            )
        case DeviceKind.HEATER:
            cycle = DutyCycle(
                power_w=data[CONF_POWER_W],
                duty_cycle_pct=data[CONF_DUTY_CYCLE_PCT],
                period=timedelta(minutes=data[CONF_PERIOD_MIN]),
            )
            return SimulatedHeater(hass, entry.entry_id, cycle, store_setting)
        case DeviceKind.CHARGER:
            return SimulatedCharger(
                hass,
                entry.entry_id,
                data[CONF_MIN_CURRENT_A],
                data[CONF_MAX_CURRENT_A],
            )
