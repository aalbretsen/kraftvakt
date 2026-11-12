"""Scenario tests for variants of appliances."""

from .configs import appliance, make_config
from .scenario import Scenario, off, on


def morning_heater_config(**settings):
    """The heater has priority over b in the morning, and is last otherwise."""
    return make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
        **settings,
    )


def test_current_variant_decides_the_place() -> None:
    """Only the entry of the current variant takes part."""
    in_the_morning = Scenario(morning_heater_config(wait_at_limit_s=0))
    otherwise = Scenario(morning_heater_config(wait_at_limit_s=0))

    assert in_the_morning.decide_many(1000, 2, true=("morning",)) == [
        on("heater:morning"),
        on("b"),
    ]
    assert otherwise.decide_many(1000, 2) == [on("b"), on("heater")]


def test_current_variant_is_found_at_each_decision() -> None:
    """No current variant before the first decision."""
    scenario = Scenario(morning_heater_config())
    assert scenario.engine.current_variants == {}

    scenario.decide(None, true=("morning",))
    assert scenario.engine.current_variants == {}

    scenario.decide(1000)
    assert scenario.engine.current_variants == {"heater": None, "b": None}

    scenario.decide(1000, true=("morning",))
    assert scenario.engine.current_variants == {"heater": "morning", "b": None}


def test_restart_forgets_the_current_variant() -> None:
    """The current variant is found again at the first decision."""
    scenario = Scenario(morning_heater_config())
    scenario.decide(1000, true=("morning",))

    scenario.engine.start(scenario.now)

    assert scenario.engine.current_variants == {}


def test_variant_switch_above_the_limit_switches_off_nothing_more() -> None:
    """Above the limit, nothing more is switched off when a variant switch has
    switched something off."""
    scenario = Scenario(morning_heater_config(wait_at_limit_s=0))
    scenario.turn_on("b", "heater")

    assert scenario.decide(10500, true=("morning",)) == off("heater:morning")
    assert scenario.engine.appliances_on == {"b"}


def test_switch_of_an_appliance_that_is_off_does_not_stop_the_switch_off() -> None:
    """The turn-off action of the new variant does not lower the consumption,
    so the lowest slot that is on is still switched off above the limit."""
    scenario = Scenario(morning_heater_config(wait_at_limit_s=0))
    scenario.turn_on("b")

    assert scenario.decide(10500, true=("morning",)) == off("heater:morning", "b")


def test_switch_above_the_lowest_on_makes_room() -> None:
    """C is switched off to give room for D, which comes back on."""
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
    scenario.turn_on("a", "b", "c")

    assert scenario.decide(9000, true=("up",)) == off("c") + on("d:up")
    assert scenario.decide(9000, true=("up",)) == on("c")


def swim_spa_config(*, reserve_w: int | None = None):
    """The spa moves from last to just below a when swimming."""
    return make_config(
        "a",
        "b",
        "c",
        appliance("spa", reserve_w=reserve_w, variants=("swim",)),
        priority=("a", "spa:swim", "b", "c", "spa"),
        wait_at_limit_s=0,
    )


def test_room_is_made_one_slot_per_decision_until_the_variant_fits() -> None:
    """Within the turn-on margin, the slots below are switched off one at a time.

    Nothing more than the room is switched off at the decision of the switch,
    and nothing above it is switched off.
    """
    scenario = Scenario(swim_spa_config())
    scenario.turn_on("a", "b", "c")

    assert scenario.decide_many(9950, 3, true=("swim",)) == [
        off("spa:swim", "c"),
        off("b"),
        [],
    ]
    assert scenario.decide(9000, true=("swim",)) == on("spa:swim")
    assert scenario.engine.appliances_on == {"a", "spa"}


def test_room_is_made_for_the_power_reserve_of_the_switched_appliance() -> None:
    scenario = Scenario(swim_spa_config(reserve_w=3000))
    scenario.turn_on("a", "b", "c")

    assert scenario.decide_many(8000, 2, true=("swim",)) == [
        off("spa:swim", "c"),
        off("b"),
    ]
    assert scenario.decide(7000, true=("swim",)) == on("spa:swim")


def test_room_made_above_the_limit_is_enough_for_one_decision() -> None:
    """Making room is a switch-off, so nothing more is switched off for being
    above the limit at the same decision."""
    scenario = Scenario(
        make_config(
            "a",
            "b",
            appliance("d", variants=("up",)),
            priority=("a", "d:up", "b", "d"),
        )
    )
    scenario.turn_on("a", "b")

    assert scenario.decide(10500, true=("up",)) == off("d:up", "b")
    assert scenario.decide(10500, true=("up",)) == off("a")


