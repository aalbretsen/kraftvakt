"""Scenario tests for EV charging in the regulation engine."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.config_model import OverrideEnd
from custom_components.kraftvakt.regulation.charging import (
    ChargerState,
    ChargerStatus,
)

from .configs import appliance, charger, charger_group, make_config
from .scenario import (
    DECISION_INTERVAL,
    Scenario,
    activate,
    current,
    deactivate,
    off,
    on,
)

ABOVE_LIMIT = 10_500
NO_CAR = {"car_connected": False}
CHARGING = {"actively_charging": True}


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


def test_current_increases_one_ampere_per_ampere_step() -> None:
    """The first one activates the charger."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)

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
        car_connected=True,
    )


def test_only_the_first_ampere_step_needs_the_power_reserve() -> None:
    scenario = one_charger(reserve_w=4000)
    scenario.set_charger("c", **CHARGING)

    assert scenario.decide(6010) == []
    assert scenario.decide(6000) == activate("c")
    assert scenario.decide(9890) == current("c", 7)


def test_current_decreases_one_ampere_per_ampere_step() -> None:
    """The last one deactivates the charger."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 8)

    assert scenario.decide_many(ABOVE_LIMIT, 4) == [
        current("c", 7),
        current("c", 6),
        deactivate("c"),
        [],
    ]
    assert scenario.engine.chargers["c"].current_a is None


def test_ampere_steps_have_their_own_growth() -> None:
    """5, 10, 15, 20, 25 and then 30 minutes."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=6),), wait_at_limit_s=300))
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 6)
    waits = []
    for _ in range(8):
        assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
        waiting_started = scenario.now + timedelta(minutes=1)
        scenario.charge("c", 6)
        waits.append((scenario.now - waiting_started) / timedelta(minutes=1))

    assert waits == [0, 5, 10, 15, 20, 25, 30, 30]


def test_ampere_steps_grow_with_the_configured_increment_and_cap() -> None:
    """Steps of half of 4 minutes, 2 steps: 4, 6 and then 8 minutes."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c", max_a=6),),
            wait_at_limit_s=240,
            charger_repeat=(0.5, 2),
        )
    )
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 6)
    waits = []
    for _ in range(6):
        assert scenario.decide(ABOVE_LIMIT) == deactivate("c")
        waiting_started = scenario.now + timedelta(minutes=1)
        scenario.charge("c", 6)
        waits.append((scenario.now - waiting_started) / timedelta(minutes=1))

    assert waits == [0, 4, 6, 8, 8, 8]


def test_several_chargers_take_turns() -> None:
    """The first ampere step of each charger, then the second."""
    scenario = two_chargers(one_at_a_time=False)
    scenario.set_charger("a", **CHARGING)
    scenario.set_charger("b", **CHARGING)

    assert scenario.decide_many(0, 5) == [
        activate("a"),
        activate("b"),
        current("a", 7),
        current("b", 7),
        [],
    ]
    assert scenario.decide_many(ABOVE_LIMIT, 2) == [current("b", 6), current("a", 6)]


def test_charger_whose_car_does_not_start_is_done() -> None:
    """Kept at the minimum current while it is tried, and deactivated when its time to start has passed."""
    scenario = one_charger()

    assert scenario.decide_many(0, 5) == [activate("c"), [], deactivate("c"), [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.DONE


@pytest.mark.parametrize(("start_delay_s", "decisions_before_bypassed"), [(300, 5), (0, 2)])
def test_cloud_controlled_charger_gets_its_start_delay_before_it_is_done(start_delay_s: int, decisions_before_bypassed: int) -> None:
    """Never less than the two windows every charger gets."""
    scenario = one_charger(cloud_controlled=True, start_delay_s=start_delay_s)
    assert scenario.decide(0) == activate("c")
    activated_at = scenario.now

    scenario.decide_many(0, decisions_before_bypassed - 1)
    status = scenario.engine.chargers["c"]
    assert status.state is ChargerState.STARTING
    assert status.starting_until == activated_at + decisions_before_bypassed * DECISION_INTERVAL
    assert scenario.decide(0) == deactivate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.DONE


@pytest.mark.parametrize(
    ("cloud_controlled", "expected"),
    [
        (False, [activate("c"), on("x"), deactivate("c"), [], [], []]),
        (True, [activate("c"), [], [], [], [], deactivate("c") + on("x")]),
    ],
)
def test_starting_cloud_controlled_charger_holds_its_power_reserve(cloud_controlled: bool, expected: list) -> None:
    """The appliance below has room only when the car that is about to draw power is left out."""
    scenario = Scenario(
        make_config(
            "x",
            chargers=(charger("c", cloud_controlled=cloud_controlled),),
            priority=("ev", "x"),
            wait_at_limit_s=0,
        )
    )

    assert scenario.decide_many(6000, 6) == expected


@pytest.mark.parametrize(
    ("cloud_controlled", "expected"),
    [
        (False, [activate("c"), on("x"), deactivate("c"), [], [], []]),
        (True, [activate("c"), [], [], [], [], deactivate("c") + on("x")]),
    ],
)
def test_waiting_time_counts_the_held_power_reserve(cloud_controlled: bool, expected: list) -> None:
    """There is room for the appliance below, but 5000 W with 4000 W held is close to the limit, so it waits."""
    scenario = Scenario(make_config("x", chargers=(charger("c", cloud_controlled=cloud_controlled),), priority=("ev", "x"), wait_at_limit_s=300))

    assert scenario.decide_many(5000, 6) == expected


def test_held_power_reserve_ends_when_the_car_starts_charging() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("c", max_a=7, cloud_controlled=True),), priority=("ev", "x"), wait_at_limit_s=0))
    assert scenario.decide_many(6000, 2) == [activate("c"), []]

    scenario.set_charger("c", **CHARGING)

    assert scenario.decide_many(6000, 2) == [current("c", 7), on("x")]


def test_appliance_below_is_turned_on_while_a_charger_is_tried() -> None:
    """A charger on trial gets no more current and does not hold back the
    appliances below «EV charging»."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0))

    assert scenario.decide_many(0, 2) == [activate("c"), on("x")]
    assert scenario.engine.chargers["c"].current_a == 6


