"""WebSocket commands for the panel."""

from __future__ import annotations

from functools import partial
from typing import Any, Final

import probatio as vol
from homeassistant.components import websocket_api
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from .actions import action_issues, default_actions_by_field, domain_actions_by_field
from .charger_profiles.recognition import charger_profile_fields
from .config_model import (
    SETTING_RANGES,
    Appliance,
    Charger,
    ChargerGroup,
    ConfigValidationError,
    GeneralConfig,
    KraftvaktConfig,
)
from .config_validation import (
    parse_config,
)
from .const import DOMAIN
from .devices import device_issues
from .diagnostics_feed import DiagnosticsFeed
from .entity import item_name
from .power_measurement import async_analyse_power_sensor, report_analysis_dict
from .runtime import ConfigIncompleteError, KraftvaktRuntime, RegulationRunningError
from .status import status_snapshot

SIGNAL_STATUS: Final = f"{DOMAIN}_status"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, websocket_capabilities)
    websocket_api.async_register_command(hass, websocket_get_charger_profile)
    websocket_api.async_register_command(hass, websocket_get_config)
    websocket_api.async_register_command(hass, websocket_power_sensor_analysis)
    websocket_api.async_register_command(hass, websocket_save_config)
    websocket_api.async_register_command(hass, websocket_set_running)
    websocket_api.async_register_command(hass, websocket_subscribe_status)
    websocket_api.async_register_command(hass, websocket_subscribe_diagnostics)


@callback
def async_forward_status(hass: HomeAssistant, runtime: KraftvaktRuntime) -> CALLBACK_TYPE:
    """Send the status to the subscribers now and each time it may change.

    The subscribers follow the runtime that sends, so they keep getting the
    status when the config entry is reloaded.
    """
    remove = runtime.async_add_status_listener(lambda: async_dispatcher_send(hass, SIGNAL_STATUS, runtime))
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
    connection.send_result(msg["id"], capabilities())


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/charger_profile/get", vol.Required("device_id"): str})
@websocket_api.require_admin
@callback
def websocket_get_charger_profile(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the name of the device's charger profile and the fields of a charger it fills, none without a profile."""
    profile, fields = charger_profile_fields(hass, msg["device_id"])
    connection.send_result(msg["id"], {"profile": None if profile is None else profile.name, "fields": fields})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/power_sensor/analysis", vol.Required("entity_id"): str})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_power_sensor_analysis(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send how the power sensor reports, from the updates Kraftvakt follows over the last hour, or else from its history or by listening to it."""
    entity_id = msg["entity_id"]
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    runtime: KraftvaktRuntime | None = entries[0].runtime_data if entries else None
    analysis = runtime.power_report_analysis() if runtime is not None and runtime.followed_power_sensor == entity_id else None
    if analysis is None or not analysis.known:
        analysis = await async_analyse_power_sensor(hass, entity_id)
    connection.send_result(msg["id"], report_analysis_dict(analysis))


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
        config = validated_config(hass, msg["config"])
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
            connection.send_error(msg["id"], "config_incomplete", str(err))
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
    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_STATUS, send_status)
    connection.send_result(msg["id"])
    send_status(runtime)


@callback
def _send_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    subscription_id: int,
    runtime: KraftvaktRuntime,
) -> None:
    connection.send_message(websocket_api.event_message(subscription_id, status_snapshot(hass, runtime)))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/diagnostics/subscribe"})
@websocket_api.require_admin
@callback
def websocket_subscribe_diagnostics(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send what the diagnostics page shows now and each time the status may change."""
    if (runtime := _loaded_runtime(hass, connection, msg)) is None:
        return
    feed = DiagnosticsFeed()

    @callback
    def send(runtime: KraftvaktRuntime) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], feed.event(runtime)))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_STATUS, send)
    connection.send_result(msg["id"])
    send(runtime)


def validated_config(hass: HomeAssistant, data: dict[str, Any]) -> KraftvaktConfig:
    """Read and validate a configuration from the panel.

    Also checks that the actions can run for their entities, which
    `parse_config()` cannot do. Raises ConfigValidationError with every issue
    found.
    """
    config = parse_config(data)
    if issues := action_issues(hass, config) + device_issues(hass, config):
        raise ConfigValidationError(issues)
    return config


def capabilities() -> dict[str, Any]:
    """Return the default and domain actions per field, the limits and defaults."""
    general = GeneralConfig()
    group = ChargerGroup(id="")
    charger = Charger(id="")
    return {
        "default_actions": default_actions_by_field(),
        "domain_actions": domain_actions_by_field(),
        "limits": {section: {name: value.to_dict() for name, value in ranges.items()} for section, ranges in SETTING_RANGES.items()},
        "defaults": {
            "general": general.to_dict(),
            "appliances": {"power_reserve_w": Appliance(id="").power_reserve_w},
            "charger_groups": {
                "one_at_a_time": group.one_at_a_time,
                "dynamic_order": group.dynamic_order,
            },
            "chargers": {
                "switched_by": charger.switched_by.value,
                "min_current_a": charger.min_current_a,
                "max_current_a": charger.max_current_a,
                "min_current_power_w": charger.min_current_power_w,
                "override_ends": charger.override_ends.value,
                "cloud_controlled": charger.cloud_controlled,
                "start_delay_s": charger.start_delay_s,
            },
        },
    }


def entity_names(hass: HomeAssistant, config: KraftvaktConfig) -> dict[str, str]:
    """Return the names of the appliances and chargers by their entities."""
    items: list[Appliance | Charger] = [
        *config.appliances,
        *config.chargers,
    ]
    return {entity_id: item_name(hass, item) for item in items if (entity_id := item.controlled_entity) is not None}


def _send_regulation_running(connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    connection.send_error(msg["id"], "regulation_running", str(RegulationRunningError()))


def _loaded_runtime(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> KraftvaktRuntime | None:
    if entries := hass.config_entries.async_loaded_entries(DOMAIN):
        runtime: KraftvaktRuntime = entries[0].runtime_data
        return runtime
    connection.send_error(msg["id"], "not_loaded", "Kraftvakt is not loaded")
    return None
