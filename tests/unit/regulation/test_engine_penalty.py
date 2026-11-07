"""Scenario tests for overconsumption and penalty in the engine (STR-001 to STR-009)."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import DecisionInput
from custom_components.kraftvakt.regulation.penalty import PenaltyState

from .configs import appliance, make_config
from .scenario import START, Scenario, off, on

ABOVE_THRESHOLD = 11.5
KWH_PER_KW_WINDOW = 1 / 60


def no_waiting(*appliances, **settings):
    return make_config(*appliances, wait_at_limit_min=0, **settings)


def start_penalty(scenario: Scenario, average_kw: float = 16.0) -> list:
    """Start the overconsumption state, then the penalty, and return its commands.

    The average equals the limit at the first decision, so the ordinary
    regulation leaves everything as it is.
    """
    assert scenario.decide(10.0, capacity=ABOVE_THRESHOLD) == []
    commands = scenario.decide(average_kw, capacity=ABOVE_THRESHOLD)
    assert scenario.engine.penalty.active
    return commands


def test_penalty_turns_everything_off_at_once() -> None:
    """STR-001, STR-003: every appliance in the configuration, at one decision."""
    scenario = Scenario(no_waiting("a", "b", "c"))
    scenario.turn_on("a", "b")

    assert start_penalty(scenario) == off("a", "b", "c")

    assert scenario.engine.appliances_on == set()
    assert scenario.engine.waiting is None
    assert scenario.engine.penalty.overconsumption_kwh == pytest.approx(
        6 * KWH_PER_KW_WINDOW
    )


def test_nothing_is_turned_on_during_the_penalty() -> None:
    """STR-003: no appliance is turned on while the penalty lasts."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")
    start_penalty(scenario)

    assert scenario.decide(5.0, capacity=ABOVE_THRESHOLD) == []
    assert scenario.decide(9.5, capacity=2.0) == []
    assert scenario.engine.penalty.active


def test_penalty_ends_with_a_restart_when_paid_back() -> None:
    """STR-006, STR-008: the regulation starts again by REG-009 when paid back."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    start_penalty(scenario)
    assert scenario.decide(5.0, capacity=ABOVE_THRESHOLD) == []

    assert scenario.decide(9.0, capacity=ABOVE_THRESHOLD) == off("a", "b")

    assert scenario.engine.started_at == scenario.now
    assert scenario.engine.penalty == PenaltyState()


def test_appliances_come_back_one_by_one_after_the_penalty() -> None:
    """STR-008, STR-009: a new overconsumption state starts at 0, without penalty."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    start_penalty(scenario, average_kw=11.0)
    assert scenario.decide(9.0, capacity=ABOVE_THRESHOLD) == off("a", "b")

    assert scenario.decide(1.0, capacity=ABOVE_THRESHOLD) == on("a")
    assert scenario.engine.penalty.overconsuming
    assert scenario.decide(2.0, capacity=ABOVE_THRESHOLD) == on("b")
    assert not scenario.engine.penalty.active


def test_restart_after_the_penalty_waits_again() -> None:
    """STR-008, REG-012: after the restart, appliances wait before turning on."""
    scenario = Scenario(make_config("a"))
    scenario.turn_on("a")
    start_penalty(scenario, average_kw=11.0)
    assert scenario.decide(5.0, capacity=ABOVE_THRESHOLD) == off("a")

    assert scenario.decide_many(5.0, 4) == [[], [], [], on("a")]


def test_no_penalty_when_overconsumption_is_paid_back() -> None:
    """STR-009: the ordinary regulation goes on when nothing is left to pay back."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    assert scenario.decide(10.0, capacity=ABOVE_THRESHOLD) == []

    assert scenario.decide(10.5, capacity=ABOVE_THRESHOLD, averages=(6.0, 10.5)) == off(
        "b"
    )

    assert not scenario.engine.penalty.active


def test_no_penalty_at_or_under_limit_plus_threshold() -> None:
    """STR-001, STR-002: overconsumption grows, but the regulation goes on."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")

    assert scenario.decide_many(12.0, 3, capacity=11.0) == [off("b"), off("a"), []]

    assert not scenario.engine.penalty.active
    assert scenario.engine.penalty.overconsumption_kwh == pytest.approx(
        4 * KWH_PER_KW_WINDOW
    )


def test_zero_threshold_gives_penalty_one_decision_later() -> None:
    """STR-002, T4: with threshold 0, the penalty starts one decision later."""
    scenario = Scenario(no_waiting("a", threshold_kw=0.0))
    scenario.turn_on("a")

    assert scenario.decide(10.0, capacity=10.01) == []
    assert scenario.decide(10.0, capacity=10.01, averages=(10.5, 10.0)) == off("a")
    assert scenario.engine.penalty.active


def test_status_shows_the_recovery() -> None:
    """STR-005, STR-007, T5, T11: what is left and whether recovery has started."""
    scenario = Scenario(no_waiting("a"))
    start_penalty(scenario)

    scenario.decide(12.0, capacity=ABOVE_THRESHOLD)
    assert not scenario.engine.penalty.recovery_started
    scenario.decide(9.0, capacity=ABOVE_THRESHOLD)
    assert scenario.engine.penalty.recovery_started
    scenario.decide(11.0, capacity=ABOVE_THRESHOLD)

    penalty = scenario.engine.penalty
    assert penalty.recovery_started
    assert penalty.overconsumption_kwh == pytest.approx(8 * KWH_PER_KW_WINDOW)


def test_stop_and_start_end_the_penalty() -> None:
    """STR-006, GEN-007: a restart forgets the overconsumption and the penalty."""
    scenario = Scenario(no_waiting("a"))
    start_penalty(scenario)

    assert scenario.engine.stop() == off("a")
    assert scenario.engine.penalty == PenaltyState()
    scenario.engine.start(scenario.now)

    assert scenario.decide(1.0) == on("a")


def test_current_variant_is_found_during_the_penalty() -> None:
    """APP-007: the current variant is found at each decision, also in a penalty."""
    scenario = Scenario(
        no_waiting(
            appliance("heater", variants=("morning",)),
            "b",
            priority=("heater:morning", "b", "heater"),
        )
    )
    scenario.turn_on("b", "heater")
    start_penalty(scenario)

    assert scenario.decide(5.0, capacity=ABOVE_THRESHOLD, true=("morning",)) == []
    assert scenario.engine.current_variants == {"heater": "morning", "b": None}


def test_no_penalty_without_a_capacity_average() -> None:
    """T2: overconsumption is only counted from a capacity average."""
    engine = RegulationEngine(no_waiting("a"))
    engine.start(START)

    commands = engine.decide(
        DecisionInput(START + timedelta(minutes=1), 5.0, None, (5.0,), True, False)
    )

    assert commands == on("a")
    assert engine.penalty == PenaltyState()
