"""WebSocket commands for the panel (3.8, B6).

Every command requires an administrator (GUI-001).
"""

from __future__ import annotations

from typing import Any, Final

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .actions import default_action_domains, default_action_issues
from .config_model import (
    SETTING_RANGES,
    Appliance,
    Charger,
    ChargingConfig,
    ConfigValidationError,
    GeneralConfig,
    KraftvaktConfig,
    parse_config,
)
from .const import DOMAIN
from .entity import entity_name
from .runtime import KraftvaktRuntime

ERR_NOT_LOADED: Final = "not_loaded"
ERR_REGULATION_RUNNING: Final = "regulation_running"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the WebSocket commands of Kraftvakt."""
    websocket_api.async_register_command(hass, websocket_capabilities)
    websocket_api.async_register_command(hass, websocket_get_config)
    websocket_api.async_register_command(hass, websocket_save_config)


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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/config/save",
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_save_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Validate and save the whole configuration (B7).

    Refused with `regulation_running` while the regulation runs (REG-010). An
    invalid configuration is not saved, and the result lists every issue. An
    incomplete configuration is saved, and the result lists what is missing.
    """
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return
    if runtime.running:
        _send_regulation_running(connection, msg)
        return
    try:
        config = validated_config(msg["config"])
    except ConfigValidationError as err:
        connection.send_result(
            msg["id"],
            {"saved": False, "errors": [issue.to_dict() for issue in err.issues]},
        )
        return
    await runtime.async_save_config(config)
    connection.send_result(
        msg["id"],
        {
            "saved": True,
            "config": config.to_dict(),
            "missing": [issue.to_dict() for issue in runtime.missing],
        },
    )


def validated_config(data: dict[str, Any]) -> KraftvaktConfig:
    """Read and validate a configuration from the panel.

    Also checks that a default action is available for the domain of each
    entity it is chosen for (T18), which parse_config cannot do. Raises
    ConfigValidationError with every issue found.
    """
    config = parse_config(data)
    if issues := default_action_issues(config):
        raise ConfigValidationError(issues)
    return config


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


def _send_regulation_running(
    connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    connection.send_error(
        msg["id"],
        ERR_REGULATION_RUNNING,
        "The regulation must be stopped to change the configuration",
    )


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
