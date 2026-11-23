"""Scenario tests for EV charging in the regulation engine.

The chargers draw 4000 W at their minimum current of 6 A, so an ampere is about 667 W.
"""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.config_model import OverrideEnd, SwitchedBy
from custom_components.kraftvakt.regulation.charging import (
    ChargerState,
    ChargerStatus,
)
from custom_components.kraftvakt.regulation.model import AmpereStepKey, Waiting, WaitingReason

from .configs import appliance, charger, charger_group, make_config
from .scenario import (
    Scenario,
    activate,
    current,
    deactivate,
    off,
    on,
)

ABOVE_LIMIT = 10_500
NO_CAR = {"car_connected": False}


def one_charger(**settings) -> Scenario:
    """Return a scenario with charger c from 6 A to 8 A and no waiting time."""
    settings.setdefault("max_a", 8)
    return Scenario(make_config(chargers=(charger("c", **settings),), wait_at_limit_s=0))


def two_chargers(*, one_at_a_time: bool, max_a: int = 7, dynamic_order: bool = False) -> Scenario:
    """Return a scenario with chargers a and b, in that priority, without waiting."""
    return Scenario(
        make_config(
            chargers=(charger("a", max_a=max_a), charger("b", max_a=max_a)),
            one_at_a_time=one_at_a_time,
            dynamic_order=dynamic_order,
            wait_at_limit_s=0,
        )
    )


def test_start_and_stop_deactivate_the_chargers() -> None:
    """The current is set to the minimum first."""
    scenario = Scenario(make_config("x", chargers=(charger("c", min_a=10),)))

    assert scenario.start_commands == off("x") + deactivate("c", 10)
    assert scenario.engine.stop() == off("x") + deactivate("c", 10)


def test_charger_is_stopped_while_the_regulation_is_stopped_and_waits_for_the_first_decision_after_a_start() -> None:
    scenario = one_charger()
    assert scenario.engine.chargers["c"].state is ChargerState.FIRST_DECISION

    scenario.engine.stop()
    assert scenario.engine.chargers["c"].state is ChargerState.STOPPED


def test_current_increases_one_ampere_per_ampere_step() -> None:
    """The first one activates the charger."""
    scenario = one_charger()
    scenario.draw("c")

    assert scenario.decide_many(2000, 4) == [
        activate("c"),
        current("c", 7),
        current("c", 8),
        [],
    ]
    assert scenario.engine.chargers["c"] == ChargerStatus(
        state=ChargerState.CHARGING,
        ampere_steps_on=3,
        current_a=8,
        bypassed=False,
        charging=True,
    )


def test_first_ampere_step_needs_the_power_at_minimum_current_and_the_next_the_measured_power_per_ampere() -> None:
    """At 6 A the car draws 4000 W, about 667 W per ampere.

    At the decision after the activation, the average shows the charger only in
    part, so its power at minimum current counts as used.
    """
    scenario = one_charger(min_current_power_w=4000)
    scenario.draw("c")

    assert scenario.decide(6010) == []
    assert scenario.decide(6000) == activate("c")
    assert scenario.decide(5400) == []
    assert scenario.decide(9340) == []
    assert scenario.decide(9330) == current("c", 7)


def test_current_decreases_one_ampere_at_a_time_when_an_ampere_covers_the_power_above_the_limit() -> None:
    """The last one deactivates the charger."""
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    assert scenario.decide_many(ABOVE_LIMIT, 4) == [
        current("c", 7),
        current("c", 6),
        deactivate("c"),
        [],
    ]
    assert scenario.engine.chargers["c"].current_a is None


def test_car_that_suddenly_draws_much_more_is_cut_by_the_power_above_the_limit_at_once() -> None:
    """3900 W above the limit at 16 A takes six amperes of 667 W, at one decision."""
    scenario = one_charger(max_a=16)
    scenario.draw("c")
    scenario.charge("c", 16)

    assert scenario.decide(13_900) == current("c", 10)


def test_car_is_cut_by_its_measured_power_per_ampere() -> None:
    """At 16 A it draws 5000 W, 312.5 W per ampere, so two amperes free the 500 W above the limit."""
    scenario = one_charger(max_a=16)
    scenario.draw("c")
    scenario.charge("c", 16)
    scenario.draw("c", drawing=False)
    scenario.set_charger("c", actively_charging=True, charging_power_w=5000)

    assert scenario.decide(ABOVE_LIMIT) == current("c", 14)


def test_freeing_power_ends_at_an_appliance() -> None:
    """Only what a charger draws is known, so an appliance is switched off only when it is the first."""
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=8),), wait_at_limit_s=0))
    scenario.turn_on("x")
    scenario.draw("c")
    scenario.charge("c", 8)

    assert scenario.decide(20_000) == deactivate("c")
    assert scenario.decide(20_000) == off("x")


