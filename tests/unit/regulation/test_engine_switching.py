"""Scenario tests for turning appliances on and off."""

from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import DecisionInput

from .configs import appliance, make_config
from .scenario import START, Scenario, off, on


def no_waiting(*appliances, **settings):
    return make_config(*appliances, wait_at_limit_s=0, **settings)


def test_engine_is_stopped_until_started() -> None:
    engine = RegulationEngine(no_waiting("a"))

    assert not engine.running
    assert engine.started_at is None
    assert engine.decide(DecisionInput(START, 0.0, 0.0, (0.0,), True, False)) == []


def test_start_turns_off_every_appliance_once() -> None:
    """Everything is turned off, an appliance with variants only once."""
    scenario = Scenario(no_waiting(appliance("a", variants=("morning",)), "b"))

    assert scenario.start_commands == off("a", "b")
    assert scenario.engine.running
    assert scenario.engine.started_at == START


def test_no_decision_before_there_is_an_average() -> None:
    """Nothing is turned on before there is a regulation average."""
    scenario = Scenario(no_waiting("a"))

    assert scenario.decide(None) == []


def test_appliances_are_turned_on_one_per_decision_in_priority_order() -> None:
    """One appliance per decision, highest priority first."""
    scenario = Scenario(no_waiting("a", "b", "c"))

    assert scenario.decide_many(2.0, 4) == [on("a"), on("b"), on("c"), []]
    assert scenario.engine.appliances_on == {"a", "b", "c"}


def test_nothing_is_turned_on_within_the_turn_on_margin() -> None:
    """The regulation average must be under the limit minus the margin,
    by default 0.1 kW."""
    scenario = Scenario(no_waiting("a"))

    assert scenario.decide(10.0) == []
    assert scenario.decide(9.9) == []
    assert scenario.decide(9.89) == on("a")


def test_average_just_below_the_limit_after_a_turn_on_turns_on_nothing() -> None:
    """Found in the exploratory test: the window after a turn-on held a few
    milliseconds of the consumption before it, 7.9993 kW of 8 kW, and the next
    appliance was turned on only to be switched off again."""
    scenario = Scenario(no_waiting("a", "b", "c", limit_kw=8.0))
    assert scenario.decide_many(4.5, 2) == [on("a"), on("b")]

    assert scenario.decide_many(7.9993, 3) == [[], [], []]
    assert scenario.decide(8.0) == []


def test_power_reserve_must_fit_under_the_limit() -> None:
    """Average plus reserve must be at most the limit."""
    scenario = Scenario(no_waiting(appliance("a", reserve=2.5)))

    assert scenario.decide(7.6) == []
    assert scenario.decide(7.5) == on("a")


def test_lower_priority_waits_for_higher_priority() -> None:
    """An appliance is not turned on before those above it are on."""
    scenario = Scenario(no_waiting(appliance("a", reserve=4.0), "b"))

    assert scenario.decide_many(7.0, 2) == [[], []]
    assert scenario.decide(6.0) == on("a")
    assert scenario.decide(7.0) == on("b")


def test_lowest_priority_is_switched_off_above_the_limit() -> None:
    """One appliance per decision, lowest priority first, no waiting."""
    scenario = Scenario(no_waiting("a", "b", "c"))
    scenario.turn_on("a", "b", "c")

    assert scenario.decide_many(10.5, 4) == [off("c"), off("b"), off("a"), []]
    assert scenario.engine.appliances_on == set()


def test_nothing_changes_at_the_limit() -> None:
    """At the limit, nothing is turned on or off."""
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
    """All appliances off, no decisions while stopped."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")

    assert scenario.engine.stop() == off("a", "b")
    assert not scenario.engine.running
    assert scenario.engine.appliances_on == set()
    assert scenario.decide(1.0) == []


def test_start_begins_with_a_new_state() -> None:
    """A restart forgets which appliances were on."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a", "b")
    later = scenario.now

    assert scenario.engine.start(later) == off("a", "b")
    assert scenario.engine.appliances_on == set()
    assert scenario.engine.started_at == later
    assert scenario.decide(1.0) == on("a")
