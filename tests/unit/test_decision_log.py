from datetime import UTC, datetime, timedelta

from custom_components.kraftvakt.decision_log import DecisionLog
from custom_components.kraftvakt.regulation.model import TurnOffAppliance, TurnOnAppliance

T0 = datetime(2026, 1, 5, 12, tzinfo=UTC)


def at(minutes: int) -> datetime:
    return T0 + timedelta(minutes=minutes)


def test_nothing_is_known_before_the_first_start() -> None:
    assert DecisionLog().commands_before is None


def test_a_decision_from_before_the_last_start_leaves_the_hour_without_changing_the_commands_before() -> None:
    log = DecisionLog()
    log.start(at(0), [TurnOffAppliance("a", None)])
    log.add(at(1), [TurnOnAppliance("a", None)], {"time": "1"})
    log.start(at(2), [TurnOffAppliance("a", None)])

    log.add(at(61), [], {"time": "61"})

    assert log.records == [{"time": "61"}]
    assert log.commands_before is not None
    assert log.commands_before["commands"] == [{"command": "TurnOffAppliance", "appliance_id": "a", "variant_id": None}]
