"""WebSocket commands for the panel."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from functools import partial
from typing import Any, Final

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.util import dt as dt_util

from .actions import default_action_domains, default_action_issues
from .config_model import (
    SETTING_RANGES,
    Appliance,
    Charger,
    ChargingConfig,
    ConfigValidationError,
    GeneralConfig,
    KraftvaktConfig,
    PriorityEntryType,
    parse_config,
)
from .const import DOMAIN
from .entity import item_name
from .regulation.model import ApplianceSlotKey, ChargerSlotKey, Waiting
from .runtime import ConfigIncompleteError, KraftvaktRuntime

ERR_NOT_LOADED: Final = "not_loaded"
ERR_REGULATION_RUNNING: Final = "regulation_running"
ERR_CONFIG_INCOMPLETE: Final = "config_incomplete"
SIGNAL_STATUS: Final = f"{DOMAIN}_status"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the WebSocket commands of Kraftvakt."""
    websocket_api.async_register_command(hass, websocket_capabilities)
    websocket_api.async_register_command(hass, websocket_get_config)
    websocket_api.async_register_command(hass, websocket_save_config)
    websocket_api.async_register_command(hass, websocket_set_running)
    websocket_api.async_register_command(hass, websocket_subscribe_status)


@callback
def async_forward_status(
    hass: HomeAssistant, runtime: KraftvaktRuntime
) -> CALLBACK_TYPE:
    """Send the status to the subscribers now and each time it may change.

    The subscribers follow the runtime that sends, so they keep getting the
    status when the config entry is reloaded.
    """
    remove = runtime.async_add_status_listener(
        lambda: async_dispatcher_send(hass, SIGNAL_STATUS, runtime)
    )
    async_dispatcher_send(hass, SIGNAL_STATUS, runtime)
    return remove


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/capabilities"})
@websocket_api.require_admin
@callback
def websocket_capabilities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the default actions, the limits and the defaults of the settings."""
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
    """Validate and save the whole configuration.

    An incomplete configuration is saved, and the result lists what is missing.
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/regulation/set_running",
        vol.Required("running"): bool,
    }
)
@websocket_api.require_admin
@callback
def websocket_set_running(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Start or stop the regulation, the same as the regulation switch."""
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return
    if not msg["running"]:
        runtime.async_stop_regulation()
    else:
        try:
            runtime.async_start_regulation()
        except ConfigIncompleteError as err:
            connection.send_error(msg["id"], ERR_CONFIG_INCOMPLETE, str(err))
            return
    connection.send_result(msg["id"], {"running": runtime.running})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/status/subscribe"})
@websocket_api.require_admin
@callback
def websocket_subscribe_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the status now and each time it may change."""
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return
    send_status = partial(_send_status, hass, connection, msg["id"])
    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_STATUS, send_status
    )
    connection.send_result(msg["id"])
    send_status(runtime)


@callback
def _send_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    subscription_id: int,
    runtime: KraftvaktRuntime,
) -> None:
    connection.send_message(
        websocket_api.event_message(subscription_id, status_snapshot(hass, runtime))
    )


