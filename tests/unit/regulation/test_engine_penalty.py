"""Scenario tests for overconsumption and penalty in the engine."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import DecisionInput
from custom_components.kraftvakt.regulation.penalty import PenaltyState

from .configs import appliance, make_config
from .scenario import START, Scenario, off, on

ABOVE_THRESHOLD = 11_500
WH_PER_W_WINDOW = 1 / 60


def no_waiting(*appliances, **settings):
    return make_config(*appliances, wait_at_limit_s=0, **settings)


def start_penalty(scenario: Scenario, average_w: float = 16_000) -> list:
    """Start the overconsumption state, then the penalty, and return its commands.

    The average equals the limit at the first decision, so the ordinary
    regulation leaves everything as it is.
    """
    assert scenario.decide(10000, tariff=ABOVE_THRESHOLD) == []
    commands = scenario.decide(average_w, tariff=ABOVE_THRESHOLD)
    assert scenario.engine.penalty.active
    return commands


def test_penalty_turns_everything_off_at_once() -> None:
    """Every appliance in the configuration, at one decision."""
    scenario = Scenario(no_waiting("a", "b", "c"))
    scenario.turn_on("a", "b")

    assert start_penalty(scenario) == off("a", "b", "c")

    assert scenario.engine.appliances_on == set()
    assert scenario.engine.waiting is None
    assert scenario.engine.penalty.overconsumption_wh == pytest.approx(6000 * WH_PER_W_WINDOW)


def test_nothing_is_turned_on_during_the_penalty() -> None:
    """No appliance is turned on while the penalty lasts."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")
    start_penalty(scenario)

    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD) == []
    assert scenario.decide(9500, tariff=2000) == []
    assert scenario.engine.penalty.active


def test_penalty_ends_with_a_restart_when_paid_back() -> None:
    """The regulation starts again with everything off when paid back."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    start_penalty(scenario)
    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD) == []

    assert scenario.decide(9000, tariff=ABOVE_THRESHOLD) == off("a", "b")

    assert scenario.engine.started_at == scenario.now
    assert scenario.engine.penalty == PenaltyState()


def test_appliances_come_back_one_by_one_after_the_penalty() -> None:
    """A new overconsumption state starts at 0, without penalty."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    start_penalty(scenario, average_w=11000)
    assert scenario.decide(9000, tariff=ABOVE_THRESHOLD) == off("a", "b")

    assert scenario.decide(1000, tariff=ABOVE_THRESHOLD) == on("a")
    assert scenario.engine.penalty.overconsuming
    assert scenario.decide(2000, tariff=ABOVE_THRESHOLD) == on("b")
    assert not scenario.engine.penalty.active


def test_restart_after_the_penalty_waits_again() -> None:
    """After the restart, appliances wait before turning on."""
    scenario = Scenario(make_config("a"))
    scenario.turn_on("a")
    start_penalty(scenario, average_w=11000)
    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD) == off("a")

    assert scenario.decide_many(8000, 5) == [[], [], [], [], on("a")]


def test_no_penalty_when_overconsumption_is_paid_back() -> None:
    """The ordinary regulation goes on when nothing is left to pay back."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    assert scenario.decide(10000, tariff=ABOVE_THRESHOLD) == []

    assert scenario.decide(10500, tariff=ABOVE_THRESHOLD, averages=(6000, 10500)) == off("b")

    assert not scenario.engine.penalty.active


def test_no_penalty_at_or_under_limit_plus_threshold() -> None:
    """Overconsumption grows, but the regulation goes on."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")

    assert scenario.decide_many(12000, 3, tariff=11000) == [off("b"), off("a"), []]

    assert not scenario.engine.penalty.active
    assert scenario.engine.penalty.overconsumption_wh == pytest.approx(4000 * WH_PER_W_WINDOW)


def test_zero_threshold_gives_penalty_one_decision_later() -> None:
    scenario = Scenario(no_waiting("a", threshold_w=0))
    scenario.turn_on("a")

    assert scenario.decide(10000, tariff=10010) == []
    assert scenario.decide(10000, tariff=10010, averages=(10500, 10000)) == off("a")
    assert scenario.engine.penalty.active


def test_status_shows_the_recovery() -> None:
    """What is left and whether recovery has started."""
    scenario = Scenario(no_waiting("a"))
    start_penalty(scenario)

    scenario.decide(12000, tariff=ABOVE_THRESHOLD)
    assert not scenario.engine.penalty.recovery_started
    scenario.decide(9000, tariff=ABOVE_THRESHOLD)
    assert scenario.engine.penalty.recovery_started
    scenario.decide(11000, tariff=ABOVE_THRESHOLD)

    penalty = scenario.engine.penalty
    assert penalty.recovery_started
    assert penalty.overconsumption_wh == pytest.approx(8000 * WH_PER_W_WINDOW)


def test_stop_and_start_end_the_penalty() -> None:
    """A restart forgets the overconsumption and the penalty."""
    scenario = Scenario(no_waiting("a"))
    start_penalty(scenario)

    assert scenario.engine.stop() == off("a")
    assert scenario.engine.penalty == PenaltyState()
    scenario.engine.start(scenario.now)

    assert scenario.decide(1000) == on("a")


def test_current_variant_is_found_during_the_penalty() -> None:
    """The current variant is found at each decision, also in a penalty, and
    a switch gives the turn-off action of the new variant."""
    scenario = Scenario(
        no_waiting(
            appliance("heater", variants=("morning",)),
            "b",
            priority=("heater:morning", "b", "heater"),
        )
    )
    scenario.turn_on("b", "heater")
    start_penalty(scenario)

    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD, true=("morning",)) == off("heater:morning")
    assert scenario.engine.current_variants == {"heater": "morning", "b": None}


def test_no_penalty_without_a_tariff_average() -> None:
    """Overconsumption is only counted from a tariff average."""
    engine = RegulationEngine(no_waiting("a"))
    engine.start(START)

    commands = engine.decide(DecisionInput(START + timedelta(minutes=1), 5.0, None, (5.0,), True, False)).commands

    assert commands == on("a")
    assert engine.penalty == PenaltyState()