def test_charger_that_starts_charging_makes_room_below() -> None:
    """The appliance turned on below while the charger was tried is switched
    off when the charger needs room for more current."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0))
    scenario.decide_many(0, 2)

    scenario.set_charger("c", **CHARGING)

    assert scenario.decide_many(9950, 2) == [off("x"), []]
    assert scenario.decide(9000) == current("c", 7)


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


def test_charger_on_trial_gets_more_current_when_the_car_draws_power() -> None:
    scenario = one_charger()
    scenario.decide(0)

    scenario.set_charger("c", **CHARGING)

    assert scenario.decide_many(0, 3) == [current("c", 7), current("c", 8), []]


def test_car_disconnected_limits_the_charger_at_once() -> None:
    """From a high current down to the minimum at once."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
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
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 8)

    scenario.set_charger("c", car_connected=False, car_disconnected=car_disconnected, actively_charging=False)

    assert scenario.decide(0) == commands


def test_car_connected_again_waits_in_the_queue_with_dynamic_order() -> None:
    """b was deactivated when its car left, so the car does not draw power before there is room for its reserve."""
    scenario = two_chargers(one_at_a_time=False, max_a=16, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 8)
    scenario.set_charger("b", car_connected=False, car_disconnected=True, actively_charging=False)
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
    scenario.set_charger("c", car_connected=True, actively_charging=False)
    assert scenario.decide(0) == activate("c")
    scenario.set_charger("c", **NO_CAR)
    scenario.decide(0)

    assert scenario.decide(ABOVE_LIMIT) == off("x")
    assert scenario.decide(ABOVE_LIMIT) == []


def test_done_charger_does_not_stand_in_the_way_one_at_a_time() -> None:
    """The other is activated and it is deactivated, and with dynamic charging order it moves to the back."""
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)

    assert scenario.decide_many(0, 3) == [
        activate("a"),
        [],
        deactivate("a") + activate("b"),
    ]
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]


def full_cars_after_both_were_tried() -> Scenario:
    """Return two chargers with full cars, one at a time, both tried and done."""
    scenario = Scenario(
        make_config(
            "x",
            chargers=(charger("a", max_a=7), charger("b", max_a=7)),
            priority=("ev", "x"),
            wait_at_limit_s=0,
        )
    )
    assert scenario.decide_many(0, 5) == [
        activate("a"),
        on("x"),
        deactivate("a") + activate("b"),
        [],
        deactivate("b"),
    ]
    return scenario


def test_chargers_with_full_cars_are_tried_once() -> None:
    """They are done until the car is disconnected."""
    scenario = full_cars_after_both_were_tried()

    assert scenario.decide_many(0, 60) == [[]] * 60
    assert scenario.engine.chargers["a"].state is ChargerState.DONE
    assert scenario.engine.chargers["b"].state is ChargerState.DONE


