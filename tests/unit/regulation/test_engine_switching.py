"""Scenario tests for turning appliances on and off (REG-003 to REG-009, REG-016)."""

from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import DecisionInput

from .configs import appliance, make_config
from .scenario import START, Scenario, off, on


def no_waiting(*appliances, **settings):
    return make_config(*appliances, wait_at_limit_min=0, **settings)


def test_engine_is_stopped_until_started() -> None:
    engine = RegulationEngine(no_waiting("a"))

    assert not engine.running
    assert engine.started_at is None
    assert engine.decide(DecisionInput(START, 0.0, 0.0, (0.0,), True, False)) == []


def test_start_turns_off_every_appliance_once() -> None:
    """REG-009: everything is turned off, an appliance with variants only once."""
    scenario = Scenario(no_waiting(appliance("a", variants=("morning",)), "b"))

    assert scenario.start_commands == off("a", "b")
    assert scenario.engine.running
    assert scenario.engine.started_at == START


def test_no_decision_before_there_is_an_average() -> None:
    """T2: nothing is turned on before there is a regulation average."""
    scenario = Scenario(no_waiting("a"))

    assert scenario.decide(None) == []


def test_appliances_are_turned_on_one_per_decision_in_priority_order() -> None:
    """REG-004, REG-007: one appliance per decision, highest priority first."""
    scenario = Scenario(no_waiting("a", "b", "c"))

    assert scenario.decide_many(2.0, 4) == [on("a"), on("b"), on("c"), []]
    assert scenario.engine.appliances_on == {"a", "b", "c"}


def test_nothing_is_turned_on_at_or_above_the_limit() -> None:
    """REG-006: the regulation average must be under the limit."""
    scenario = Scenario(no_waiting("a"))

    assert scenario.decide(10.0) == []
    assert scenario.decide(9.99) == on("a")


def test_power_reserve_must_fit_under_the_limit() -> None:
    """REG-006: average plus reserve must be at most the limit."""
    scenario = Scenario(no_waiting(appliance("a", reserve=2.5)))

    assert scenario.decide(7.6) == []
    assert scenario.decide(7.5) == on("a")


def test_lower_priority_waits_for_higher_priority() -> None:
    """REG-007: an appliance is not turned on before those above it are on."""
    scenario = Scenario(no_waiting(appliance("a", reserve=4.0), "b"))

    assert scenario.decide_many(7.0, 2) == [[], []]
    assert scenario.decide(6.0) == on("a")
    assert scenario.decide(7.0) == on("b")


def test_lowest_priority_is_switched_off_above_the_limit() -> None:
    """REG-008: one appliance per decision, lowest priority first, no waiting."""
    scenario = Scenario(no_waiting("a", "b", "c"))
    scenario.turn_on("a", "b", "c")

    assert scenario.decide_many(10.5, 4) == [off("c"), off("b"), off("a"), []]
    assert scenario.engine.appliances_on == set()


def test_nothing_changes_at_the_limit() -> None:
    """At the limit, nothing is turned on (REG-006) or off (REG-008)."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")

    assert scenario.decide(10.0) == []
    assert scenario.engine.appliances_on == {"a"}


def test_appliance_switched_off_is_turned_on_again() -> None:
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")

    assert scenario.decide(11.0) == off("b")
    assert scenario.decide(8.0) == on("b")


def test_ev_charging_entry_takes_no_slot_yet() -> None:
    scenario = Scenario(no_waiting("a", "b", priority=("a", "ev", "b")))

    assert scenario.decide_many(1.0, 2) == [on("a"), on("b")]


def test_stop_turns_off_everything_and_makes_no_decisions() -> None:
    """REG-016: all appliances off, no decisions while stopped."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")

    assert scenario.engine.stop() == off("a", "b")
    assert not scenario.engine.running
    assert scenario.engine.appliances_on == set()
    assert scenario.decide(1.0) == []


def test_start_begins_with_a_new_state() -> None:
    """GEN-007, REG-009: a restart forgets which appliances were on."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    later = scenario.now

    assert scenario.engine.start(later) == off("a", "b")
    assert scenario.engine.appliances_on == set()
    assert scenario.engine.started_at == later
    assert scenario.decide(1.0) == on("a")
