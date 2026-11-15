"""Diagnostics of Kraftvakt, downloaded from the integration's page."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .charger_profiles.device_description import device_description
from .runtime import KraftvaktConfigEntry
from .status import status_snapshot


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> dict[str, Any]:
    """Return the configuration, the status, the state held in memory, the last decisions and failures, and the device of each charger.

    The configuration is not redacted, since it holds no credentials. The devices are described so a charger profile can be written from them.
    """
    runtime = entry.runtime_data
    return {
        "config": runtime.config.to_dict(),
        "status": status_snapshot(hass, runtime),
        **plain(runtime.diagnostics()),
        "recent_decisions": runtime.recent_decisions,
        "failed_actions": runtime.failed_actions,
        "charger_devices": {charger.id: device_description(hass, charger.device_id) for charger in runtime.config.chargers if charger.device_id is not None},
    }


def plain(value: Any) -> Any:
    """Return the value as JSON: times in ISO 8601 in Home Assistant's time zone, durations in seconds, enums as their values, sets sorted and dataclasses as objects.

    An object that is not a dataclass describes itself with `diagnostics()`.
    """
    match value:
        case Enum():
            return plain(value.value)
        case None | bool() | int() | float() | str():
            return value
        case datetime():
            return dt_util.as_local(value).isoformat()
        case timedelta():
            return value.total_seconds()
        case Mapping():
            return {str(key): plain(item) for key, item in value.items()}
        case set() | frozenset():
            return sorted((plain(item) for item in value), key=str)
        case Sequence():
            return [plain(item) for item in value]
        case _ if is_dataclass(value) and not isinstance(value, type):
            return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
        case _ if hasattr(value, "diagnostics"):
            return plain(value.diagnostics())
    raise TypeError(f"{type(value).__name__} cannot be shown in the diagnostics")