def test_charger_activated_again_waits_the_waiting_time_for_ev_chargers() -> None:
    """It is activated at once the first time.

    Activated again, it waits from when it is next as an appliance would with twice the waiting time at the limit, with its own power at minimum current counted:
    151 s by the curve, then 10 minutes.
    """
    scenario = Scenario(make_config(chargers=(charger("c", max_a=6, min_current_power_w=2000),), wait_at_limit_s=300))
    scenario.draw("c")

    assert scenario.decide(7000) == activate("c")
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
    assert scenario.decide_many(5000, 4) == [[], [], [], activate("c")]
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
    assert scenario.decide_many(5000, 11) == [[]] * 10 + [activate("c")]


def test_charger_is_one_unit_for_the_growth_on_repeated_turn_on() -> None:
    """Its own amperes up and down neither count nor end the count, so the third activation waits 10 minutes, not 151 s by the curve."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=7, min_current_power_w=2000),), wait_at_limit_s=300))
    scenario.draw("c")

    assert scenario.decide_many(7000, 2) == [activate("c"), current("c", 7)]
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
    assert scenario.decide_many(5000, 5) == [[], [], [], activate("c"), current("c", 7)]
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
    assert scenario.decide_many(5000, 11) == [[]] * 10 + [activate("c")]


def test_charger_activated_again_waits_also_with_a_step_on_below() -> None:
    """The waiting protects the relays of the charger and the car, so x on below does not let c go on again at once after a short fault.

    It waits its 151 s by the curve, and x stays on meanwhile.
    """
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=6, min_current_power_w=2000),), priority=("ev", "x"), wait_at_limit_s=300))
    scenario.draw("c")
    assert scenario.decide_many(0, 2) == [activate("c"), on("x")]
    scenario.set_charger("c", fault=True)
    assert scenario.decide(0) == deactivate("c")

    scenario.set_charger("c", fault=False)

    assert scenario.decide_many(5000, 4) == [[], [], [], activate("c")]


def test_command_to_an_appliance_leaves_a_charger_activated_again_waiting() -> None:
    """x is switched off while c waits, and c still waits its 151 s by the curve."""
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=6, min_current_power_w=2000),), wait_at_limit_s=300))
    scenario.turn_on("x")
    scenario.draw("c")
    assert scenario.decide(7000) == activate("c")
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")

    scenario.exclude("x")

    assert scenario.decide_many(5000, 4) == [off("x"), [], [], activate("c")]


def test_car_connected_again_is_activated_as_the_first_time() -> None:
    """b, deactivated when its car left, gets a switch-over at once when a car is connected again, instead of waiting until a charges at its maximum."""
    scenario = Scenario(make_config(chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True))
    scenario.draw("a")
    scenario.draw("b")
    scenario.charge("a", 8)
    scenario.draw("b", False)
    scenario.set_charger("b", car_connected=False, car_disconnected=True)
    assert deactivate("b")[-1] in scenario.decide(5000)

    scenario.set_charger("b", car_connected=True, car_disconnected=False)
    scenario.draw("b")

    assert scenario.decide(6000) == current("a", 6) + activate("b")


def test_command_to_another_charger_leaves_a_charger_activated_again_waiting() -> None:
    """a is deactivated while b waits, and b still waits its 151 s by the curve."""
    scenario = Scenario(
        make_config(
            chargers=(charger("a", max_a=6, min_current_power_w=2000), charger("b", max_a=6, min_current_power_w=2000)),
            one_at_a_time=False,
            wait_at_limit_s=300,
        )
    )
    scenario.draw("a")
    scenario.draw("b")
    assert scenario.decide_many(0, 2) == [activate("a"), activate("b")]
    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")

    scenario.set_charger("a", excluded=True)

    assert scenario.decide_many(5000, 4) == [deactivate("a"), [], [], activate("b")]


def test_charger_deactivated_just_above_the_limit_is_not_activated_again_at_the_next_decision() -> None:
    """The flip from a diagnostics file: 73 W above the limit deactivates the charger, and 5655 W is far below it,
    but with its own 4157 W the charger would be at 98 % of the limit, which gives 598 s by the curve."""
    scenario = Scenario(make_config(chargers=(charger("c", min_current_power_w=4157),), wait_at_limit_s=300))
    scenario.draw("c")
    assert scenario.decide(1000) == activate("c")
    assert scenario.decide(10_073) == deactivate("c")

    assert scenario.decide(5655) == []
    waiting = scenario.engine.waiting
    assert waiting is not None
    assert waiting.until - waiting.started_at == timedelta(seconds=598)


def test_charger_deactivated_longer_ago_than_the_longest_waiting_time_is_activated_at_once() -> None:
    """The longest it can wait is 30 minutes: 10 minutes at the limit and four steps of 5 minutes."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=6, min_current_power_w=2000),), wait_at_limit_s=300))
    scenario.draw("c")
    assert scenario.decide(7000) == activate("c")
    assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
    assert scenario.decide_many(10_000, 29) == [[]] * 29

    assert scenario.decide(7000) == []
    assert scenario.decide(7000) == activate("c")


def test_several_chargers_take_turns() -> None:
    """The first ampere step of each charger, then the second."""
    scenario = two_chargers(one_at_a_time=False)
    scenario.draw("a")
    scenario.draw("b")

    assert scenario.decide_many(0, 5) == [
        activate("a"),
        activate("b"),
        current("a", 7),
        current("b", 7),
        [],
    ]
    assert scenario.decide_many(ABOVE_LIMIT, 2) == [current("b", 6), current("a", 6)]


