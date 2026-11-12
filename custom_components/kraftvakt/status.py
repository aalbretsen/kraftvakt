"""The status of the regulation, as the status page shows it."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .config_model import (
    Appliance,
    Charger,
    ChargerGroup,
    KraftvaktConfig,
    PriorityEntryType,
)
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
    positions = _current_positions(config, runtime.current_variants)
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
        "regulation_average_w": (
            None if averages is None else averages.regulation_average_w
        ),
        "tariff_average_w": (None if averages is None else averages.tariff_average_w),
        "power_limit_w": config.general.power_limit_w,
        "regulation_window_s": config.general.regulation_window_s,
        "regulation_interval": config.general.regulation_interval,
        "next_decision_at": _local_time(runtime.next_decision_at),
        "appliances": [
            _appliance_status(hass, runtime, appliance)
            for appliance in sorted(
                config.appliances, key=lambda appliance: positions[appliance.id]
            )
        ],
        "charger_groups": [
            _charger_group_status(hass, runtime, group, positions)
            for group in _groups_in_order(config)
        ],
    }


def _charger_group_status(
    hass: HomeAssistant,
    runtime: KraftvaktRuntime,
    group: ChargerGroup,
    positions: Mapping[str, int],
) -> dict[str, Any]:
    priority = runtime.charging_priorities.get(group.id, [])
    return {
        "id": group.id,
        "name": group.name,
        "position": _charger_group_position(runtime.config, group, positions),
        "chargers": [
            _charger_status(hass, runtime, charger, status)
            for charger in _in_order(group.chargers, priority)
            if (status := runtime.chargers.get(charger.id)) is not None
        ],
    }


def _appliance_status(
    hass: HomeAssistant, runtime: KraftvaktRuntime, appliance: Appliance
) -> dict[str, Any]:
    variant_id = runtime.current_variants.get(appliance.id)
    variant = next(
        (variant for variant in appliance.variants if variant.id == variant_id), None
    )
    return {
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


def _waiting_fields(
    runtime: KraftvaktRuntime, waiting_for: ApplianceStepKey | str
) -> Mapping[str, str | None]:
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


def _groups_in_order(config: KraftvaktConfig) -> list[ChargerGroup]:
    """Return the groups in the order of their entries."""
    entries = [
        entry.group_id
        for entry in config.priority
        if entry.type is PriorityEntryType.CHARGER_GROUP
    ]
    return sorted(config.charger_groups, key=lambda group: _position(entries, group.id))


def _charger_group_position(
    config: KraftvaktConfig, group: ChargerGroup, positions: Mapping[str, int]
) -> int:
    """Return how many appliances come before the entry of the group."""
    entry = _position([entry.group_id for entry in config.priority], group.id)
    return sum(1 for position in positions.values() if position < entry)


def _in_order(chargers: Sequence[Charger], priority: Sequence[str]) -> list[Charger]:
    return sorted(chargers, key=lambda charger: _position(priority, charger.id))


def _position[T](items: Sequence[T], item: T) -> int:
    """Return the position of the item, or a place after every item if missing."""
    return items.index(item) if item in items else len(items)


def _local_time(moment: datetime | None) -> str | None:
    return None if moment is None else dt_util.as_local(moment).isoformat()
