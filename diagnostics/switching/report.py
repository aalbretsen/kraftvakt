"""The changes of the recorded history as a text report, with a table per appliance and EV charger, and the changes to each state and attribute under their entity."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta

from .changes import EntityChanges, HistoryChanges

COLUMNS: dict[str, Callable[[EntityChanges], str]] = {
    "entity": lambda entity: entity.entity_id,
    "fields": lambda entity: ", ".join(entity.fields),
    "changes": lambda entity: str(entity.changes),
    "up": lambda entity: _count(entity.increases),
    "down": lambda entity: _count(entity.decreases),
    "reversals": lambda entity: _count(entity.reversals),
    "shortest hold": lambda entity: _duration(entity.shortest_hold),
    "busiest hour": lambda entity: _hour(entity.busiest_hour),
    "lost values": lambda entity: str(entity.lost_values),
}


def report_text(history: HistoryChanges) -> str:
    lines = [f"Recorded history from {_time(history.start)} to {_time(history.end)}"]
    for item in history.items:
        rows = [list(COLUMNS), *([value(entity) for value in COLUMNS.values()] for entity in item.entities)]
        widths = [max(len(row[column]) for row in rows) for column in range(len(COLUMNS))]
        lines += ["", item.label]
        for row, entity in zip(rows, [None, *item.entities], strict=True):
            lines.append("  " + "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip())
            if entity is not None and not entity.recorded:
                lines.append("    no recorded states: the recorder leaves it out, or it did not exist")
            if entity is not None and entity.changes_to:
                lines.append(f"    changes to: {_counts(entity.changes_to)}")
            if entity is not None and entity.attribute_changes:
                lines.append(f"    attributes changed: {_counts(entity.attribute_changes)}")
    return "\n".join(lines) + "\n"


def _count(count: int | None) -> str:
    return "-" if count is None else str(count)


def _counts(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{key} {count}" for key, count in sorted(counts.items(), key=lambda key_count: -key_count[1]))


def _duration(duration: timedelta | None) -> str:
    return "-" if duration is None else f"{duration.total_seconds():.0f} s"


def _hour(busiest_hour: tuple[datetime, int] | None) -> str:
    return "-" if busiest_hour is None else f"{busiest_hour[0]:%Y-%m-%d %H}:00 ({busiest_hour[1]})"


def _time(time: datetime) -> str:
    return f"{time:%Y-%m-%d %H:%M}"