def test_full_car_stays_activated_at_its_minimum_current() -> None:
    """Kraftvakt never guesses that a car is done."""
    scenario = one_charger()

    assert scenario.decide_many(0, 5) == [activate("c"), [], [], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED


def test_car_that_draws_power_again_gets_more_current() -> None:
    """As one that heats in the morning."""
    scenario = one_charger()
    scenario.decide_many(0, 3)

    scenario.draw("c")

    assert scenario.decide_many(0, 3) == [current("c", 7), current("c", 8), []]


def test_car_that_draws_less_than_half_of_the_power_at_minimum_current_is_held_at_its_minimum() -> None:
    """One that has more is set back to its minimum at once."""
    scenario = one_charger()
    scenario.set_charger("c", actively_charging=True, charging_power_w=1100)
    assert scenario.decide_many(0, 3) == [activate("c"), [], []]
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.draw("c", drawing=False)
    scenario.set_charger("c", actively_charging=True, charging_power_w=1100)

    assert scenario.decide(0) == current("c", 6)
    assert scenario.engine.chargers["c"].state is ChargerState.CHARGING


def test_car_that_pauses_is_held_at_its_minimum_and_gets_its_amperes_back() -> None:
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.draw("c", drawing=False)
    assert scenario.decide_many(0, 10) == [current("c", 6)] + [[]] * 9
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED

    scenario.draw("c")
    assert scenario.decide_many(0, 2) == [current("c", 7), current("c", 8)]


def test_starting_charger_holds_back_the_appliance_below_for_its_whole_start_delay() -> None:
    """The pool heater from a diagnostics file: plenty of power is free, but the car is about to draw it. A car that does not draw lets it on when the start delay ends."""
    scenario = Scenario(make_config("pool", chargers=(charger("c", start_delay_s=180),), priority=("ev", "pool"), wait_at_limit_s=0))
    assert scenario.decide(1250) == activate("c")
    activated_at = scenario.now

    assert scenario.decide_many(1250, 2) == [[], []]
    assert scenario.engine.waiting == Waiting(AmpereStepKey("c", 0), activated_at, activated_at + timedelta(minutes=3), WaitingReason.START_DELAY)
    assert scenario.engine.chargers["c"].state is ChargerState.STARTING
    assert scenario.engine.chargers["c"].starting_until == activated_at + timedelta(minutes=3)
    assert scenario.decide(1250) == on("pool")
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED


def test_starting_charger_holds_back_the_appliance_below_also_while_its_car_ramps_up() -> None:
    """A car that charges with less than 90 % of its power at minimum current gets no more current while it is starting."""
    scenario = Scenario(make_config("pool", chargers=(charger("c", start_delay_s=180),), priority=("ev", "pool"), wait_at_limit_s=0))
    assert scenario.decide(1250) == activate("c")

    scenario.set_charger("c", actively_charging=True, charging_power_w=3500)

    assert scenario.decide_many(4750, 2) == [[], []]
    assert scenario.engine.chargers["c"].state is ChargerState.CHARGING
    assert scenario.decide(4750) == current("c", 7)


def test_starting_charger_gets_more_amperes_when_its_car_draws_almost_all_its_power_at_minimum_current() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=7, start_delay_s=180),), priority=("ev", "x"), wait_at_limit_s=0))
    assert scenario.decide(1000) == activate("c")

    scenario.draw("c")

    assert scenario.decide_many(1000, 3) == [current("c", 7), [], on("x")]


def test_starting_charger_does_not_hold_back_the_steps_above_it() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("c", start_delay_s=180),), priority=("x", "ev"), wait_at_limit_s=0), excluded=("x",))
    assert scenario.decide(1000) == activate("c")

    scenario.exclude()

    assert scenario.decide(1000) == on("x")


def test_starting_charger_holds_back_the_next_charger_of_its_group() -> None:
    """With one charger at a time, both cars wait at the minimum current, but b is activated only when a's start delay has ended."""
    scenario = Scenario(make_config(chargers=(charger("a", start_delay_s=180), charger("b", start_delay_s=180)), wait_at_limit_s=0))

    assert scenario.decide_many(0, 4) == [activate("a"), [], [], activate("b")]


def test_waiting_time_counts_the_held_power_at_minimum_current() -> None:
    """There is room for the appliance below, but 5000 W with 4000 W held is close to the limit, so it waits."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=300))

    assert scenario.decide_many(5000, 6) == [activate("c"), [], on("x"), [], [], []]


def test_appliance_below_is_turned_on_while_a_car_does_not_draw_power() -> None:
    """A charger held at its minimum gets no more current and does not hold back the appliances below «EV charging»."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0))

    assert scenario.decide_many(0, 2) == [activate("c"), on("x")]
    assert scenario.engine.chargers["c"].current_a == 6


