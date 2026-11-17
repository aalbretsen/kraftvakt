"""Scenario tests for essential appliances, which only a penalty turns off."""

from datetime import timedelta

from .configs import appliance, make_config
from .scenario import Scenario, off, on
from .test_engine_penalty import ABOVE_THRESHOLD, start_penalty


def essential_first(*appliances: str):
    """Return a configuration with the essential appliance «e» at the top, without waiting times."""
    return make_config(appliance("e", essential=True), *appliances, wait_at_limit_s=0)


def test_start_turns_the_essential_appliance_on() -> None:
    scenario = Scenario(essential_first("a"))

    assert scenario.start_commands == on("e") + off("a")
    assert scenario.engine.appliances_on == {"e"}
    assert scenario.engine.steps_on == 0


def test_essential_appliance_is_never_switched_off_above_the_limit() -> None:
    """It is no step: the lowest step that is on is switched off, and nothing when no step is on."""
    scenario = Scenario(essential_first("a"))
    scenario.turn_on("a")

    assert scenario.decide(10_500) == off("a")
    assert scenario.decide(10_500) == []
    assert scenario.engine.appliances_on == {"e"}


def test_penalty_turns_the_essential_appliance_off_until_it_ends() -> None:
    """The start when the penalty is paid back turns it on again."""
    scenario = Scenario(essential_first("a"))

    assert start_penalty(scenario) == off("e", "a")
    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD) == []
    assert scenario.engine.appliances_on == set()

    assert scenario.decide(0, tariff=ABOVE_THRESHOLD) == on("e") + off("a")
    assert not scenario.engine.penalty.active


def test_safe_state_keeps_the_essential_appliance_on() -> None:
    scenario = Scenario(essential_first("a"))
    scenario.turn_on("a")

    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == on("e") + off("a")
    assert scenario.engine.appliances_on == {"e"}


def test_stop_turns_the_essential_appliance_on() -> None:
    """Also when it was turned off by a penalty."""
    scenario = Scenario(essential_first("a"))
    start_penalty(scenario)

    assert scenario.engine.stop() == on("e") + off("a")


def test_excluded_essential_appliance_is_turned_off_and_on_again_when_included() -> None:
    """Turning it on again is no step, so the next step is still turned on at the same decision."""
    scenario = Scenario(essential_first("a"))
    scenario.exclude("e")

    assert scenario.decide(10_500) == off("e")
    scenario.exclude()
    assert scenario.decide(5000) == on("e") + on("a")


def test_excluding_the_essential_appliance_above_the_limit_switches_off_nothing_more() -> None:
    """The average was measured before it was switched off."""
    scenario = Scenario(essential_first("a"))
    scenario.turn_on("a")
    scenario.exclude("e")

    assert scenario.decide(10_500) == off("e")
    assert scenario.engine.appliances_on == {"a"}


def test_essential_appliance_excluded_at_start_is_turned_off() -> None:
    scenario = Scenario(essential_first("a"), excluded=("e",))

    assert scenario.start_commands == off("e", "a")
    assert scenario.decide(5000) == on("a")


def test_essential_appliance_included_during_a_penalty_stays_off() -> None:
    scenario = Scenario(essential_first("a"), excluded=("e",))
    start_penalty(scenario)
    scenario.exclude()

    assert scenario.decide(5000, tariff=ABOVE_THRESHOLD) == []


def test_essential_appliance_gets_its_turn_on_repeated() -> None:
    scenario = Scenario(essential_first("a"))

    assert scenario.repeat(timedelta(minutes=30)) == on("e") + off("a")
