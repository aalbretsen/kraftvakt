"""Scenario tests for the ampere damping time, with its default of 5 minutes and decisions a minute apart."""

from datetime import timedelta

from custom_components.kraftvakt.regulation.model import AmpereStepKey, Waiting

from .configs import appliance, charger, make_config
from .scenario import Scenario, activate, current, deactivate, off, on

ABOVE_LIMIT = 10_500


def test_ampere_taken_back_above_the_limit_comes_back_when_the_damping_time_has_passed() -> None:
    """The flip from a diagnostics file: a short spike takes 13 A back to 12 A, and 13 A fits again at once."""
    scenario = Scenario(make_config(chargers=(charger("c", min_current_power_w=4157),)))
    scenario.draw("c")
    scenario.charge("c", 13)
    scenario.settle()

    assert scenario.decide(10_072) == current("c", 12)
    taken_back_at = scenario.now
    assert scenario.decide_many(9179, 4) == [[], [], [], []]
    assert scenario.engine.waiting == Waiting(AmpereStepKey("c", 7), taken_back_at, taken_back_at + timedelta(minutes=5))
    assert scenario.decide(9179) == current("c", 13)
    assert scenario.engine.waiting is None


def test_steps_below_wait_while_an_ampere_is_damped() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=8),), priority=("ev", "x"), wait_at_limit_s=0))
    scenario.draw("c")
    scenario.charge("c", 8)

    assert scenario.decide(ABOVE_LIMIT) == current("c", 7)
    assert scenario.decide_many(0, 4) == [[], [], [], []]
    assert scenario.decide_many(0, 2) == [current("c", 8), on("x")]


def test_charger_deactivated_above_the_limit_is_activated_when_the_damping_time_has_passed() -> None:
    """Every ampere taken back at once is damped from then, so the ones after the first come back without waiting."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=8),)))
    scenario.draw("c")
    scenario.charge("c", 8)

    assert scenario.decide(20_000) == deactivate("c")
    assert scenario.decide_many(0, 4) == [[], [], [], []]
    assert scenario.decide_many(0, 3) == [activate("c"), current("c", 7), current("c", 8)]


def test_ampere_taken_back_to_make_room_is_damped() -> None:
    """The variant switch takes 7 A back for the appliance that moves above the group, which then is turned on at once."""
    scenario = Scenario(
        make_config(
            appliance("h", variants=("morning",)),
            chargers=(charger("c", max_a=7),),
            priority=("h:morning", "ev", "h"),
        )
    )
    scenario.draw("c")
    scenario.charge("c", 7)
    morning = ("morning",)

    assert scenario.decide(9900, true=morning) == off("h:morning") + current("c", 6)
    assert scenario.decide(0, true=morning) == on("h:morning")
    assert scenario.decide_many(0, 3, true=morning) == [[], [], []]
    assert scenario.decide(0, true=morning) == current("c", 7)


def test_no_switch_over_to_a_queued_charger_that_is_damped() -> None:
    """b, deactivated above the limit, is queued behind a, which gets its next ampere instead."""
    scenario = Scenario(make_config(chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=0))
    scenario.set_charger("a", car_connected=False)
    scenario.draw("b")
    scenario.charge("b", 7)
    scenario.set_charger("a", car_connected=True)
    scenario.draw("a")
    assert scenario.decide(5000) == current("b", 6) + activate("a")
    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")

    assert scenario.decide(5000) == current("a", 7)
