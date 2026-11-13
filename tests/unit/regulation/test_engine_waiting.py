"""Scenario tests for the waiting time before turning on."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.model import ApplianceStepKey

from .configs import appliance, make_config
from .scenario import Scenario, off, on


def test_appliance_is_turned_on_after_the_waiting_time() -> None:
    """At the pivot, 80 % of 5 minutes, so on at the decision 4 minutes later."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide(8000) == []
    started = scenario.now
    waiting = scenario.engine.waiting
    assert waiting is not None
    assert (waiting.key, waiting.started_at) == (ApplianceStepKey("a"), started)
    assert waiting.until - started == pytest.approx(timedelta(minutes=4))
    assert scenario.decide_many(8000, 4) == [[], [], [], on("a")]
    assert scenario.now - started == timedelta(minutes=4)
    assert scenario.engine.waiting is None


def test_end_of_the_waiting_time_follows_the_average() -> None:
    """The end is calculated again at each decision while it runs."""
    scenario = Scenario(make_config("a"))
    scenario.decide(9000)
    started = scenario.now

    scenario.decide(8000)

    waiting = scenario.engine.waiting
    assert waiting is not None
    assert waiting.started_at == started
    assert waiting.until - started == pytest.approx(timedelta(minutes=4))


def test_no_waiting_time_turns_on_at_the_same_decision() -> None:
    scenario = Scenario(make_config("a", "b", wait_at_limit_s=0))

    assert scenario.decide(9000) == on("a")


def test_zero_average_gives_no_waiting_time() -> None:
    scenario = Scenario(make_config("a"))

    assert scenario.decide(0) == on("a")


def test_waiting_time_is_calculated_again_at_each_decision() -> None:
    scenario = Scenario(make_config("a"))

    assert scenario.decide(9800) == []
    assert scenario.decide(9800) == []
    assert scenario.decide(2000) == on("a")


def test_waiting_time_close_to_the_limit() -> None:
    """9.5 kW of 10 kW gives about 4.95 minutes, so on 5 minutes later."""
    scenario = Scenario(make_config("a"))

    assert scenario.decide_many(9500, 6) == [[], [], [], [], [], on("a")]


def test_waiting_time_is_cancelled_when_conditions_fail() -> None:
    """A new waiting time starts when the appliance can be turned on again."""
    scenario = Scenario(make_config(appliance("a", reserve_w=2000)))

    assert scenario.decide_many(7000, 2) == [[], []]
    assert scenario.decide(8500) == []
    assert scenario.engine.waiting is None
    assert scenario.decide_many(7000, 2) == [[], []]
    assert scenario.decide(7000) == on("a")


def test_waiting_time_is_cancelled_at_the_limit() -> None:
    scenario = Scenario(make_config("a"))

    assert scenario.decide(8000) == []
    assert scenario.decide(10000) == []
    assert scenario.engine.waiting is None


def test_switching_off_cancels_the_waiting_time() -> None:
    """Switching off happens without waiting and ends a waiting time."""
    scenario = Scenario(make_config("a", "b"))
    scenario.turn_on("a")

    assert scenario.decide(8000) == []
    assert scenario.engine.waiting is not None
    assert scenario.decide(10500) == off("a")
    assert scenario.engine.waiting is None