def test_appliance_that_was_on_is_switched_off_and_on_again() -> None:
    """Off after the switch, then on in the normal way after waiting."""
    scenario = Scenario(morning_heater_config())
    scenario.turn_on("b", "heater")

    assert scenario.decide(8000, true=("morning",)) == off("heater:morning")
    assert scenario.engine.appliances_on == {"b"}
    assert scenario.decide_many(8000, 4, true=("morning",)) == [
        [],
        [],
        [],
        on("heater:morning"),
    ]


def test_appliance_turned_off_and_on_at_the_same_decision_only_gets_turn_on() -> None:
    """Without waiting, an appliance that was on comes on again at once, with
    the turn-on action of its new variant and no turn-off before it."""
    scenario = Scenario(morning_heater_config(wait_at_limit_s=0))
    scenario.turn_on("b", "heater")

    assert scenario.decide(1000, true=("morning",)) == on("heater:morning")
    assert scenario.engine.appliances_on == {"b", "heater"}


def test_switch_below_the_lowest_on_turns_nothing_off() -> None:
    scenario = Scenario(
        make_config(
            "a",
            "b",
            appliance("d", variants=("down",)),
            priority=("a", "d", "b", "d:down"),
            wait_at_limit_s=0,
        )
    )
    scenario.turn_on("a")

    assert scenario.decide(9000, true=("down",)) == off("d:down") + on("b")


def heater_moving_down_config():
    """The heater is below b, and lower still with its variant."""
    return make_config(
        appliance("heater", variants=("low",)),
        "b",
        priority=("b", "heater", "heater:low"),
    )


def test_switch_restarts_the_waiting_time_of_the_appliance() -> None:
    """The waiting time for the appliance starts again."""
    scenario = Scenario(heater_moving_down_config())
    scenario.turn_on("b")
    assert scenario.decide_many(8000, 2) == [[], []]

    assert scenario.decide(8000, true=("low",)) == off("heater:low")
    assert scenario.decide_many(8000, 4, true=("low",)) == [
        [],
        [],
        [],
        on("heater:low"),
    ]


def test_switch_resets_the_increasing_waiting_time() -> None:
    """The counter for increasing waiting time is reset."""
    scenario = Scenario(heater_moving_down_config())
    scenario.turn_on("b", "heater")
    assert scenario.decide(10500) == off("heater")
    assert scenario.decide(0) == on("heater")
    assert scenario.decide(10500) == off("heater")

    assert scenario.decide(0, true=("low",)) == on("heater:low")


def test_several_switches_are_handled_one_by_one_by_new_place() -> None:
    """E makes room by switching off D, which has to go off anyway."""
    scenario = Scenario(
        make_config(
            "a",
            "b",
            appliance("d", variants=("down",)),
            appliance("e", variants=("up",)),
            priority=("a", "e:up", "b", "d", "e", "d:down"),
            wait_at_limit_s=0,
        )
    )
    scenario.turn_on("a", "b", "d")

    assert scenario.decide(10000, true=("down", "up")) == off("e:up", "d:down")
    assert scenario.engine.appliances_on == {"a", "b"}


def test_several_appliances_switching_up_switch_off_one_each() -> None:
    scenario = Scenario(
        make_config(
            "a",
            "b",
            "c",
            appliance("d", variants=("up",)),
            appliance("e", variants=("up_too",)),
            priority=("d:up", "e:up_too", "a", "b", "c", "d", "e"),
            wait_at_limit_s=0,
        )
    )
    scenario.turn_on("a", "b", "c")

    assert scenario.decide(10000, true=("up", "up_too")) == off(
        "d:up", "c", "e:up_too", "b"
    )


def test_switch_of_an_appliance_that_is_off_gives_the_new_turn_off_action() -> None:
    """Also a switch back to the appliance itself."""
    scenario = Scenario(heater_moving_down_config())
    scenario.turn_on("b")

    assert scenario.decide(10000, true=("low",)) == off("heater:low")
    assert scenario.decide(10000, true=("low",)) == []
    assert scenario.decide(10000) == off("heater")


def test_first_decision_gives_the_turn_off_action_of_the_current_variant() -> None:
    """The start turns the appliance off as the appliance itself does it."""
    scenario = Scenario(heater_moving_down_config())
    scenario.decide(10000)
    scenario.decide(10000, true=("low",))

    assert scenario.engine.start(scenario.now) == off("heater", "b")
    assert scenario.decide(10000, true=("low",)) == off("heater:low")


def test_everything_off_follows_the_current_variant() -> None:
    """Stop and the safe state turn off as the current variant does."""
    scenario = Scenario(heater_moving_down_config())
    scenario.decide(10000, true=("low",))

    assert scenario.decide(None, sensor_lost=True) == off("heater:low", "b")
    assert scenario.engine.stop() == off("heater:low", "b")