def test_car_that_starts_drawing_power_makes_room_below() -> None:
    """The appliance turned on below while the car did not draw is switched off when the charger needs room for more current."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0))
    scenario.decide_many(0, 2)

    scenario.draw("c")

    assert scenario.decide_many(9950, 2) == [off("x"), []]
    assert scenario.decide(9000) == current("c", 7)


def test_charger_whose_car_does_not_draw_is_not_switched_off_above_the_limit() -> None:
    """Switching it off would free nothing, so the appliance above it goes."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), wait_at_limit_s=0))
    scenario.turn_on("x")
    assert scenario.decide(0) == activate("c")

    assert scenario.decide_many(ABOVE_LIMIT, 2) == [off("x"), []]
    assert scenario.engine.chargers["c"].current_a == 6


def test_bypassed_charger_keeps_its_current_when_room_is_made() -> None:
    """Room is made only from steps that can be switched off."""
    scenario = Scenario(
        make_config(
            appliance("d", variants=("up",)),
            chargers=(charger("c"),),
            priority=("d:up", "ev", "d"),
            wait_at_limit_s=0,
        )
    )
    assert scenario.decide_many(0, 2) == [activate("c"), on("d")]
    scenario.set_charger("c", **NO_CAR)
    assert scenario.decide(0) == []
    assert scenario.engine.chargers["c"].bypassed

    assert scenario.decide_many(9950, 2, true=("up",)) == [off("d:up"), []]
    assert scenario.engine.chargers["c"].current_a == 6


def test_charger_switched_by_its_current_gets_only_the_current() -> None:
    """Its minimum current activates it and 0 A deactivates it, also at the start, the stop and the command repeat."""
    scenario = one_charger(switched_by=SwitchedBy.CURRENT)
    assert scenario.start_commands == current("c", 0)
    scenario.draw("c")

    assert scenario.decide_many(0, 3) == [current("c", 6), current("c", 7), current("c", 8)]
    assert scenario.decide_many(ABOVE_LIMIT, 3) == [current("c", 7), current("c", 6), current("c", 0)]
    assert scenario.repeat(timedelta(minutes=30)) == current("c", 0)
    assert scenario.engine.stop() == current("c", 0)


def test_car_disconnected_limits_the_charger_at_once() -> None:
    """From a high current down to the minimum at once."""
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.set_charger("c", **NO_CAR)

    assert scenario.decide(0) == current("c", 6)
    assert scenario.decide_many(0, 3) == [[], [], []]


@pytest.mark.parametrize(
    ("dynamic_order", "car_disconnected", "commands"),
    [
        (False, True, current("c", 6)),
        (True, False, current("c", 6)),
        (True, True, deactivate("c")),
    ],
)
def test_charger_without_a_car_keeps_its_minimum_unless_dynamic_order_knows_the_car_left(dynamic_order: bool, car_disconnected: bool, commands: list) -> None:
    """Without evidence that the car left, as while a cloud service is down, the car may still be charging."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=8),), dynamic_order=dynamic_order, wait_at_limit_s=0))
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.draw("c", drawing=False)
    scenario.set_charger("c", car_connected=False, car_disconnected=car_disconnected)

    assert scenario.decide(0) == commands


def test_car_connected_again_waits_in_the_queue_with_dynamic_order() -> None:
    """b was deactivated when its car left, so the car does not draw power before there is room for its power at minimum current."""
    scenario = two_chargers(one_at_a_time=False, max_a=16, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 8)
    scenario.draw("b", drawing=False)
    scenario.set_charger("b", car_connected=False, car_disconnected=True)
    assert scenario.decide(0) == deactivate("b")

    scenario.set_charger("b", car_connected=True, car_disconnected=False)

    assert scenario.decide(9950) == []
    assert scenario.engine.chargers["b"].state is ChargerState.QUEUED
    assert scenario.decide(5000) == activate("b")


def test_bypassed_charger_is_not_switched_off_above_the_limit() -> None:
    """Switching it off would not lower the consumption."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), wait_at_limit_s=0))
    scenario.turn_on("x")
    scenario.set_charger("c", **NO_CAR)
    assert scenario.decide(0) == []
    scenario.set_charger("c", car_connected=True)
    assert scenario.decide(0) == activate("c")
    scenario.set_charger("c", **NO_CAR, actively_charging=True, charging_power_w=4000)
    scenario.decide(0)

    assert scenario.decide(ABOVE_LIMIT) == off("x")
    assert scenario.decide(ABOVE_LIMIT) == []


def test_current_priority_starts_as_configured_at_each_start() -> None:
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.decide(0)
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]

    scenario.engine.start(scenario.now)

    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]


def test_excluded_charger_above_the_limit_switches_off_nothing_more() -> None:
    """Above the limit, nothing more is switched off when an excluded charger is deactivated."""
    scenario = two_chargers(one_at_a_time=False)
    scenario.draw("a")
    scenario.draw("b")
    scenario.charge("a", 7)
    scenario.charge("b", 7)

    scenario.set_charger("b", excluded=True)

    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")
    assert scenario.engine.chargers["a"].current_a == 7
    assert scenario.decide(ABOVE_LIMIT) == current("a", 6)