def status_snapshot(hass: HomeAssistant, runtime: KraftvaktRuntime) -> dict[str, Any]:
    """Return how the regulation stands now, for the status page."""
    config = runtime.config
    averages = runtime.latest_averages
    penalty = runtime.penalty
    waiting = runtime.waiting
    waiting_key = None if waiting is None else waiting.key
    no_waiting = _waiting_fields(None, None)
    waiting_fields = _waiting_fields(waiting, runtime.waiting_ends_at)
    variant_labels = {
        variant.id: variant.label
        for appliance in config.appliances
        for variant in appliance.variants
    }
    current_variant_labels = {
        appliance_id: variant_labels[variant_id]
        for appliance_id, variant_id in runtime.current_variants.items()
        if variant_id is not None
    }
    positions = _current_positions(config, runtime.current_variants)
    return {
        "running": runtime.running,
        "missing": [issue.to_dict() for issue in runtime.missing],
        "safe_state": runtime.safe_state,
        "penalty": {
            "active": penalty.active,
            "overconsumption_wh": penalty.overconsumption_wh,
            "recovery_started": penalty.recovery_started,
        },
        "regulation_average_w": (
            None if averages is None else averages.regulation_average_w
        ),
        "capacity_average_w": (
            None if averages is None else averages.capacity_average_w
        ),
        "power_limit_w": runtime.power_limit_w,
        "regulation_window_s": config.general.regulation_window_s,
        "regulation_interval": config.general.regulation_interval,
        "next_decision_at": _local_time(runtime.next_decision_at),
        "appliances": [
            {
                "id": appliance.id,
                "name": item_name(hass, appliance),
                "on": appliance.id in runtime.appliances_on,
                "variant": current_variant_labels.get(appliance.id),
                **(
                    waiting_fields
                    if waiting_key == ApplianceSlotKey(appliance.id)
                    else no_waiting
                ),
            }
            for appliance in sorted(
                config.appliances, key=lambda appliance: positions[appliance.id]
            )
        ],
        "ev_charging_position": _ev_charging_position(config, positions),
        "chargers": [
            {
                "id": charger.id,
                "name": item_name(hass, charger),
                "activated": status.fictive_on > 0,
                "current_a": status.current_a,
                "bypassed": status.bypassed,
                "waiting": status.waiting,
                "allowed": status.allowed,
                "excluded": status.excluded,
                "charging": status.charging,
                "window_overridden": status.window_overridden,
                "car_connected": status.car_connected,
                **(
                    waiting_fields
                    if isinstance(waiting_key, ChargerSlotKey)
                    and waiting_key.charger_id == charger.id
                    else no_waiting
                ),
            }
            for charger in _in_order(
                config.charging.chargers, runtime.charging_priority
            )
            if (status := runtime.chargers.get(charger.id)) is not None
        ],
    }


def _current_positions(
    config: KraftvaktConfig, current_variants: Mapping[str, str | None]
) -> dict[str, int]:
    """The appliance itself counts as the current variant until the first decision."""
    entries = [(entry.appliance_id, entry.variant_id) for entry in config.priority]
    return {
        appliance.id: _position(
            entries, (appliance.id, current_variants.get(appliance.id))
        )
        for appliance in config.appliances
    }


def _ev_charging_position(
    config: KraftvaktConfig, positions: Mapping[str, int]
) -> int | None:
    types = [entry.type for entry in config.priority]
    if PriorityEntryType.EV_CHARGING not in types:
        return None
    ev_charging = types.index(PriorityEntryType.EV_CHARGING)
    return sum(1 for position in positions.values() if position < ev_charging)


def _in_order(chargers: Sequence[Charger], priority: Sequence[str]) -> list[Charger]:
    return sorted(chargers, key=lambda charger: _position(priority, charger.id))


def _position[T](items: Sequence[T], item: T) -> int:
    """Return the position of the item, or a place after every item if missing."""
    return items.index(item) if item in items else len(items)


def validated_config(data: dict[str, Any]) -> KraftvaktConfig:
    """Read and validate a configuration from the panel.

    Also checks the default actions, which `parse_config()` cannot do. Raises
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
            "appliances": {"power_reserve_w": Appliance(id="").power_reserve_w},
            "charging": {
                "enabled": charging.enabled,
                "one_at_a_time": charging.one_at_a_time,
            },
            "chargers": {
                "min_current_a": charger.min_current_a,
                "max_current_a": charger.max_current_a,
                "power_reserve_w": charger.power_reserve_w,
            },
        },
    }


def entity_names(hass: HomeAssistant, config: KraftvaktConfig) -> dict[str, str]:
    """Return the names of the appliances and chargers by their entities."""
    items: list[Appliance | Charger] = [
        *config.appliances,
        *config.charging.chargers,
    ]
    return {
        item.entity_id: item_name(hass, item)
        for item in items
        if item.entity_id is not None
    }


def _waiting_fields(
    waiting: Waiting | None, ends_at: datetime | None
) -> dict[str, str | None]:
    if waiting is None or ends_at is None:
        return {"waiting_since": None, "waiting_until": None, "waiting_ends_at": None}
    return {
        "waiting_since": _local_time(waiting.started_at),
        "waiting_until": _local_time(waiting.until),
        "waiting_ends_at": _local_time(ends_at),
    }


def _local_time(moment: datetime | None) -> str | None:
    return None if moment is None else dt_util.as_local(moment).isoformat()


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
    if entries := hass.config_entries.async_loaded_entries(DOMAIN):
        return entries[0].runtime_data
    connection.send_error(msg["id"], ERR_NOT_LOADED, "Kraftvakt is not loaded")
    return None