def test_car_connected_again_is_tried_at_once() -> None:
    """Only evidence that the car is disconnected ends done."""
    scenario = full_cars_after_both_were_tried()
    scenario.set_charger("a", car_connected=False)
    assert scenario.decide(0) == []
    scenario.set_charger("a", car_connected=True)
    assert scenario.decide(0) == []

    scenario.set_charger("a", car_connected=False, car_disconnected=True)
    assert scenario.decide(0) == []
    scenario.set_charger("a", car_connected=True, car_disconnected=False)

    assert scenario.decide(0) == activate("a")


def test_car_connected_again_gets_two_windows_on_the_charger_that_stayed_activated() -> None:
    scenario = one_charger()
    scenario.set_charger("c", car_connected=True, **CHARGING)
    scenario.charge("c", 8)
    scenario.set_charger("c", car_connected=False, actively_charging=False)
    assert scenario.decide(0) == current("c", 6)

    scenario.set_charger("c", car_connected=True)

    scenario.decide_many(0, 2)
    assert scenario.engine.chargers["c"].state is ChargerState.ACTIVATED
    assert scenario.decide(0) == deactivate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.DONE


def test_current_priority_starts_as_configured_at_each_start() -> None:
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.decide(0)
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]

    scenario.engine.start(scenario.now)

    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]


def test_excluded_charger_above_the_limit_switches_off_nothing_more() -> None:
    """Above the limit, nothing more is switched off when an excluded charger
    is deactivated."""
    scenario = two_chargers(one_at_a_time=False)
    scenario.set_charger("a", **CHARGING)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("a", 7)
    scenario.charge("b", 7)

    scenario.set_charger("b", excluded=True)

    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")
    assert scenario.engine.chargers["a"].current_a == 7
    assert scenario.decide(ABOVE_LIMIT) == current("a", 6)


def test_charging_charger_goes_first_and_the_other_waits() -> None:
    """Until it stops, whatever the priority, with dynamic charging order."""
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    assert scenario.decide(0) == activate("b")

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(0, 3) == [current("b", 7), [], []]
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED

    scenario.set_charger("b", actively_charging=False, car_connected=False)

    assert scenario.decide(0) == deactivate("b") + activate("a")
    assert scenario.engine.chargers["a"].state is not ChargerState.QUEUED


def test_first_charger_in_the_current_priority_is_chosen() -> None:
    """When none charges, also when both have a car."""
    scenario = two_chargers(one_at_a_time=True)

    assert scenario.decide(0) == activate("a")
    assert scenario.engine.chargers["b"].current_a is None


def test_charger_that_counts_as_charging_keeps_the_other_waiting() -> None:
    scenario = two_chargers(one_at_a_time=True, dynamic_order=True)
    scenario.set_charger("b", actively_charging=True)

    assert scenario.decide(0) == activate("b")
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED


def test_excluded_charger_that_counts_as_charging_lets_the_other_charge() -> None:
    """Only a charger that is allowed to charge holds back the others."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("b", actively_charging=True, excluded=True)

    assert scenario.decide(0) == activate("a")
    assert scenario.engine.chargers["a"].state is not ChargerState.QUEUED


def test_new_car_takes_the_room_of_a_charger_below_without_dynamic_order() -> None:
    """The configured priority applies, so b goes to its minimum at once, and is deactivated when the reserve of a still does not fit."""
    scenario = two_chargers(one_at_a_time=False, max_a=16)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 8)

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(7000, 2) == [current("b", 6), deactivate("b")]
    assert scenario.decide(5500) == activate("a")


def test_one_at_a_time_without_dynamic_order_stops_the_charger_below() -> None:
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 7)

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(0) == deactivate("b") + activate("a")


def test_one_at_a_time_without_dynamic_order_stops_the_charger_below_before_there_is_room() -> None:
    """b may not charge on, so it is deactivated at once, and a is activated when the average shows room for its reserve."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 7)

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(9000) == deactivate("b")
    assert scenario.decide(5000) == activate("a")


def test_appliance_below_the_group_gives_room_before_a_charger_goes_to_its_minimum() -> None:
    scenario = Scenario(make_config("x", chargers=(charger("a"), charger("b", max_a=8)), priority=("ev", "x"), one_at_a_time=False, wait_at_limit_s=0))
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 8)
    assert scenario.decide(0) == on("x")

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(7000, 3) == [off("x"), current("b", 6), deactivate("b")]


