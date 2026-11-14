"""Unit tests of when the decisions are made."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.decision_clock import DecisionClock, first_decision_from
from custom_components.kraftvakt.measurement import WindowAverages

NEXT = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
INTERVAL = timedelta(seconds=60)
WINDOW = timedelta(seconds=10)


@pytest.mark.parametrize(
    ("moment", "decision"),
    [
        (NEXT - timedelta(seconds=10), NEXT),
        (NEXT, NEXT),
        (NEXT + timedelta(seconds=1), NEXT + INTERVAL),
        (NEXT + INTERVAL, NEXT + INTERVAL),
        (NEXT + timedelta(seconds=150), NEXT + 3 * INTERVAL),
    ],
)
def test_first_decision_from_a_moment(moment: datetime, decision: datetime) -> None:
    assert first_decision_from(moment, NEXT, INTERVAL) == decision


def window(start: datetime) -> WindowAverages:
    return WindowAverages(start, start + WINDOW, 1000, 1000, sensor_valid=True)


def test_windows_that_started_before_the_start_do_not_count() -> None:
    started_at = NEXT + timedelta(seconds=5)
    clock = DecisionClock()

    clock.add(window(NEXT))
    assert not clock.is_due(started_at, 1)
    assert clock.next_decision_at(started_at, 1, NEXT + WINDOW, NEXT + 2 * WINDOW, WINDOW) == NEXT + 2 * WINDOW

    clock.add(window(NEXT + WINDOW))
    assert clock.is_due(started_at, 1)
    assert len(clock.take_windows()) == 2
    assert not clock.is_due(started_at, 1)


def test_next_decision_counts_the_running_window_and_those_left() -> None:
    clock = DecisionClock()
    clock.add(window(NEXT))

    assert clock.next_decision_at(NEXT, 3, NEXT + WINDOW, NEXT + 2 * WINDOW, WINDOW) == NEXT + 3 * WINDOW
    clock.restart()
    assert clock.next_decision_at(NEXT, 3, NEXT + WINDOW, NEXT + 2 * WINDOW, WINDOW) == NEXT + 4 * WINDOW
    assert not clock.is_due(None, 1)
