"""What the panel's diagnostics page shows of what the diagnostics hold."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.util import dt as dt_util

from .json_values import plain
from .runtime import KraftvaktRuntime


class DiagnosticsFeed:
    """Makes the events of one subscription of the diagnostics page.

    The measurements and the decisions are sent in parts, since they cover up
    to an hour. A part holds every item kept, or only those after the last
    sent. The last two measurements are sent again, since a new measurement at
    the same time replaces the last one, and may merge it into the one before.
    The panel replaces what it holds from the first item of a part, and forgets
    what is older than the first item kept.
    """

    def __init__(self) -> None:
        self._runtime: KraftvaktRuntime | None = None
        self._first_measurement: datetime | None = None
        self._last_measurement: datetime | None = None
        self._last_decision: datetime | None = None

    def event(self, runtime: KraftvaktRuntime) -> dict[str, Any]:
        replace = runtime is not self._runtime
        if replace:
            self._runtime = runtime
            self._first_measurement = self._last_measurement = self._last_decision = None
        change = runtime.interval_change
        return {
            "started_at": plain(runtime.started_at),
            "power_sensor": {
                "valid": runtime.power_sensor_valid,
                "update_interval_s": plain(runtime.update_interval),
                "reported_interval_s": None if change is None else plain(change.reported_interval),
                "last_missed_windows": plain(runtime.last_missed_windows),
            },
            "queued_commands": runtime.queued_commands,
            "repeats_due_at": plain(runtime.repeats_due_at()),
            "measurements": self._measurements_part(runtime.power_measurements, replace),
            "decisions": self._decisions_part(runtime.recent_decisions, replace),
            "failed_actions": runtime.failed_actions,
        }

    def _measurements_part(self, measurements: list[tuple[datetime, float]], replace: bool) -> dict[str, Any]:
        """Return the measurements from the last one sent, or all when history from the recorder has been added before the first one sent."""
        first = measurements[0][0] if measurements else None
        if first is not None and self._first_measurement is not None and first < self._first_measurement:
            replace = True
        last = None if replace else self._last_measurement
        if measurements:
            if self._first_measurement is None or replace:
                self._first_measurement = first
            self._last_measurement = measurements[max(len(measurements) - 2, 0)][0]
        sent = [{"start": plain(start), "power_w": power_w} for start, power_w in measurements if last is None or start >= last]
        return _part(replace, first, sent)

    def _decisions_part(self, decisions: list[dict[str, Any]], replace: bool) -> dict[str, Any]:
        last = self._last_decision
        sent = [decision for decision in decisions if last is None or _time(decision) > last]
        if sent:
            self._last_decision = _time(sent[-1])
        return _part(replace, _time(decisions[0]) if decisions else None, sent)


def _part(replace: bool, kept_from: datetime | None, items: list[Any]) -> dict[str, Any]:
    return {"replace": replace, "kept_from": plain(kept_from), "items": items}


def _time(decision: dict[str, Any]) -> datetime:
    """Return the time of a decision record, kept as JSON."""
    return dt_util.parse_datetime(decision["time"], raise_on_error=True)