def test_one_at_a_time_every_car_may_wait_at_the_minimum_until_one_draws_power() -> None:
    """Without dynamic charging order, a car higher up that draws power takes over, and the charger below is deactivated at once."""
    scenario = two_chargers(one_at_a_time=True)

    assert scenario.decide_many(0, 3) == [activate("a"), activate("b"), []]
    assert scenario.engine.chargers["a"].state is ChargerState.ACTIVATED

    scenario.draw("b")
    assert scenario.decide_many(0, 2) == [current("b", 7), []]
    assert scenario.engine.chargers["a"].current_a == 6

    scenario.draw("a")
    assert scenario.decide(0) == deactivate("b") + current("a", 7)
    assert scenario.engine.chargers["b"].state is ChargerState.QUEUED


def test_one_at_a_time_with_dynamic_order_the_charger_that_draws_keeps_its_turn() -> None:
    """The others are deactivated at once, and may wait at their minimum again when it stops charging, when it moves to the back."""
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)
    assert scenario.decide_many(0, 2) == [activate("a"), activate("b")]

    scenario.draw("b")

    assert scenario.decide(0) == deactivate("a") + current("b", 7)
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]

    scenario.draw("b", drawing=False)
    assert scenario.decide(0) == current("b", 6) + activate("a")
    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]


def test_one_at_a_time_charger_higher_up_that_gets_a_car_gets_room_from_the_one_that_charges() -> None:
    """Without dynamic charging order, the 4000 W of a at its minimum current takes 3000 W from b at 16 A: five amperes, at once."""
    scenario = two_chargers(one_at_a_time=True, max_a=16)
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 16)

    scenario.settle()
    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(9000) == current("b", 11)
    assert scenario.decide(6000) == activate("a")


def test_excluded_charger_that_seems_to_charge_lets_the_other_charge() -> None:
    """Only a charger that is allowed to charge holds back the others."""
    scenario = two_chargers(one_at_a_time=True)
    assert scenario.decide(0) == activate("a")
    scenario.set_charger("a", actively_charging=True, charging_power_w=4000, excluded=True)

    assert scenario.decide(0) == deactivate("a") + activate("b")
    assert scenario.engine.chargers["b"].state is not ChargerState.QUEUED


def test_new_car_takes_the_room_of_a_charger_below_without_dynamic_order() -> None:
    """The configured priority applies, so b gives up what a needs at its minimum current at once: 1000 W, two amperes."""
    scenario = two_chargers(one_at_a_time=False, max_a=16)
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 8)

    scenario.settle()
    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(7000) == current("b", 6)
    assert scenario.decide(5500) == activate("a")


def test_appliance_below_the_group_gives_room_before_a_charger_goes_down() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("a"), charger("b", max_a=8)), priority=("ev", "x"), one_at_a_time=False, wait_at_limit_s=0))
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 8)
    assert scenario.decide(0) == on("x")

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(7000, 3) == [off("x"), current("b", 6), deactivate("b")]


def sharing_chargers(*, b_amperes: int, **settings) -> Scenario:
    """Return a and b sharing by charging power, b charging with b_amperes and a's car connected afterwards."""
    scenario = Scenario(
        make_config(
            chargers=(charger("a", max_a=16, **settings), charger("b", max_a=16)),
            one_at_a_time=False,
            dynamic_order=True,
            wait_at_limit_s=0,
        )
    )
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", b_amperes)
    scenario.draw("b", drawing=False)
    scenario.set_charger("b", actively_charging=True, charging_power_w=b_amperes * 4000 / 6)
    scenario.set_charger("a", car_connected=True)
    return scenario


def test_charger_that_charges_keeps_its_room_from_a_car_connected_later() -> None:
    """With dynamic charging order, a waits for room beside b instead of taking it."""
    scenario = sharing_chargers(b_amperes=7)

    assert scenario.decide_many(9950, 3) == [[], [], []]
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]


def test_switch_over_shares_the_power_when_it_covers_the_power_at_minimum_current() -> None:
    """b at 11 A frees 5/11 of what it draws by going to 6 A.

    From 8600 W it frees 3909 W, which with 50 W free is not enough for the 4000 W a draws at its minimum, but from 8800 W it frees 4000 W, which is.
    """
    scenario = sharing_chargers(b_amperes=11)
    scenario.set_charger("b", charging_power_w=8600)
    assert scenario.decide(9950) == []

    scenario.set_charger("b", charging_power_w=8800)

    assert scenario.decide(9950) == current("b", 6) + activate("a")
    scenario.decide(9950)
    assert scenario.engine.chargers["a"].state is ChargerState.ACTIVATED


def test_switch_over_when_the_free_power_alone_covers_the_power_at_minimum_current() -> None:
    """b at its minimum gives nothing up, and a starts beside it before b gets more current."""
    scenario = sharing_chargers(b_amperes=6)
    scenario.set_charger("b", charging_power_w=4100)

    assert scenario.decide(5000) == activate("a")


