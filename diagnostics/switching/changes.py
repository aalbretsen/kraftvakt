"""How often each entity the regulation reads and sets changed, from the recorded history in a diagnostics file, grouped by appliance and EV charger."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Any

from ..diagnostics_file import DiagnosticsFile


@dataclass(frozen=True, slots=True)
class EntityChanges:
    """The changes of an entity's state, leaving out unavailable and unknown, which are counted as lost values.

    An entity without states is not recorded, as when it is excluded from the recorder.
    A state that is a number has increases, decreases and reversals, where a reversal is a change in the other direction than the one before.
    Any other state has the number of changes to each state. The attributes count changes of each attribute, for the entities the regulation sets.
    """

    entity_id: str
    fields: tuple[str, ...]
    recorded: bool
    changes: int
    increases: int | None
    decreases: int | None
    reversals: int | None
    changes_to: Mapping[str, int] | None
    shortest_hold: timedelta | None
    busiest_hour: tuple[datetime, int] | None
    lost_values: int
    attribute_changes: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class ItemChanges:
    label: str
    entities: tuple[EntityChanges, ...]


@dataclass(frozen=True, slots=True)
class HistoryChanges:
    start: datetime
    end: datetime
    items: tuple[ItemChanges, ...]


def history_changes(diagnostics: DiagnosticsFile) -> HistoryChanges:
    """Return the changes of each entity under each appliance and EV charger that uses it, after the power sensor and the regulation's own entities."""
    config, history = diagnostics.config, diagnostics.history
    labels: dict[str | None, str] = {None: "Power sensor and regulation"}
    for appliance in config.appliances:
        labels[appliance.id] = f"Appliance {appliance.entity_id or appliance.id}"
    for group in config.charger_groups:
        for charger in group.chargers:
            labels[charger.id] = f"EV charger {charger.controlled_entity or charger.id} in {group.name}"
    rows: dict[str | None, list[EntityChanges]] = {item: [] for item in labels}
    for entity_id, entity in history["entities"].items():
        fields_by_item: dict[str | None, list[str]] = {}
        for use in entity["uses"]:
            fields_by_item.setdefault(use["item"], []).append(use["field"])
        for item, fields in fields_by_item.items():
            rows.setdefault(item, []).append(entity_changes(entity_id, tuple(fields), entity["states"]))
    return HistoryChanges(
        datetime.fromisoformat(history["start"]),
        datetime.fromisoformat(history["end"]),
        tuple(ItemChanges(labels.get(item) or f"Removed item {item}", tuple(entities)) for item, entities in rows.items()),
    )


def entity_changes(entity_id: str, fields: tuple[str, ...], states: Sequence[Mapping[str, Any]]) -> EntityChanges:
    values: list[tuple[datetime, str]] = []
    lost_values = 0
    had_value = False
    attribute_changes: Counter[str] = Counter()
    previous_attributes: Mapping[str, Any] | None = None
    for record in states:
        state = record["state"]
        if state in ("unavailable", "unknown", None):
            lost_values += had_value
            had_value = False
            continue
        had_value = True
        values.append((datetime.fromisoformat(record["time"]), state))
        attributes = record.get("attributes")
        if attributes is not None and previous_attributes is not None:
            attribute_changes.update(key for key in attributes.keys() | previous_attributes.keys() if attributes.get(key) != previous_attributes.get(key))
        previous_attributes = attributes if attributes is not None else previous_attributes
    changes = [(time, before, after) for (_, before), (time, after) in pairwise(values) if after != before]
    numeric = bool(values) and _all_numbers([state for _, state in values])
    directions = [float(after) > float(before) for _, before, after in changes] if numeric else []
    return EntityChanges(
        entity_id=entity_id,
        fields=fields,
        recorded=bool(states),
        changes=len(changes),
        increases=sum(directions) if numeric else None,
        decreases=len(directions) - sum(directions) if numeric else None,
        reversals=sum(1 for before, after in pairwise(directions) if after != before) if numeric else None,
        changes_to=None if numeric else dict(Counter(after for _, _, after in changes)),
        shortest_hold=min((after[0] - before[0] for before, after in pairwise(changes)), default=None),
        busiest_hour=_busiest_hour([time for time, _, _ in changes]),
        lost_values=lost_values,
        attribute_changes=dict(attribute_changes),
    )


def _all_numbers(states: list[str]) -> bool:
    try:
        for state in states:
            float(state)
    except ValueError:
        return False
    return True


def _busiest_hour(times: list[datetime]) -> tuple[datetime, int] | None:
    """Return the clock hour with the most changes, the first of them on a tie."""
    per_hour = Counter(time.replace(minute=0, second=0, microsecond=0) for time in times)
    return max(per_hour.items(), key=lambda hour_count: (hour_count[1], -hour_count[0].timestamp()), default=None)
