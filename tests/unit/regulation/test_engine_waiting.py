"""Scenario tests for the waiting time before turning on (REG-012, REG-013)."""

from datetime import timedelta

from custom_components.kraftvakt.regulation.model import ApplianceSlotKey, Waiting

from .configs import appliance, make_config
from .scenario import Scenario, off, on


def test_appliance_is_turned_on_after_the_waiting_time() -> None:
    """REG-012: 5 kW gives 2.5 minutes, so on at the decision 3 minutes later."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide(5.0) == []
    started = scenario.now
    assert scenario.engine.waiting == Waiting(ApplianceSlotKey("a"), started)
    assert scenario.decide_many(5.0, 3) == [[], [], on("a")]
    assert scenario.now - started == timedelta(minutes=3)
    assert scenario.engine.waiting is None


def test_no_waiting_time_turns_on_at_the_same_decision() -> None:
    """REG-012: a waiting time of 0 turns the appliance on at once."""
    scenario = Scenario(make_config("a", "b", wait_at_limit_min=0))

    assert scenario.decide(9.0) == on("a")


def test_zero_average_gives_no_waiting_time() -> None:
    """REG-013: an average of 0 gives no waiting time."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide(0.0) == on("a")


def test_waiting_time_is_calculated_again_at_each_decision() -> None:
    """REG-013: the waiting time follows the average at each decision."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide(9.9) == []
    assert scenario.decide(9.9) == []
    assert scenario.decide(2.0) == on("a")


def test_waiting_time_close_to_the_limit() -> None:
    """REG-013: 9.5 kW of 10 kW gives 4.75 minutes, so on 5 minutes later."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide_many(9.5, 6) == [[], [], [], [], [], on("a")]


def test_waiting_time_is_cancelled_when_conditions_fail() -> None:
    """REG-012: a new waiting time starts when the appliance can be turned on again."""
    scenario = Scenario(make_config(appliance("a", reserve=2.0)))

    assert scenario.decide_many(5.0, 2) == [[], []]
    assert scenario.decide(8.5) == []
    assert scenario.engine.waiting is None
    assert scenario.decide_many(5.0, 3) == [[], [], []]
    assert scenario.decide(5.0) == on("a")


def test_waiting_time_is_cancelled_at_the_limit() -> None:
    scenario = Scenario(make_config("a"))

    assert scenario.decide(5.0) == []
    assert scenario.decide(10.0) == []
    assert scenario.engine.waiting is None


def test_switching_off_cancels_the_waiting_time() -> None:
    """REG-008: switching off happens without waiting and ends a waiting time."""
    scenario = Scenario(make_config("a", "b"))
    scenario.turn_on("a")

    assert scenario.decide(5.0) == []
    assert scenario.engine.waiting is not None
    assert scenario.decide(10.5) == off("a")
    assert scenario.engine.waiting is None