def test_no_switch_over_while_an_entry_above_the_group_waits_for_room() -> None:
    """The appliance above gets room from b first, by the fixed order.

    Included again, it takes b's lowest ampere step, and then b gives up what its 5000 W at minimum current needs: b at its minimum would free too little, so it is deactivated.
    """
    scenario = Scenario(make_config(appliance("x", reserve_w=5000), chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=0))
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.exclude("x")
    scenario.charge("b", 12)
    scenario.draw("b", drawing=False)
    scenario.set_charger("b", actively_charging=True, charging_power_w=8300)
    scenario.set_charger("a", car_connected=True)
    scenario.exclude()
    assert scenario.decide(9950) == current("b", 11)

    assert scenario.decide(9950) == deactivate("b")


def test_switch_over_does_not_wait() -> None:
    scenario = Scenario(make_config(chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=120))
    scenario.set_charger("a", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 12)
    scenario.draw("b", drawing=False)
    scenario.set_charger("b", actively_charging=True, charging_power_w=8300)
    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(9100) == current("b", 6) + activate("a")


def test_switch_over_to_a_charger_activated_again_waits_its_waiting_time() -> None:
    """b, deactivated above the limit, is queued behind a, and waits on its own row before the switch-over.

    a gets no more current meanwhile, as when any step waits.
    """
    scenario = Scenario(make_config(chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True))
    scenario.set_charger("a", car_connected=False)
    scenario.draw("b")
    scenario.charge("b", 7)
    scenario.set_charger("a", car_connected=True)
    scenario.draw("a")
    assert scenario.decide(5000) == current("b", 6) + activate("a")
    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")

    assert scenario.decide(5000) == []
    waiting = scenario.engine.waiting
    assert waiting is not None
    assert (waiting.key, waiting.reason) == (AmpereStepKey("b", 0), WaitingReason.WAITING_TIME)
    while scenario.now + timedelta(minutes=1) < waiting.until:
        assert scenario.decide(5000) == []
    assert scenario.decide(5000) == activate("b")


def test_starting_charger_holds_back_the_charger_that_charges() -> None:
    """b does not take the power the car of a is about to draw, and no second switch-over is made on b's old charging power."""
    scenario = sharing_chargers(b_amperes=12, start_delay_s=180)
    scenario.set_charger("b", charging_power_w=8300)
    scenario.decide(9100)

    assert scenario.decide(6500) == []

    scenario.draw("a")
    scenario.set_charger("b", charging_power_w=4100)
    assert scenario.decide(6500) == current("a", 7)


def test_chargers_that_both_charge_share_in_the_configured_priority() -> None:
    """a is higher, so above the limit b loses its last ampere, here its first."""
    scenario = sharing_chargers(b_amperes=12)
    scenario.set_charger("b", charging_power_w=8300)
    scenario.decide(9100)
    scenario.draw("a")

    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")
    assert scenario.engine.chargers["a"].current_a == 6
    scenario.decide(9950)
    assert scenario.engine.chargers["b"].state is ChargerState.QUEUED


def test_excluded_charger_stops_at_once_and_never_charges() -> None:
    """All ampere steps off at once."""
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.set_charger("c", excluded=True)

    assert scenario.decide(0) == deactivate("c")
    assert scenario.decide_many(0, 3) == [[], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.EXCLUDED


def test_charger_with_a_fault_stops_at_once_and_charges_again_when_it_clears() -> None:
    """All ampere steps off at once, and from the minimum current again when the fault has cleared."""
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    scenario.set_charger("c", fault=True)

    assert scenario.decide(0) == deactivate("c")
    assert scenario.decide_many(0, 3) == [[], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.FAULT
    scenario.set_charger("c", excluded=True)
    assert scenario.decide(0) == []
    assert scenario.engine.chargers["c"].state is ChargerState.FAULT

    scenario.set_charger("c", fault=False, excluded=False)
    assert scenario.decide_many(0, 2) == [activate("c"), current("c", 7)]


def test_charger_that_stops_charging_with_a_fault_gets_no_rest() -> None:
    """The other may charge while it has a fault, and it keeps its place when the fault clears."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.draw("a")
    assert scenario.decide(0) == activate("a")
    scenario.decide_many(0, 3)

    scenario.set_charger("a", fault=True)
    assert scenario.decide(0) == deactivate("a") + activate("b")
    assert list(scenario.engine.charging_priorities.values()) == [["a", "b"]]

    scenario.set_charger("a", fault=False)
    assert scenario.decide(0) == activate("a")
    assert scenario.decide(0) == deactivate("b") + current("a", 7)


def test_fault_neither_arms_nor_ends_the_override() -> None:
    """The car charges outside the window again when the fault clears."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CAR_DISCONNECTED)
    scenario.draw("c")
    scenario.set_charger("c", window_override=True, fault=True)

    assert scenario.decide(0) == []
    assert scenario.overrides.armed == []

    scenario.set_charger("c", car_connected=False, car_disconnected=True, override_armed=True)
    assert scenario.decide(0) == []
    assert scenario.overrides.ended == []

    scenario.set_charger("c", car_connected=True, car_disconnected=False, fault=False)
    assert scenario.decide(0) == activate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED


def test_charger_charges_only_inside_its_charging_window() -> None:
    """Charging stops at the first decision after the window ends."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c", max_a=8, window="22:00-22:03"),),
            wait_at_limit_s=0,
        ),
        start=datetime(2026, 11, 7, 21, 58, tzinfo=UTC),
    )
    scenario.draw("c")

    assert scenario.decide_many(0, 5) == [
        [],
        activate("c"),
        current("c", 7),
        current("c", 8),
        deactivate("c"),
    ]


def window_ending_scenario() -> Scenario:
    """Return charger c, 6 A to 10 A, with charge until disconnected, charging at 8 A when its window ends at 22:03."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c", max_a=10, window="22:00-22:03"),),
            wait_at_limit_s=0,
        ),
        start=datetime(2026, 11, 7, 21, 58, tzinfo=UTC),
    )
    scenario.draw("c")
    scenario.set_charger("c", charge_until_disconnected=True)
    assert scenario.decide_many(0, 4) == [
        [],
        activate("c"),
        current("c", 7),
        current("c", 8),
    ]
    assert scenario.charged_in_window == {"c"}
    return scenario


