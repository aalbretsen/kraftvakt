"""Scenario tests for EV charging in the regulation engine."""

from datetime import UTC, datetime, timedelta

from custom_components.kraftvakt.regulation.charging import (
    ChargerState,
    ChargerStatus,
)
from custom_components.kraftvakt.regulation.model import ActivateCharger

from .configs import appliance, charger, charger_group, make_config
from .scenario import (
    START,
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
    return Scenario(
        make_config(chargers=(charger("c", **settings),), wait_at_limit_s=0)
    )


def two_chargers(*, one_at_a_time: bool, max_a: int = 7) -> Scenario:
    """Return a scenario with chargers a and b, in that priority, without waiting."""
    return Scenario(
        make_config(
            chargers=(charger("a", max_a=max_a), charger("b", max_a=max_a)),
            one_at_a_time=one_at_a_time,
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
    scenario = Scenario(
        make_config(chargers=(charger("c", max_a=6),), wait_at_limit_s=300)
    )
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


def test_charger_that_does_not_draw_power_is_bypassed() -> None:
    """Kept at the minimum current while it is tried, and not deactivated."""
    scenario = one_charger()

    assert scenario.decide_many(0, 5) == [activate("c"), [], [], [], []]
    assert scenario.engine.chargers["c"].bypassed


def test_appliance_below_is_turned_on_while_a_charger_is_tried() -> None:
    """A charger on trial gets no more current and does not hold back the
    appliances below «EV charging»."""
    scenario = Scenario(
        make_config(
            "x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0
        )
    )

    assert scenario.decide_many(0, 3) == [activate("c"), on("x"), []]
    assert scenario.engine.chargers["c"].current_a == 6


def test_charger_that_starts_charging_makes_room_below() -> None:
    """The appliance turned on below while the charger was tried is switched
    off when the charger needs room for more current."""
    scenario = Scenario(
        make_config(
            "x", chargers=(charger("c"),), priority=("ev", "x"), wait_at_limit_s=0
        )
    )
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
    assert scenario.decide_many(0, 3) == [activate("c"), on("d"), []]
    assert scenario.engine.chargers["c"].bypassed

    assert scenario.decide_many(9950, 2, true=("up",)) == [off("d:up"), []]
    assert scenario.engine.chargers["c"].current_a == 6


def test_bypassed_charger_starts_again_when_the_car_draws_power() -> None:
    """It is no longer bypassed and gets more current."""
    scenario = one_charger()
    scenario.decide_many(0, 3)

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


def test_bypassed_charger_is_not_switched_off_above_the_limit() -> None:
    """Switching it off would not lower the consumption."""
    scenario = Scenario(make_config("x", chargers=(charger("c"),), wait_at_limit_s=0))
    scenario.turn_on("x")
    scenario.set_charger("c", **NO_CAR)
    assert scenario.decide(0) == []
    scenario.set_charger("c", car_connected=None, actively_charging=False)
    assert scenario.decide(0) == activate("c")
    scenario.set_charger("c", **NO_CAR)
    scenario.decide(0)

    assert scenario.decide(ABOVE_LIMIT) == off("x")
    assert scenario.decide(ABOVE_LIMIT) == []


def test_bypassed_charger_does_not_stand_in_the_way_one_at_a_time() -> None:
    """The other is activated and it is deactivated."""
    scenario = two_chargers(one_at_a_time=True)

    assert scenario.decide_many(0, 3) == [
        activate("a"),
        [],
        deactivate("a") + activate("b"),
    ]
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]


def full_cars_after_both_were_tried() -> Scenario:
    """Return two chargers with full cars, one at a time: a rests, b is tried."""
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
        [],
    ]
    return scenario


def test_chargers_with_full_cars_do_not_take_turns_forever() -> None:
    """A charger that did not charge rests 15 minutes before it is tried again.

    a did not charge at minute 3 and b at minute 5.
    """
    scenario = full_cars_after_both_were_tried()

    assert scenario.decide_many(0, 12) == [[]] * 12
    assert scenario.engine.chargers["a"].bypassed
    assert scenario.engine.chargers["b"].bypassed
    assert scenario.decide(0) == deactivate("b") + activate("a")


def test_rest_grows_while_the_car_does_not_charge() -> None:
    """15, 30 and then 60 minutes after the charger did not charge."""
    scenario = full_cars_after_both_were_tried()

    activated = {"a": [], "b": []}
    for minute in range(6, 130):
        for command in scenario.decide(0):
            if isinstance(command, ActivateCharger):
                activated[command.charger_id].append(minute)

    assert activated == {"a": [18, 50, 112], "b": [20, 52, 114]}


def test_car_connected_again_is_tried_at_once() -> None:
    scenario = full_cars_after_both_were_tried()
    scenario.set_charger("a", car_connected=False)
    assert scenario.decide(0) == []

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(0) == deactivate("b") + activate("a")


def test_current_priority_starts_as_configured_at_each_start() -> None:
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.decide(0)
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]

    scenario.engine.start(scenario.now)

    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]


