"""WebSocket commands for the panel (3.8, B6).

Every command requires an administrator (GUI-001).
"""

from __future__ import annotations

from typing import Any, Final

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .actions import default_action_domains
from .config_model import (
    SETTING_RANGES,
    Appliance,
    Charger,
    ChargingConfig,
    GeneralConfig,
    KraftvaktConfig,
)
from .const import DOMAIN
from .entity import entity_name
from .runtime import KraftvaktRuntime

ERR_NOT_LOADED: Final = "not_loaded"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the WebSocket commands of Kraftvakt."""
    websocket_api.async_register_command(hass, websocket_capabilities)
    websocket_api.async_register_command(hass, websocket_get_config)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/capabilities"})
@websocket_api.require_admin
@callback
def websocket_capabilities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the default actions, the limits and the defaults of the settings.

    The panel gets the limits from here, so they are kept in one place.
    """
    connection.send_result(msg["id"], capabilities())


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/config/get"})
@websocket_api.require_admin
@callback
def websocket_get_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the configuration, the names of its entities and what is missing."""
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return
    connection.send_result(
        msg["id"],
        {
            "config": runtime.config.to_dict(),
            "entity_names": entity_names(hass, runtime.config),
            "missing": [issue.to_dict() for issue in runtime.missing],
        },
    )


def capabilities() -> dict[str, Any]:
    """Return the default actions per field, and the limits and defaults."""
    general = GeneralConfig()
    charging = ChargingConfig()
    charger = Charger(id="")
    return {
        "default_actions": default_action_domains(),
        "limits": {
            section: {name: value.to_dict() for name, value in ranges.items()}
            for section, ranges in SETTING_RANGES.items()
        },
        "defaults": {
            "general": general.to_dict(),
            "appliances": {"power_reserve_kw": Appliance(id="").power_reserve_kw},
            "charging": {
                "enabled": charging.enabled,
                "one_at_a_time": charging.one_at_a_time,
            },
            "chargers": {
                "min_current_a": charger.min_current_a,
                "max_current_a": charger.max_current_a,
                "power_reserve_kw": charger.power_reserve_kw,
            },
        },
    }


def entity_names(hass: HomeAssistant, config: KraftvaktConfig) -> dict[str, str]:
    """Return the names of the entities of the appliances and chargers (GEN-013)."""
    items: list[Appliance | Charger] = [
        *config.appliances,
        *config.charging.chargers,
    ]
    return {
        item.entity_id: entity_name(hass, item.entity_id)
        for item in items
        if item.entity_id is not None
    }


def _loaded_runtime(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> KraftvaktRuntime | None:
    """Return the runtime, or send an error when Kraftvakt is not loaded."""
    if entries := hass.config_entries.async_loaded_entries(DOMAIN):
        return entries[0].runtime_data
    connection.send_error(msg["id"], ERR_NOT_LOADED, "Kraftvakt is not loaded")
    return None
