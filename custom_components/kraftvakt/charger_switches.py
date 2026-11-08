"""The user's switches for the chargers (ENT-003, ENT-004, GEN-011)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .config_model import ChargerSwitches, KraftvaktConfig, charger_switches_for
from .storage import KraftvaktStorage, StoredData

type SwitchListener = Callable[[], None]


class ChargerSwitchBoard:
    """Keeps the positions of the charger switches and saves them at once.

    The positions are configuration and are kept over any restart, together
    with the rest of the configuration (GEN-011, B3). When the override of the
    charging window was switched on is kept only in memory. After a restart of
    Home Assistant or the integration, the first start of the regulation counts
    instead (T13). The switches can be used while the regulation runs, and the
    regulation reads them at its next decision (REG-005, REG-010).
    """

    def __init__(
        self, hass: HomeAssistant, storage: KraftvaktStorage, stored: StoredData
    ) -> None:
        """Create the board from the stored configuration and switches."""
        self._hass = hass
        self._storage = storage
        self._config = stored.config
        self._switches = charger_switches_for(stored.config, stored.charger_switches)
        self._override_switched_on_at: dict[str, datetime] = {}
        self._listeners: list[SwitchListener] = []

    @property
    def config(self) -> KraftvaktConfig:
        """Return the configuration the switches belong to."""
        return self._config

    def switches(self, charger_id: str) -> ChargerSwitches:
        """Return the positions of the switches for the charger."""
        return self._switches.get(charger_id, ChargerSwitches())

    def override_switched_on_at(self, charger_id: str) -> datetime | None:
        """Return when the override was switched on, if it is on and known (T13)."""
        return self._override_switched_on_at.get(charger_id)

    @callback
    def async_regulation_started(self, now: datetime) -> None:
        """Count overrides switched on before a restart from `now` (LAD-027, T13).

        Overrides whose switch-on time is known keep it.
        """
        for charger_id, switches in self._switches.items():
            if switches.window_override:
                self._override_switched_on_at.setdefault(charger_id, now)

    async def async_set(
        self,
        charger_id: str,
        *,
        excluded: bool | None = None,
        window_override: bool | None = None,
    ) -> None:
        """Change the switches for the charger and save them at once."""
        self._apply(charger_id, excluded, window_override)
        await self._async_save()

    @callback
    def async_reset_window_override(self, charger_id: str) -> None:
        """Switch the override off when it has ended (LAD-027, ENT-004).

        The position changes at once and is saved in the background.
        """
        self._apply(charger_id, None, False)
        self._hass.async_create_task(
            self._async_save(), "kraftvakt save charger switches"
        )

    async def async_update_config(self, config: KraftvaktConfig) -> None:
        """Use a new configuration and save it with the switches (B9).

        Chargers that remain keep their switches, new chargers get the default
        positions, and the switches of removed chargers are dropped.
        """
        self._config = config
        self._switches = charger_switches_for(config, self._switches)
        self._override_switched_on_at = {
            charger_id: switched_on_at
            for charger_id, switched_on_at in self._override_switched_on_at.items()
            if charger_id in self._switches
        }
        self._notify()
        await self._async_save()

    @callback
    def async_add_listener(self, listener: SwitchListener) -> CALLBACK_TYPE:
        """Call `listener` each time the switches or the configuration change."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _apply(
        self, charger_id: str, excluded: bool | None, window_override: bool | None
    ) -> None:
        current = self._switches[charger_id]
        updated = replace(
            current,
            excluded=current.excluded if excluded is None else excluded,
            window_override=(
                current.window_override if window_override is None else window_override
            ),
        )
        if updated.window_override and not current.window_override:
            self._override_switched_on_at[charger_id] = dt_util.utcnow()
        elif not updated.window_override:
            self._override_switched_on_at.pop(charger_id, None)
        self._switches[charger_id] = updated
        self._notify()

    async def _async_save(self) -> None:
        await self._storage.async_save(StoredData(self._config, self._switches))

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()