def test_charger_that_charged_in_its_window_may_charge_until_the_car_is_disconnected() -> None:
    """It is regulated as inside the window, also after the limit has taken its last ampere or the car has stopped charging."""
    scenario = window_ending_scenario()

    assert scenario.decide(0) == current("c", 9)
    assert scenario.engine.chargers["c"].state is ChargerState.CHARGING
    assert scenario.decide(20_000) == deactivate("c")
    assert scenario.decide(0) == activate("c")
    scenario.draw("c", drawing=False)
    assert scenario.decide(0) == []
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED

    scenario.set_charger("c", car_connected=False, car_disconnected=True)
    assert scenario.decide(0) == deactivate("c")
    assert scenario.charged_in_window == set()
    scenario.set_charger("c", car_connected=True, car_disconnected=False)
    assert scenario.decide_many(0, 2) == [[], []]
    assert scenario.engine.chargers["c"].state is ChargerState.OUTSIDE_WINDOW


def test_charging_until_disconnected_needs_evidence_that_the_car_is_disconnected() -> None:
    """A car sensor without a value bypasses the charger, but does not end it."""
    scenario = window_ending_scenario()
    scenario.set_charger("c", car_connected=False)

    assert scenario.decide(0) == current("c", 6)
    assert scenario.charged_in_window == {"c"}
    scenario.set_charger("c", car_connected=True)
    assert scenario.decide(0) == current("c", 7)


def test_charge_until_disconnected_turned_off_ends_the_charging_after_the_window() -> None:
    scenario = window_ending_scenario()
    scenario.set_charger("c", charge_until_disconnected=False)

    assert scenario.decide(0) == deactivate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.OUTSIDE_WINDOW


def test_charged_in_window_is_kept_in_the_safe_state_until_the_car_is_disconnected() -> None:
    scenario = window_ending_scenario()

    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == deactivate("c")
    assert scenario.decide(None, sensor_valid=False) == []
    assert scenario.charged_in_window == {"c"}
    scenario.set_charger("c", car_connected=False, car_disconnected=True)
    assert scenario.decide(None, sensor_valid=False) == []
    assert scenario.charged_in_window == set()


def test_charger_whose_car_did_not_use_power_in_its_window_waits_for_the_next() -> None:
    scenario = Scenario(
        make_config(chargers=(charger("c", window="22:00-22:02"),), wait_at_limit_s=0),
        start=datetime(2026, 11, 7, 21, 59, tzinfo=UTC),
    )
    scenario.set_charger("c", charge_until_disconnected=True)

    assert scenario.decide_many(0, 3) == [activate("c"), [], deactivate("c")]
    assert scenario.charged_in_window == set()


def test_override_lasts_until_a_connected_car_is_disconnected() -> None:
    """A window that starts does not end it, nor a car sensor without evidence."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CAR_DISCONNECTED)
    scenario.draw("c")
    scenario.set_charger("c", window_override=True, car_connected=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.overrides.armed == ["c"]
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED
    assert scenario.decide(0, after=timedelta(hours=20)) == []
    assert scenario.overrides.ended == []

    scenario.draw("c", drawing=False)
    scenario.set_charger("c", car_connected=False, override_armed=True)
    assert scenario.decide(0) == []
    assert scenario.overrides.ended == []
    scenario.set_charger("c", car_disconnected=True)
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]
    assert scenario.engine.chargers["c"].state is ChargerState.NO_CAR


def test_override_ends_when_the_activated_charger_stops_charging() -> None:
    """It arms only when the charger was activated and charging, and ends at the first evidence that the car does not charge."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CHARGING_STOPPED)
    scenario.draw("c")
    scenario.set_charger("c", window_override=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.overrides.armed == []
    assert scenario.decide(0) == []
    assert scenario.overrides.armed == ["c"]

    scenario.draw("c", drawing=False)
    scenario.set_charger("c", override_armed=True, charging_stopped=True)
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]


