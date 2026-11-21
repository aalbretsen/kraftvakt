"""The user's switches for the appliances and the chargers."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .config_model import (
    ApplianceSwitches,
    ChargerSwitches,
    KraftvaktConfig,
    OverrideEnd,
    appliance_switches_for,
    charger_switches_for,
)
from .storage import KraftvaktStorage, StoredData

type SwitchListener = Callable[[], None]


class Settings:
    """The stored configuration and the user's switches, saved together."""

    def __init__(self, hass: HomeAssistant, storage: KraftvaktStorage, stored: StoredData) -> None:
        self._hass = hass
        self._storage = storage
        self._config = stored.config
        self._appliance_switches = appliance_switches_for(stored.config, stored.appliance_switches)
        self._charger_switches = charger_switches_for(stored.config, stored.charger_switches)
        self._armed_overrides: set[str] = set()
        self._charged_in_window: set[str] = set()
        self._listeners: list[SwitchListener] = []

    @property
    def config(self) -> KraftvaktConfig:
        return self._config

    def diagnostics(self) -> dict[str, Any]:
        """Return the switches, the armed overrides and the chargers charged in their window; the configuration is a section of its own."""
        return {
            "appliance_switches": self._appliance_switches,
            "charger_switches": self._charger_switches,
            "armed_overrides": self._armed_overrides,
            "charged_in_window": self._charged_in_window,
        }

    def appliance_switches(self, appliance_id: str) -> ApplianceSwitches:
        return self._appliance_switches.get(appliance_id, ApplianceSwitches())

    def charger_switches(self, charger_id: str) -> ChargerSwitches:
        return self._charger_switches.get(charger_id, ChargerSwitches())

    def override_armed(self, charger_id: str) -> bool:
        """Return whether what ends the override has been seen since it was switched on.

        It is kept in memory only, so after a restart a car that is still
        connected or charging arms the override again at a decision.
        """
        return charger_id in self._armed_overrides

    @callback
    def async_arm_overrides(self, charger_ids: Iterable[str]) -> None:
        self._armed_overrides |= {charger_id for charger_id in charger_ids if self.charger_switches(charger_id).window_override}

    def charged_in_window(self, charger_id: str) -> bool:
        """Return whether the charger charged inside its charging window since the car was connected.

        It is kept in memory only, so a restart forgets it.
        """
        return charger_id in self._charged_in_window

    @callback
    def async_update_charged_in_window(self, added: Iterable[str], removed: Iterable[str]) -> None:
        self._charged_in_window = (self._charged_in_window | set(added)) - set(removed)

    async def async_set_appliance(self, appliance_id: str, *, excluded: bool) -> None:
        """Change the switches for the appliance and save them at once."""
        self._appliance_switches[appliance_id] = ApplianceSwitches(excluded=excluded)
        self._notify()
        await self.async_save()

    async def async_set_charger(
        self,
        charger_id: str,
        *,
        excluded: bool | None = None,
        window_override: bool | None = None,
    ) -> None:
        """Change the switches for the charger and save them at once."""
        self._apply_charger(charger_id, excluded, window_override)
        await self.async_save()

    @callback
    def async_reset_window_override(self, charger_id: str) -> None:
        """Switch the override off when it has ended."""
        self._apply_charger(charger_id, None, False)
        self._hass.async_create_task(self.async_save(), "kraftvakt save switches")

    @callback
    def async_use_config(self, config: KraftvaktConfig) -> None:
        """Use a new configuration and keep the switches of its items; not saved yet.

        An override stays armed only while what ends it is the same.
        """
        previous_ends = _override_ends(self._config)
        self._config = config
        self._appliance_switches = appliance_switches_for(config, self._appliance_switches)
        self._charger_switches = charger_switches_for(config, self._charger_switches)
        current_ends = _override_ends(config)
        self._armed_overrides = {charger_id for charger_id in self._armed_overrides if charger_id in current_ends and previous_ends.get(charger_id) is current_ends[charger_id]}
        self._charged_in_window &= current_ends.keys()
        self._notify()

    @callback
    def async_add_listener(self, listener: SwitchListener) -> CALLBACK_TYPE:
        """Call `listener` each time the switches or the configuration change."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _apply_charger(self, charger_id: str, excluded: bool | None, window_override: bool | None) -> None:
        current = self._charger_switches[charger_id]
        updated = replace(
            current,
            excluded=current.excluded if excluded is None else excluded,
            window_override=(current.window_override if window_override is None else window_override),
        )
        if updated.window_override != current.window_override:
            self._armed_overrides.discard(charger_id)
        self._charger_switches[charger_id] = updated
        self._notify()

    async def async_save(self) -> None:
        await self._storage.async_save(StoredData(self._config, self._appliance_switches, self._charger_switches))

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()


def _override_ends(config: KraftvaktConfig) -> dict[str, OverrideEnd]:
    return {charger.id: charger.override_ends for charger in config.chargers}