def sharing_chargers(*, b_amperes: int) -> Scenario:
    """Return a and b sharing by charging power, b charging with b_amperes and a's car connected afterwards."""
    scenario = two_chargers(one_at_a_time=False, max_a=16, dynamic_order=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", b_amperes)
    scenario.set_charger("a", car_connected=True)
    return scenario


def test_charger_that_charges_keeps_its_room_from_a_car_connected_later() -> None:
    """With dynamic charging order, a waits for room beside b instead of taking it."""
    scenario = sharing_chargers(b_amperes=7)

    assert scenario.decide_many(9950, 3) == [[], [], []]
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]


def test_switch_over_shares_the_power_when_it_covers_the_reserve() -> None:
    """b at 11 A draws 3000 W above its reserve, which is not enough for the 4000 W reserve of a, but 4300 W is."""
    scenario = sharing_chargers(b_amperes=11)
    scenario.set_charger("b", charging_power_w=7000)
    assert scenario.decide(9950) == []

    scenario.set_charger("b", charging_power_w=8300)

    assert scenario.decide(9950) == current("b", 6) + activate("a")
    scenario.decide(9950)
    assert scenario.engine.chargers["a"].state is ChargerState.STARTING


def test_switch_over_when_the_free_power_alone_covers_the_reserve() -> None:
    """b at its minimum gives nothing up, and a starts beside it before b gets more current."""
    scenario = sharing_chargers(b_amperes=6)
    scenario.set_charger("b", charging_power_w=4100)

    assert scenario.decide(5000) == activate("a")


def test_no_switch_over_while_an_entry_above_the_group_waits_for_room() -> None:
    """The appliance above gets room from b first, by the fixed order."""
    scenario = Scenario(make_config(appliance("x", reserve_w=5000), chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=0))
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.exclude("x")
    scenario.charge("b", 12)
    scenario.set_charger("a", car_connected=True)
    scenario.set_charger("b", charging_power_w=8300)
    scenario.exclude()
    assert scenario.decide(9950) == current("b", 11)

    assert scenario.decide(9950) == current("b", 10)


def test_switch_over_waits_for_the_waiting_time() -> None:
    scenario = Scenario(make_config(chargers=(charger("a"), charger("b")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=120))
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 12)
    scenario.set_charger("a", car_connected=True)
    scenario.set_charger("b", charging_power_w=8300)

    assert scenario.decide_many(9100, 2) == [[], []]
    assert scenario.decide(9100) == current("b", 6) + activate("a")


def test_starting_charger_holds_its_reserve_from_the_charger_that_charges() -> None:
    """b does not take the power the car of a is about to draw, and no second switch-over is made on b's old charging power."""
    scenario = sharing_chargers(b_amperes=12)
    scenario.set_charger("b", charging_power_w=8300)
    scenario.decide(9100)

    assert scenario.decide(6500) == []

    scenario.set_charger("a", **CHARGING)
    scenario.set_charger("b", charging_power_w=4100)
    assert scenario.decide(6500) == current("a", 7)


def test_chargers_that_both_charge_share_in_the_configured_priority() -> None:
    """a is higher, so above the limit b loses its last ampere and then its first."""
    scenario = sharing_chargers(b_amperes=12)
    scenario.set_charger("b", charging_power_w=8300)
    scenario.decide(9100)
    scenario.set_charger("a", **CHARGING)

    assert scenario.decide(ABOVE_LIMIT) == deactivate("b")
    assert scenario.engine.chargers["a"].current_a == 6
    scenario.decide(9950)
    assert scenario.engine.chargers["b"].state is ChargerState.QUEUED


def test_car_that_pauses_keeps_the_minimum_current_through_its_grace_period() -> None:
    """Then it is done. A car that charges again within the grace period gets its amperes back."""
    scenario = Scenario(make_config(chargers=(charger("c", max_a=8),), wait_at_limit_s=0))
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 8)

    scenario.set_charger("c", actively_charging=False)
    assert scenario.decide(0) == current("c", 6)
    assert scenario.engine.chargers["c"].state is ChargerState.GRACE
    scenario.set_charger("c", **CHARGING)
    assert scenario.decide_many(0, 2) == [current("c", 7), current("c", 8)]

    scenario.set_charger("c", actively_charging=False)
    assert scenario.decide_many(0, 5) == [current("c", 6), [], [], [], []]
    assert scenario.decide(0) == deactivate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.DONE


