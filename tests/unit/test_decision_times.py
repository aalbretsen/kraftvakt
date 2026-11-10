"""Unit tests of when the decision that ends a waiting time comes."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.runtime import first_decision_from

NEXT = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)
INTERVAL = timedelta(seconds=60)


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
