"""Unit tests of what the diagnostics page gets after the first event."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from homeassistant.util import dt as dt_util

from custom_components.kraftvakt.diagnostics_feed import DiagnosticsFeed
from custom_components.kraftvakt.power_measurement import WindowCloses
from custom_components.kraftvakt.regulation.model import RepeatsDue
from custom_components.kraftvakt.report_analysis import ReportAnalysis

START = datetime(2026, 1, 5, 12, tzinfo=UTC)


def runtime(measurements: list[tuple[datetime, float]]) -> Any:
    return SimpleNamespace(
        started_at=START,
        power_sensor_valid=True,
        last_power_update_at=START,
        last_missed_windows=None,
        power_report_analysis=lambda: ReportAnalysis(2, None, False, timedelta(seconds=10), timedelta(seconds=10), 0),
        window_closes=lambda: WindowCloses(1, 0),
        queued_commands=0,
        repeats_due_at=lambda: RepeatsDue({}, {}),
        power_measurements=measurements,
        recent_decisions=[],
        commands_before_decisions=None,
        failed_actions=[],
    )


def starts(event: dict[str, Any]) -> list[str]:
    return [item["start"] for item in event["measurements"]["items"]]


def local(minutes: int) -> str:
    return dt_util.as_local(START + timedelta(minutes=minutes)).isoformat()


def test_history_added_before_the_first_measurement_sent_replaces_the_measurements() -> None:
    """The hour before is read from the recorder after the first measurement, so the page may open before it is there."""
    feed = DiagnosticsFeed()
    held = runtime([(START, 1000.0)])
    assert feed.event(held)["measurements"]["replace"]

    held.power_measurements = [(START - timedelta(minutes=30), 2000.0), (START, 1000.0)]
    event = feed.event(held)

    assert event["measurements"]["replace"]
    assert starts(event) == [local(-30), local(0)]


def test_the_measurement_before_the_last_one_sent_is_sent_again() -> None:
    """A new measurement at the time of the last one replaces it, and merges it into the one before when it has the same power."""
    feed = DiagnosticsFeed()
    held = runtime([(START, 1000.0), (START + timedelta(minutes=1), 2000.0)])
    feed.event(held)

    held.power_measurements = [(START, 1000.0)]
    event = feed.event(held)

    assert not event["measurements"]["replace"]
    assert starts(event) == [local(0)]


def test_nothing_is_sent_before_the_first_measurement() -> None:
    feed = DiagnosticsFeed()
    held = runtime([])

    event = feed.event(held)

    assert event["measurements"] == {"replace": True, "kept_from": None, "items": []}
    held.power_measurements = [(START, 1000.0)]
    assert starts(feed.event(held)) == [local(0)]