def test_car_that_charges_again_after_its_grace_is_first_in_each_round() -> None:
    """With dynamic charging order a, below b in the configured priority, gets each ampere before b gets the same."""
    scenario = Scenario(make_config(chargers=(charger("b"), charger("a")), one_at_a_time=False, dynamic_order=True, wait_at_limit_s=0))
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 12)
    scenario.set_charger("a", car_connected=True)
    scenario.set_charger("b", charging_power_w=8300)
    assert scenario.decide(9950) == current("b", 6) + activate("a")
    scenario.set_charger("a", **CHARGING)
    assert scenario.decide_many(0, 2) == [current("b", 7), current("a", 7)]

    scenario.set_charger("a", actively_charging=False)
    assert scenario.decide(9950) == current("a", 6)
    scenario.set_charger("a", **CHARGING)

    assert scenario.decide_many(0, 3) == [current("a", 7), current("a", 8), current("b", 8)]
    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]


def test_excluded_charger_stops_at_once_and_never_charges() -> None:
    """All ampere steps off at once."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 8)

    scenario.set_charger("c", excluded=True)

    assert scenario.decide(0) == deactivate("c")
    assert scenario.decide_many(0, 3) == [[], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.EXCLUDED


def test_charger_with_a_fault_stops_at_once_and_charges_again_when_it_clears() -> None:
    """All ampere steps off at once, and from the minimum current again when the fault has cleared."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
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
    """A charger in fault draws no power, but it is tried again as soon as the fault clears, and keeps its place."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **CHARGING)
    assert scenario.decide(0) == activate("a")
    scenario.decide_many(0, 3)

    scenario.set_charger("a", actively_charging=False, fault=True)
    assert scenario.decide(0) == deactivate("a") + activate("b")
    assert list(scenario.engine.charging_priorities.values()) == [["a", "b"]]

    scenario.set_charger("a", fault=False)
    assert scenario.decide(0) == deactivate("b") + activate("a")


def test_charger_with_a_fault_that_counts_as_charging_lets_the_other_charge() -> None:
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **CHARGING)
    assert scenario.decide(0) == activate("a")

    scenario.set_charger("a", fault=True)
    scenario.set_charger("b", **CHARGING)

    assert scenario.decide(0) == deactivate("a") + activate("b")


def test_fault_neither_arms_nor_ends_the_override() -> None:
    """The car charges outside the window again when the fault clears."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CAR_DISCONNECTED)
    scenario.set_charger("c", **CHARGING, window_override=True, fault=True)

    assert scenario.decide(0) == []
    assert scenario.overrides.armed == []

    scenario.set_charger("c", car_connected=False, car_disconnected=True, override_armed=True)
    assert scenario.decide(0) == []
    assert scenario.overrides.ended == []

    scenario.set_charger("c", car_connected=True, car_disconnected=False, fault=False)
    assert scenario.decide(0) == activate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.OVERRIDE