def test_override_does_not_end_when_the_regulation_has_deactivated_the_charger() -> None:
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CHARGING_STOPPED)
    scenario.draw("c")
    scenario.set_charger("c", window_override=True, override_armed=True)
    scenario.decide(0)
    assert scenario.decide(12_000) == deactivate("c")

    scenario.draw("c", drawing=False)
    scenario.set_charger("c", charging_stopped=True)

    assert scenario.decide(12_000) == []
    assert scenario.overrides.ended == []


def test_override_ends_also_during_a_penalty() -> None:
    """The override is evaluated at every decision."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CAR_DISCONNECTED)
    scenario.set_charger("c", window_override=True, car_connected=True)
    scenario.decide(12000, tariff=12000)
    assert scenario.decide(12000, tariff=12000) == deactivate("c")
    assert scenario.engine.penalty.active

    scenario.set_charger("c", car_disconnected=True, override_armed=True)
    assert scenario.decide(12000, tariff=12000) == []
    assert scenario.overrides.ended == ["c"]


def test_switching_the_override_off_stops_charging_outside_the_window() -> None:
    scenario = one_charger(max_a=6, window="22:00-06:00")
    scenario.draw("c")
    scenario.set_charger("c", window_override=True)
    assert scenario.decide(0) == activate("c")

    scenario.set_charger("c", window_override=False)

    assert scenario.decide(0) == deactivate("c")


def test_override_without_window_has_no_effect() -> None:
    """The charger may always charge, and the override stays."""
    scenario = one_charger(max_a=6)
    scenario.draw("c")
    scenario.set_charger("c", window_override=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.decide(0, after=timedelta(days=2)) == []


def test_penalty_and_safe_state_deactivate_the_chargers() -> None:
    """All at once, and the charger starts again afterwards."""
    scenario = one_charger()
    scenario.draw("c")
    scenario.charge("c", 8)

    assert scenario.decide(0, sensor_lost=True) == deactivate("c")
    assert scenario.engine.chargers["c"].ampere_steps_on == 0
    assert scenario.decide(0) == deactivate("c")
    assert scenario.decide(0) == activate("c")


def test_variant_switch_makes_room_by_switching_off_an_ampere_step() -> None:
    """The lowest step that is on may be an ampere step."""
    scenario = Scenario(
        make_config(
            appliance("h", variants=("morning",)),
            chargers=(charger("c", max_a=7),),
            priority=("h:morning", "ev", "h"),
        )
    )
    scenario.draw("c")
    scenario.charge("c", 7)

    assert scenario.decide(9900, true=("morning",)) == off("h:morning") + current("c", 6)


def test_variant_switch_makes_room_past_a_charger_whose_car_does_not_draw() -> None:
    """Switching it off would free nothing, so the appliance above it gives room."""
    scenario = Scenario(
        make_config(
            appliance("d", variants=("up",), reserve_w=20_000),
            "x",
            chargers=(charger("c"),),
            priority=("d:up", "x", "ev", "d"),
            wait_at_limit_s=0,
        )
    )
    assert scenario.decide_many(0, 2) == [on("x"), activate("c")]

    assert scenario.decide(9950, true=("up",)) == off("d:up") + off("x")
    assert scenario.engine.chargers["c"].current_a == 6


def two_groups() -> Scenario:
    """Return chargers a and b in their own groups, around appliance x."""
    return Scenario(
        make_config(
            "x",
            chargers=(charger("a", max_a=7),),
            groups=(charger_group("g2", charger("b", max_a=7)),),
            priority=("ev", "x", "@g2"),
            wait_at_limit_s=0,
        )
    )


def test_starting_charger_holds_back_a_switch_over_in_a_group_below() -> None:
    scenario = Scenario(
        make_config(
            chargers=(charger("a", start_delay_s=180),),
            groups=(charger_group("g2", charger("b"), charger("c"), one_at_a_time=False, dynamic_order=True),),
            priority=("ev", "@g2"),
            wait_at_limit_s=0,
        )
    )
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("c", **NO_CAR)
    scenario.draw("b")
    scenario.charge("b", 12)
    scenario.draw("b", drawing=False)
    scenario.set_charger("b", actively_charging=True, charging_power_w=8000)
    scenario.set_charger("a", car_connected=True)
    scenario.set_charger("c", car_connected=True)

    assert scenario.decide(1000) == activate("a")
    assert scenario.decide_many(1000, 2) == [[], []]
    assert scenario.decide(1000) == current("b", 6) + activate("c")


def test_each_charger_group_has_its_own_place_and_one_at_a_time() -> None:
    """The charger that charges in one group does not deactivate the charger in the other."""
    scenario = two_groups()
    scenario.draw("a")
    scenario.draw("b")

    assert scenario.start_commands == off("x") + deactivate("a") + deactivate("b")
    assert scenario.decide_many(0, 6) == [
        activate("a"),
        current("a", 7),
        on("x"),
        activate("b"),
        current("b", 7),
        [],
    ]
    assert scenario.engine.charging_priorities == {"ev": ["a"], "g2": ["b"]}
    assert scenario.decide_many(ABOVE_LIMIT, 3) == [
        current("b", 6),
        deactivate("b"),
        off("x"),
    ]
