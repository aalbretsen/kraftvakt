"""WebSocket commands for the panel (3.8, B6).

Every command requires an administrator (GUI-001).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
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
from .entity import entity_name, item_name
from .regulation.model import ApplianceSlotKey, ChargerSlotKey
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
    """Start or stop the regulation, the same as the regulation switch (GUI-007).

    Starting is refused with `config_incomplete` until the configuration is
    complete (REG-016).
    """
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
    """Send the status now and then at each new average, decision, start and stop.

    The status is what the status page shows (GUI-005, GUI-006, T11).
    """
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return

    @callback
    def send_status(runtime: KraftvaktRuntime) -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], status_snapshot(hass, runtime))
        )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_STATUS, send_status
    )
    connection.send_result(msg["id"])
    send_status(runtime)


def status_snapshot(hass: HomeAssistant, runtime: KraftvaktRuntime) -> dict[str, Any]:
    """Return how the regulation stands now (GUI-005, GUI-006, T11).

    `waiting_until` is set for the appliance or charger whose slot is next and
    waits (REG-012). The averages are None until the first window has closed.
    The appliances are in the order of their current variant in the priority
    list, and the chargers in the current charging priority.
    """
    config = runtime.config
    averages = runtime.latest_averages
    penalty = runtime.penalty
    waiting = runtime.waiting
    waiting_key = None if waiting is None else waiting.key
    waiting_until = None if waiting is None else _local_time(waiting.until)
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
    return {
        "running": runtime.running,
        "missing": [issue.to_dict() for issue in runtime.missing],
        "safe_state": runtime.safe_state,
        "penalty": {
            "active": penalty.active,
            "overconsumption_kwh": penalty.overconsumption_kwh,
            "recovery_started": penalty.recovery_started,
        },
        "regulation_average_kw": (
            None if averages is None else averages.regulation_average_kw
        ),
        "capacity_average_kw": (
            None if averages is None else averages.capacity_average_kw
        ),
        "power_limit_kw": config.general.power_limit_kw,
        "next_decision_at": _local_time(runtime.next_decision_at),
        "appliances": [
            {
                "id": appliance.id,
                "name": item_name(hass, appliance),
                "on": appliance.id in runtime.appliances_on,
                "variant": current_variant_labels.get(appliance.id),
                "waiting_until": (
                    waiting_until
                    if waiting_key == ApplianceSlotKey(appliance.id)
                    else None
                ),
            }
            for appliance in _in_current_priority(config, runtime.current_variants)
        ],
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
                "waiting_until": (
                    waiting_until
                    if isinstance(waiting_key, ChargerSlotKey)
                    and waiting_key.charger_id == charger.id
                    else None
                ),
            }
            for charger in _in_order(
                config.charging.chargers, runtime.charging_priority
            )
            if (status := runtime.chargers.get(charger.id)) is not None
        ],
    }


def _in_current_priority(
    config: KraftvaktConfig, current_variants: Mapping[str, str | None]
) -> list[Appliance]:
    """Return the appliances in the order of the entries for their current variant.

    The appliance itself counts as the current variant until the first decision.
    """
    entries = [
        (entry.appliance_id, entry.variant_id)
        for entry in config.priority
        if entry.type is PriorityEntryType.APPLIANCE
    ]
    return sorted(
        config.appliances,
        key=lambda appliance: _position(
            entries, (appliance.id, current_variants.get(appliance.id))
        ),
    )


def _in_order(chargers: Sequence[Charger], priority: Sequence[str]) -> list[Charger]:
    """Return the chargers in the current charging priority (LAD-016)."""
    return sorted(chargers, key=lambda charger: _position(priority, charger.id))


def _position[T](items: Sequence[T], item: T) -> int:
    """Return the position of the item, or a place after every item if missing."""
    return items.index(item) if item in items else len(items)


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
    """Return the runtime, or send an error when Kraftvakt is not loaded."""
    if entries := hass.config_entries.async_loaded_entries(DOMAIN):
        return entries[0].runtime_data
    connection.send_error(msg["id"], ERR_NOT_LOADED, "Kraftvakt is not loaded")
    return None