def test_charger_charges_only_inside_its_charging_window() -> None:
    """Charging stops at the first decision after the window ends."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c", max_a=8, window="22:00-22:03"),),
            wait_at_limit_s=0,
        ),
        start=datetime(2026, 11, 7, 21, 58, tzinfo=UTC),
    )
    scenario.set_charger("c", **CHARGING)

    assert scenario.decide_many(0, 5) == [
        [],
        activate("c"),
        current("c", 7),
        current("c", 8),
        deactivate("c"),
    ]


def window_ending_scenario(**reading) -> Scenario:
    """Return charger c, 6 A to 10 A, charging at 8 A when its window ends at 22:03."""
    scenario = Scenario(
        make_config(
            chargers=(charger("c", max_a=10, window="22:00-22:03"),),
            wait_at_limit_s=0,
        ),
        start=datetime(2026, 11, 7, 21, 58, tzinfo=UTC),
    )
    scenario.set_charger("c", **CHARGING, finish_after_window=True, **reading)
    assert scenario.decide_many(0, 4) == [
        [],
        activate("c"),
        current("c", 7),
        current("c", 8),
    ]
    return scenario


def test_charger_finishes_ongoing_charging_after_its_window() -> None:
    """It is regulated as before, until it stops charging."""
    scenario = window_ending_scenario()

    assert scenario.decide(0) == current("c", 9)
    assert scenario.engine.chargers["c"].state is ChargerState.FINISHING
    assert scenario.decide(ABOVE_LIMIT) == current("c", 8)
    scenario.set_charger("c", actively_charging=False)
    assert scenario.decide_many(0, 5) == [current("c", 6), [], [], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.GRACE
    assert scenario.decide(0) == deactivate("c")
    assert scenario.engine.chargers["c"].state is not ChargerState.FINISHING


def test_charger_is_not_turned_on_again_after_its_window() -> None:
    """Whatever stopped it, here a disconnected car."""
    scenario = window_ending_scenario()
    scenario.set_charger("c", car_connected=False)

    assert scenario.decide(0) == deactivate("c")
    scenario.set_charger("c", car_connected=True)
    assert scenario.decide_many(0, 3) == [[], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.OUTSIDE_WINDOW


def test_charger_on_trial_when_its_window_ends_does_not_finish() -> None:
    scenario = Scenario(
        make_config(chargers=(charger("c", window="22:00-22:02"),), wait_at_limit_s=0),
        start=datetime(2026, 11, 7, 21, 59, tzinfo=UTC),
    )
    scenario.set_charger("c", finish_after_window=True)

    assert scenario.decide_many(0, 3) == [activate("c"), [], deactivate("c")]


def test_override_lasts_until_a_connected_car_is_disconnected() -> None:
    """A window that starts does not end it, nor a car sensor without evidence."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CAR_DISCONNECTED)
    scenario.set_charger("c", **CHARGING, window_override=True, car_connected=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.overrides.armed == ["c"]
    assert scenario.engine.chargers["c"].state is ChargerState.OVERRIDE
    assert scenario.decide(0, after=timedelta(hours=20)) == []
    assert scenario.overrides.ended == []

    scenario.set_charger("c", actively_charging=False, car_connected=False, override_armed=True)
    assert scenario.decide(0) == []
    assert scenario.overrides.ended == []
    scenario.set_charger("c", car_disconnected=True)
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]
    assert scenario.engine.chargers["c"].state is ChargerState.OUTSIDE_WINDOW


def test_override_ends_when_the_activated_charger_stops_charging() -> None:
    """It arms only when the charger was activated and charging."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CHARGING_STOPPED)
    scenario.set_charger("c", **CHARGING, window_override=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.overrides.armed == []
    assert scenario.decide(0) == []
    assert scenario.overrides.armed == ["c"]

    scenario.set_charger("c", actively_charging=False, override_armed=True, charging_stopped=True)
    assert scenario.decide_many(0, 5) == [[]] * 5
    assert scenario.overrides.ended == []
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]


def test_override_gives_a_reactivated_car_time_to_start_charging() -> None:
    """As before a charger is bypassed, two windows after it was activated."""
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CHARGING_STOPPED)
    scenario.set_charger("c", **CHARGING, window_override=True, override_armed=True)
    scenario.decide(0)
    assert scenario.decide(12000) == deactivate("c")
    assert scenario.decide(0) == activate("c")

    scenario.set_charger("c", actively_charging=False, charging_stopped=True)
    assert scenario.decide(0) == []
    assert scenario.overrides.ended == []
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]


def test_override_gives_a_cloud_controlled_charger_its_start_delay() -> None:
    scenario = one_charger(max_a=6, window="22:00-06:00", override_ends=OverrideEnd.CHARGING_STOPPED, cloud_controlled=True)
    scenario.set_charger("c", window_override=True, override_armed=True, charging_stopped=True)
    assert scenario.decide(0) == activate("c")

    assert scenario.decide_many(0, 4) == [[], [], [], []]
    assert scenario.overrides.ended == []
    assert scenario.decide(0) == deactivate("c")
    assert scenario.overrides.ended == ["c"]


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
    scenario.set_charger("c", **CHARGING, window_override=True)
    assert scenario.decide(0) == activate("c")

    scenario.set_charger("c", window_override=False)

    assert scenario.decide(0) == deactivate("c")


def test_override_without_window_has_no_effect() -> None:
    """The charger may always charge, and the override stays."""
    scenario = one_charger(max_a=6)
    scenario.set_charger("c", **CHARGING, window_override=True)

    assert scenario.decide(0) == activate("c")
    assert scenario.decide(0, after=timedelta(days=2)) == []


def test_penalty_and_safe_state_deactivate_the_chargers() -> None:
    """All at once, and the charger starts again afterwards."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
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
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 7)

    assert scenario.decide(9900, true=("morning",)) == off("h:morning") + current("c", 6)


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


def test_each_charger_group_has_its_own_place_and_one_at_a_time() -> None:
    """Activating b does not deactivate a, which is in another group."""
    scenario = two_groups()
    scenario.set_charger("a", **CHARGING)
    scenario.set_charger("b", **CHARGING)

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