def test_priority_is_corrected_when_a_charger_has_all_ampere_steps_on() -> None:
    """A charger that gets a car moves up again when another has all on."""
    scenario = two_chargers(one_at_a_time=False)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)

    assert scenario.decide_many(0, 3) == [activate("b"), current("b", 7), []]
    assert scenario.engine.charging_priorities["ev"] == ["b", "a"]

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide(0) == activate("a")
    assert scenario.engine.charging_priorities["ev"] == ["a", "b"]
    assert scenario.decide(ABOVE_LIMIT) == current("b", 6)


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
    """Until it stops, whatever the priority."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    assert scenario.decide(0) == activate("b")

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(0, 3) == [current("b", 7), [], []]
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED

    scenario.set_charger("b", actively_charging=False, car_connected=False)

    assert scenario.decide(0) == (current("b", 6) + deactivate("b") + activate("a"))
    assert scenario.engine.chargers["a"].state is not ChargerState.QUEUED


def test_first_charger_in_the_current_priority_is_chosen() -> None:
    """When none charges, also when both have a car."""
    scenario = two_chargers(one_at_a_time=True)

    assert scenario.decide(0) == activate("a")
    assert scenario.engine.chargers["b"].current_a is None


def test_charger_that_counts_as_charging_keeps_the_other_waiting() -> None:
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("b", actively_charging=True)

    assert scenario.decide(0) == activate("b")
    assert scenario.engine.chargers["a"].state is ChargerState.QUEUED


def test_excluded_charger_that_counts_as_charging_lets_the_other_charge() -> None:
    """Only a charger that is allowed to charge holds back the others."""
    scenario = two_chargers(one_at_a_time=True)
    scenario.set_charger("b", actively_charging=True, excluded=True)

    assert scenario.decide(0) == activate("a")
    assert scenario.engine.chargers["a"].state is not ChargerState.QUEUED


def test_new_car_makes_room_for_the_power_reserve() -> None:
    """A new car is not activated until there is room for the power reserve.

    A was bypassed and is behind b, so the room comes from the amperes of b
    after its first, which are below the first of a when interleaved.
    """
    scenario = two_chargers(one_at_a_time=False, max_a=16)
    scenario.set_charger("a", **NO_CAR)
    scenario.set_charger("b", **CHARGING)
    scenario.charge("b", 8)

    scenario.set_charger("a", car_connected=True)

    assert scenario.decide_many(7000, 3) == [current("b", 7), current("b", 6), []]
    assert scenario.decide(5500) == activate("a")


def test_excluded_charger_stops_at_once_and_never_charges() -> None:
    """All ampere steps off at once."""
    scenario = one_charger()
    scenario.set_charger("c", **CHARGING)
    scenario.charge("c", 8)

    scenario.set_charger("c", excluded=True)

    assert scenario.decide(0) == deactivate("c")
    assert scenario.decide_many(0, 3) == [[], [], []]
    assert scenario.engine.chargers["c"].state is ChargerState.EXCLUDED


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


def test_override_allows_charging_until_the_next_window_starts() -> None:
    """The switch is set back when the override ends."""
    scenario = one_charger(max_a=6, window="22:00-22:05")
    scenario.set_charger(
        "c", **CHARGING, window_override=True, override_switched_on_at=START
    )

    assert scenario.decide(0) == activate("c")
    assert scenario.engine.chargers["c"].state is ChargerState.OVERRIDE
    assert scenario.decide(0, after=timedelta(hours=9, minutes=58)) == []
    assert scenario.ended_overrides == []
    assert scenario.decide(0) == []
    assert scenario.ended_overrides == ["c"]
    assert scenario.engine.chargers["c"].state is ChargerState.CHARGING
    scenario.set_charger("c", window_override=False)
    assert scenario.decide(0, after=timedelta(minutes=4)) == []
    assert scenario.decide(0) == deactivate("c")


def test_override_ends_also_during_a_penalty() -> None:
    """The override is evaluated at every decision."""
    scenario = one_charger(max_a=6, window="12:30-13:00")
    scenario.set_charger("c", window_override=True, override_switched_on_at=START)
    scenario.decide(12000, tariff=12000)
    assert scenario.decide(12000, tariff=12000) == deactivate("c")
    assert scenario.engine.penalty.active

    assert scenario.decide(12000, tariff=12000, after=timedelta(minutes=28)) == []
    assert scenario.ended_overrides == ["c"]


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


def test_variant_switch_makes_room_by_switching_off_a_ampere_step() -> None:
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

    assert scenario.decide(9900, true=("morning",)) == off("h:morning") + current(
        "c", 6
    )


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
