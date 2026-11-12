"""Scenario tests for appliances the user excludes from the regulation."""

from custom_components.kraftvakt.regulation.model import ApplianceStepKey

from .configs import appliance, make_config
from .scenario import Scenario, off, on


def test_excluded_appliance_is_skipped() -> None:
    """The appliance below an excluded one is turned on as if it was not there."""
    scenario = Scenario(make_config("a", "b", "c", wait_at_limit_s=0))
    scenario.exclude("b")

    assert scenario.decide_many(1000, 3) == [on("a"), on("c"), []]
    assert scenario.engine.excluded_appliances == {"b"}


def test_excluding_an_appliance_that_is_on_switches_it_off() -> None:
    """It is switched off at the next decision and no longer counted as on."""
    scenario = Scenario(make_config("a", "b", "c", wait_at_limit_s=0))
    scenario.turn_on("a", "b", "c")
    scenario.exclude("b")

    assert scenario.decide(5000) == off("b")
    assert scenario.engine.appliances_on == {"a", "c"}
    assert scenario.engine.steps_on == 2


def test_excluding_above_the_limit_switches_off_nothing_more() -> None:
    """The average was measured before the excluded appliance was switched off."""
    scenario = Scenario(make_config("a", "b", wait_at_limit_s=0))
    scenario.turn_on("a", "b")
    scenario.exclude("a")

    assert scenario.decide(10500) == off("a")
    assert scenario.engine.appliances_on == {"b"}


def test_included_again_above_the_lowest_on_makes_room() -> None:
    """C is switched off to give room for B, which is turned on before C."""
    scenario = Scenario(make_config("a", "b", "c", wait_at_limit_s=0))
    scenario.exclude("b")
    scenario.turn_on("a", "c")
    scenario.exclude()

    assert scenario.decide(9000) == off("c") + on("b")
    assert scenario.decide(9000) == on("c")
    assert scenario.engine.excluded_appliances == set()


def test_excluded_appliance_that_switches_variant_makes_no_room() -> None:
    """D moves above C, but is never turned on, so C stays on. D gets the
    turn-off action of its new variant."""
    scenario = Scenario(
        make_config(
            "a",
            "b",
            "c",
            appliance("d", variants=("up",)),
            priority=("a", "b", "d:up", "c", "d"),
            wait_at_limit_s=0,
        )
    )
    scenario.exclude("d")
    scenario.turn_on("a", "b", "c")

    assert scenario.decide(9000, true=("up",)) == off("d:up")
    assert scenario.engine.appliances_on == {"a", "b", "c"}


def test_waiting_moves_to_the_next_when_the_waiting_appliance_is_excluded() -> None:
    """The waiting time starts again for the appliance below."""
    scenario = Scenario(make_config("a", "b"))
    scenario.decide(9000)
    assert scenario.engine.waiting is not None
    assert scenario.engine.waiting.key == ApplianceStepKey("a")
    scenario.exclude("a")

    scenario.decide(9000)

    assert scenario.engine.waiting is not None
    assert scenario.engine.waiting.key == ApplianceStepKey("b")
    assert scenario.engine.waiting.started_at == scenario.now


def test_exclusion_is_found_at_each_decision() -> None:
    """A start forgets the excluded appliances until the first decision."""
    scenario = Scenario(make_config("a", "b"))
    scenario.exclude("a")
    scenario.decide(1000)

    scenario.engine.start(scenario.now)

    assert scenario.engine.excluded_appliances == set()


def test_exclusion_is_followed_during_a_penalty() -> None:
    """Nothing is on, so excluding and including again give no commands."""
    scenario = Scenario(make_config("a", "b", wait_at_limit_s=0, threshold_w=0))
    scenario.turn_on("a", "b")
    scenario.decide(10500, tariff=10500)
    assert scenario.decide(10500, tariff=10500) == off("a", "b")
    scenario.exclude("a")

    assert scenario.decide(10500, tariff=10500) == []
    assert scenario.engine.excluded_appliances == {"a"}
    scenario.exclude()
    assert scenario.decide(10500, tariff=10500) == []
