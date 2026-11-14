"""The status of the regulation, as the status page shows it."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .config_model import Appliance, Charger, ChargerGroup, PriorityEntryType
from .entity import item_name
from .regulation.charging import ChargerStatus
from .regulation.model import AmpereStepKey, ApplianceStepKey
from .runtime import KraftvaktRuntime

NO_WAITING: Mapping[str, None] = {
    "waiting_since": None,
    "waiting_until": None,
    "waiting_ends_at": None,
}


def status_snapshot(hass: HomeAssistant, runtime: KraftvaktRuntime) -> dict[str, Any]:
    """Return how the regulation stands now, for the status page."""
    config = runtime.config
    averages = runtime.latest_averages
    penalty = runtime.penalty
    return {
        "running": runtime.running,
        "config_version": runtime.config_version,
        "missing": [issue.to_dict() for issue in runtime.missing],
        "safe_state": runtime.safe_state,
        "penalty": {
            "active": penalty.active,
            "overconsumption_wh": penalty.overconsumption_wh,
            "recovery_started": penalty.recovery_started,
        },
        "regulation_average_w": (None if averages is None else averages.regulation_average_w),
        "tariff_average_w": None if averages is None else averages.tariff_average_w,
        "power_limit_w": config.general.power_limit_w,
        "regulation_window_s": config.general.regulation_window_s,
        "regulation_interval": config.general.regulation_interval,
        "next_decision_at": _local_time(runtime.next_decision_at),
        "priority": _priority_rows(hass, runtime),
    }


def _priority_rows(hass: HomeAssistant, runtime: KraftvaktRuntime) -> list[dict[str, Any]]:
    """Return the priority list with each appliance at the entry of its current variant.

    Before the first decision after a start, the appliance itself is the
    current variant.
    """
    config = runtime.config
    appliances = {appliance.id: appliance for appliance in config.appliances}
    groups = {group.id: group for group in config.charger_groups}
    current_variants = runtime.current_variants
    rows = []
    for entry in config.priority:
        if entry.type is PriorityEntryType.CHARGER_GROUP:
            group = groups[entry.group_id or ""]
            rows.append(_charger_group_status(hass, runtime, group))
        elif current_variants.get(entry.appliance_id or "") == entry.variant_id:
            appliance = appliances[entry.appliance_id or ""]
            rows.append(_appliance_status(hass, runtime, appliance))
    return rows


def _charger_group_status(hass: HomeAssistant, runtime: KraftvaktRuntime, group: ChargerGroup) -> dict[str, Any]:
    priority = runtime.charging_priorities.get(group.id, [])
    return {
        "type": PriorityEntryType.CHARGER_GROUP.value,
        "id": group.id,
        "name": group.name,
        "chargers": [
            _charger_status(hass, runtime, charger, status) for charger in _in_order(group.chargers, priority) if (status := runtime.chargers.get(charger.id)) is not None
        ],
    }


def _appliance_status(hass: HomeAssistant, runtime: KraftvaktRuntime, appliance: Appliance) -> dict[str, Any]:
    variant_id = runtime.current_variants.get(appliance.id)
    variant = next((variant for variant in appliance.variants if variant.id == variant_id), None)
    return {
        "type": PriorityEntryType.APPLIANCE.value,
        "id": appliance.id,
        "name": item_name(hass, appliance),
        "on": appliance.id in runtime.appliances_on,
        "excluded": appliance.id in runtime.excluded_appliances,
        "variant": None if variant is None else variant.label,
        **_waiting_fields(runtime, ApplianceStepKey(appliance.id)),
    }


def _charger_status(
    hass: HomeAssistant,
    runtime: KraftvaktRuntime,
    charger: Charger,
    status: ChargerStatus,
) -> dict[str, Any]:
    return {
        "id": charger.id,
        "name": item_name(hass, charger),
        "state": status.state.value,
        "activated": status.ampere_steps_on > 0,
        "current_a": status.current_a,
        "bypassed": status.bypassed,
        "charging": status.charging,
        **_waiting_fields(runtime, charger.id),
    }


def _waiting_fields(runtime: KraftvaktRuntime, waiting_for: ApplianceStepKey | str) -> Mapping[str, str | None]:
    """Return when the waiting started and ends, for the step that waits.

    `waiting_for` is the step of an appliance, or the id of a charger whose
    next ampere step waits.
    """
    waiting = runtime.waiting
    ends_at = runtime.waiting_ends_at
    if waiting is None or ends_at is None:
        return NO_WAITING
    key = waiting.key
    waiting_charger = key.charger_id if isinstance(key, AmpereStepKey) else None
    if key != waiting_for and waiting_charger != waiting_for:
        return NO_WAITING
    return {
        "waiting_since": _local_time(waiting.started_at),
        "waiting_until": _local_time(waiting.until),
        "waiting_ends_at": _local_time(ends_at),
    }


def _in_order(chargers: Sequence[Charger], priority: Sequence[str]) -> list[Charger]:
    return sorted(chargers, key=lambda charger: _position(priority, charger.id))


def _position[T](items: Sequence[T], item: T) -> int:
    """Return the position of the item, or a place after every item if missing."""
    return items.index(item) if item in items else len(items)


def _local_time(moment: datetime | None) -> str | None:
    return None if moment is None else dt_util.as_local(moment).isoformat()
