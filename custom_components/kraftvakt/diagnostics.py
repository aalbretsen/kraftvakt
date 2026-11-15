"""Diagnostics of Kraftvakt, downloaded from the integration's page."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .charger_profiles.device_description import device_description
from .json_values import plain
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
