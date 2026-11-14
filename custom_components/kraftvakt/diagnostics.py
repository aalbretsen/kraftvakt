"""Diagnostics of Kraftvakt, downloaded from the integration's page."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .runtime import KraftvaktConfigEntry
from .status import status_snapshot


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> dict[str, Any]:
    """Return the configuration, the status, and the last decisions and failures.

    Nothing is redacted, since the configuration holds no credentials.
    """
    runtime = entry.runtime_data
    return {
        "config": runtime.config.to_dict(),
        "status": status_snapshot(hass, runtime),
        "recent_decisions": runtime.recent_decisions,
        "failed_actions": runtime.failed_actions,
    }
