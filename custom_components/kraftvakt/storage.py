"""Persistent storage of the configuration and the user's switches."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .config_model import (
    MAIN_ACTIONS,
    ApplianceSwitches,
    ChargerSwitches,
    KraftvaktConfig,
    appliance_switches_for,
    charger_switches_for,
    switches_to_dict,
)
from .config_reader import read_config, read_switches
from .const import DOMAIN

STORAGE_KEY: Final = f"{DOMAIN}.config"
STORAGE_VERSION: Final = 2


@dataclass(frozen=True, slots=True)
class StoredData:
    """Everything Kraftvakt keeps over a restart."""

    config: KraftvaktConfig = field(default_factory=KraftvaktConfig)
    appliance_switches: Mapping[str, ApplianceSwitches] = field(default_factory=dict)
    charger_switches: Mapping[str, ChargerSwitches] = field(default_factory=dict)


class _KraftvaktStore(Store[dict[str, Any]]):
    """The store of the configuration, which migrates older versions."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Version 2 keeps the actions of an appliance in a map with its variants."""
        if old_major_version < 2:
            old_data = _with_appliance_actions_map(old_data)
        return old_data


def _with_appliance_actions_map(data: dict[str, Any]) -> dict[str, Any]:
    appliances = data.get("appliances")
    if not isinstance(appliances, list):
        return data
    return {
        **data,
        "appliances": [
            _appliance_with_actions_map(appliance)
            if isinstance(appliance, dict)
            else appliance
            for appliance in appliances
        ],
    }


def _appliance_with_actions_map(appliance: dict[str, Any]) -> dict[str, Any]:
    migrated = {
        key: value
        for key, value in appliance.items()
        if key not in ("turn_on", "turn_off")
    }
    migrated["actions"] = {
        MAIN_ACTIONS: {
            "turn_on": appliance.get("turn_on"),
            "turn_off": appliance.get("turn_off"),
        }
    }
    return migrated


class KraftvaktStorage:
    """Loads and saves the configuration and the user's switches.

    Everything is kept in one file, written atomically, so a restart never
    sees a half-written configuration.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Create the storage for the Home Assistant instance."""
        self._store = _KraftvaktStore(
            hass, STORAGE_VERSION, STORAGE_KEY, atomic_writes=True
        )

    async def async_load(self) -> StoredData:
        """Return the stored data, or the defaults when nothing is stored.

        Raises ConfigValidationError if the stored data cannot be read.
        """
        data = await self._store.async_load()
        if data is None:
            return StoredData()
        config = read_config(data)
        appliance_switches = read_switches(
            data.get("appliance_switches") or {}, ApplianceSwitches, "appliances"
        )
        charger_switches = read_switches(
            data.get("charger_switches") or {}, ChargerSwitches, "chargers"
        )
        return StoredData(
            config,
            appliance_switches_for(config, appliance_switches),
            charger_switches_for(config, charger_switches),
        )

    async def async_save(self, stored: StoredData) -> None:
        """Save the configuration and the switches for its appliances and chargers."""
        config = stored.config
        await self._store.async_save(
            {
                **config.to_dict(),
                "appliance_switches": switches_to_dict(
                    appliance_switches_for(config, stored.appliance_switches)
                ),
                "charger_switches": switches_to_dict(
                    charger_switches_for(config, stored.charger_switches)
                ),
            }
        )
