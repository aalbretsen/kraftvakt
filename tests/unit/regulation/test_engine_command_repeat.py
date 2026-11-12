"""Scenario tests for repeating the command for the current state."""

from datetime import timedelta

from .configs import appliance, charger, make_config
from .scenario import (
    DECISION_INTERVAL,
    Scenario,
    activate,
    current,
    deactivate,
    off,
    on,
)

REPEAT_INTERVAL = timedelta(minutes=30)


def test_command_is_repeated_when_the_interval_has_passed() -> None:
    """Every start turns everything off, so the interval counts from the start."""
    scenario = Scenario(make_config("a", "b", chargers=(charger("c"),)))

    assert scenario.repeat(REPEAT_INTERVAL - timedelta(seconds=1)) == []
    assert scenario.repeat(timedelta(seconds=1)) == off("a", "b") + deactivate("c")
    assert scenario.repeat(REPEAT_INTERVAL - timedelta(seconds=1)) == []


def test_a_command_starts_the_interval_again() -> None:
    """A gets its command again 30 minutes after it was turned on, as its
    current variant does it."""
    scenario = Scenario(
        make_config(
            appliance("a", variants=("morning",)),
            "b",
            priority=("a:morning", "a", "b"),
            wait_at_limit_s=0,
        )
    )
    assert scenario.decide(9000, true=("morning",)) == on("a:morning")
    assert scenario.decide(9950, true=("morning",)) == []

    assert scenario.repeat(REPEAT_INTERVAL - 2 * DECISION_INTERVAL) == off("b")
    assert scenario.repeat(DECISION_INTERVAL) == on("a:morning")


def test_repeat_leaves_the_waiting_alone() -> None:
    """A repeat is not a switch, so the waiting time goes on."""
    scenario = Scenario(make_config("a", "b"))
    scenario.decide(9000)
    waiting = scenario.engine.waiting
    assert waiting is not None

    assert scenario.repeat(REPEAT_INTERVAL) == off("a", "b")
    assert scenario.engine.waiting == waiting


def test_charger_gets_its_current_while_activated_and_off_while_deactivated() -> None:
    """C1 charges at 8 A, and C2 waits since only one may charge at a time."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c1", max_a=8), charger("c2", max_a=8)),
            wait_at_limit_s=0,
        )
    )
    scenario.set_charger("c1", actively_charging=True)
    assert scenario.decide(2000) == activate("c1")
    scenario.charge("c1", 8, average_w=2000)

    assert scenario.repeat(REPEAT_INTERVAL - 2 * DECISION_INTERVAL) == deactivate("c2")
    assert scenario.repeat(2 * DECISION_INTERVAL) == current("c1", 8)


def test_excluded_appliances_and_chargers_are_left_alone() -> None:
    scenario = Scenario(make_config("a", "b", chargers=(charger("c1"), charger("c2"))))
    scenario.exclude("a")
    scenario.set_charger("c1", excluded=True)

    assert scenario.repeat(REPEAT_INTERVAL) == off("b") + deactivate("c2")


def test_safe_state_repeats_off() -> None:
    scenario = Scenario(make_config("a", wait_at_limit_s=0))
    scenario.turn_on("a")
    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == off("a")

    assert scenario.repeat(REPEAT_INTERVAL) == off("a")


def test_nothing_is_repeated_while_stopped() -> None:
    scenario = Scenario(make_config("a", chargers=(charger("c"),)))
    scenario.engine.stop()

    assert scenario.repeat(REPEAT_INTERVAL) == []
