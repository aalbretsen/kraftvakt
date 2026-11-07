"""Persistent storage of the configuration and the charger switches (GEN-011, B3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .config_model import (
    ChargerSwitches,
    KraftvaktConfig,
    charger_switches_for,
    charger_switches_from_dict,
    charger_switches_to_dict,
)
from .const import DOMAIN

STORAGE_KEY: Final = f"{DOMAIN}.config"
STORAGE_VERSION: Final = 1


@dataclass(frozen=True, slots=True)
class StoredData:
    """Everything Kraftvakt keeps over a restart."""

    config: KraftvaktConfig = field(default_factory=KraftvaktConfig)
    charger_switches: Mapping[str, ChargerSwitches] = field(default_factory=dict)


class KraftvaktStorage:
    """Loads and saves the configuration and the charger switches.

    Both are kept in one file, written atomically, so a restart never sees a
    half-written configuration.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Create the storage for the Home Assistant instance."""
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, STORAGE_KEY, atomic_writes=True
        )

    async def async_load(self) -> StoredData:
        """Return the stored data, or the defaults when nothing is stored.

        Raises ConfigValidationError if the stored data cannot be read.
        """
        data = await self._store.async_load()
        if data is None:
            return StoredData()
        config = KraftvaktConfig.from_dict(data)
        switches = charger_switches_from_dict(data.get("charger_switches") or {})
        return StoredData(config, charger_switches_for(config, switches))

    async def async_save(self, stored: StoredData) -> None:
        """Save the configuration and the switches for its chargers."""
        switches = charger_switches_for(stored.config, stored.charger_switches)
        await self._store.async_save(
            {
                **stored.config.to_dict(),
                "charger_switches": charger_switches_to_dict(switches),
            }
        )
