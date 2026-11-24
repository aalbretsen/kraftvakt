"""The recorded history of the entities the regulation reads and sets, for the diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Final

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .actions import action_entities
from .conditions import condition_entities, group_variables, item_variables
from .config_model import KraftvaktConfig
from .const import DOMAIN
from .item_entity import ChargerEntity, item_entity_key
from .json_values import plain
from .runtime import KraftvaktConfigEntry
from .switch import ApplianceSwitch

HISTORY_PERIOD: Final = timedelta(hours=24)

# Kraftvakt's entities that change at every regulation window, which the power sensor's history and the measurements already cover.
EVERY_WINDOW_ENTITY_KEYS: Final = frozenset({"power_regulation_average", "power_tariff_average", "power_free", "waiting_time_next_turn_on"})


@dataclass(frozen=True, slots=True)
class EntityUse:
    """`item` is the id of the appliance, charger or charger group, None for the power sensor and the entities of the regulation."""

    item: str | None
    field: str


type EntityUses = dict[str, list[EntityUse]]


async def async_recorded_history(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> dict[str, Any] | None:
    """Return the states of the entities the regulation reads and sets over the last day, None without the recorder.

    The entities it sets come with their attributes, since an action may set an attribute, such as the temperature of a thermostat.
    """
    if "recorder" not in hass.config.components:
        return None
    config = entry.runtime_data.config
    inputs, outputs = _read_entities(hass, config), _set_entities(hass, config)
    for entity_id, uses in _kraftvakt_entities(hass, entry, config).items():
        inputs.setdefault(entity_id, []).extend(uses)
    inputs = {entity_id: uses for entity_id, uses in inputs.items() if entity_id not in outputs}
    end = dt_util.utcnow()
    start = end - HISTORY_PERIOD
    recorded = {
        **await _async_states(hass, start, end, list(inputs), with_attributes=False),
        **await _async_states(hass, start, end, list(outputs), with_attributes=True),
    }
    entities = {
        entity_id: {"uses": uses, "states": [_state_record(state, entity_id in outputs) for state in recorded.get(entity_id, [])]} for entity_id, uses in (outputs | inputs).items()
    }
    history_section: dict[str, Any] = plain({"start": start, "end": end, "entities": entities})
    return history_section


def _read_entities(hass: HomeAssistant, config: KraftvaktConfig) -> EntityUses:
    uses: EntityUses = {}
    if config.general.power_sensor:
        _add(uses, config.general.power_sensor, EntityUse(None, "power_sensor"))
    for _, item in config.items():
        variables = item_variables(hass, item)
        for field_name, condition in item.regulation_conditions():
            for entity_id in sorted(condition_entities(hass, condition, variables)):
                _add(uses, entity_id, EntityUse(item.id, field_name))
    for group in config.charger_groups:
        for field_name, condition in group.conditions():
            for entity_id in sorted(condition_entities(hass, condition, group_variables(config))):
                _add(uses, entity_id, EntityUse(group.id, field_name))
    return uses


def _set_entities(hass: HomeAssistant, config: KraftvaktConfig) -> EntityUses:
    uses: EntityUses = {}
    for _, item in config.items():
        if item.controlled_entity is not None:
            _add(uses, item.controlled_entity, EntityUse(item.id, "controlled_entity"))
        for field_name, entity_id in action_entities(hass, item):
            _add(uses, entity_id, EntityUse(item.id, field_name))
    return uses


def _kraftvakt_entities(hass: HomeAssistant, entry: KraftvaktConfigEntry, config: KraftvaktConfig) -> EntityUses:
    """Return Kraftvakt's own entities, but those that change at every regulation window, under the appliance or charger they belong to."""
    item_prefixes = {
        item_entity_key(kind, item.id, ""): item.id for kind, items in ((ApplianceSwitch.kind, config.appliances), (ChargerEntity.kind, config.chargers)) for item in items
    }
    uses: EntityUses = {}
    for registry_entry in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id):
        key = registry_entry.translation_key
        if registry_entry.platform != DOMAIN or key is None or key in EVERY_WINDOW_ENTITY_KEYS:
            continue
        item = next((item_id for prefix, item_id in item_prefixes.items() if registry_entry.unique_id.startswith(prefix)), None)
        _add(uses, registry_entry.entity_id, EntityUse(item, key))
    return uses


def _add(uses: EntityUses, entity_id: str, use: EntityUse) -> None:
    entity_uses = uses.setdefault(entity_id, [])
    if use not in entity_uses:
        entity_uses.append(use)


async def _async_states(hass: HomeAssistant, start: datetime, end: datetime, entity_ids: list[str], *, with_attributes: bool) -> dict[str, list[State]]:
    """Return the state at the start and every change after it; with attributes, also the changes of attributes the recorder finds significant."""
    if not entity_ids:  # The recorder refuses an empty list.
        return {}
    states: dict[str, list[Any]] = await get_instance(hass).async_add_executor_job(
        partial(history.get_significant_states, hass, start, end, entity_ids, no_attributes=not with_attributes)
    )
    return states


def _state_record(state: State, with_attributes: bool) -> dict[str, Any]:
    if with_attributes:
        return {"time": state.last_updated, "state": state.state, "attributes": dict(state.attributes)}
    return {"time": state.last_changed, "state": state.state}
