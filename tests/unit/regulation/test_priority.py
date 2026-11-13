"""Unit tests for the steps built from the priority list."""

from custom_components.kraftvakt.config_model import Charger
from custom_components.kraftvakt.regulation.model import (
    AmpereStepKey,
    ApplianceStepKey,
    Step,
)
from custom_components.kraftvakt.regulation.priority import (
    ampere_steps,
    build_steps,
    current_variant,
)
from custom_components.kraftvakt.regulation.waiting import RepeatedTurnOnGrowth

from .configs import appliance, make_config

APPLIANCE_GROWTH = RepeatedTurnOnGrowth.from_waiting_at_limit(300, 0.5, 4)
AMPERE_STEP_GROWTH = RepeatedTurnOnGrowth.from_waiting_at_limit(300, 1.0, 5)


def keys(steps: list[Step]) -> list[str]:
    return [step.key.appliance_id for step in steps]


def test_appliance_without_true_condition_is_its_own_current_variant() -> None:
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {}) is None
    assert current_variant(heater, {"morning": False, "evening": False}) is None


def test_topmost_true_condition_gives_current_variant() -> None:
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {"evening": True}) == "evening"
    assert current_variant(heater, {"morning": True, "evening": True}) == "morning"


def test_slots_follow_the_priority_list() -> None:
    config = make_config(appliance("a", reserve_w=2500), "b", "c")

    steps = build_steps(
        config, current_variants={}, appliances_on={"b"}, growth=APPLIANCE_GROWTH
    )

    assert steps == [
        Step(ApplianceStepKey("a"), False, 2500, APPLIANCE_GROWTH),
        Step(ApplianceStepKey("b"), True, None, APPLIANCE_GROWTH),
        Step(ApplianceStepKey("c"), False, None, APPLIANCE_GROWTH),
    ]


def test_only_the_current_variant_gets_a_slot() -> None:
    """The other entries of the appliance are skipped."""
    config = make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
    )

    assert keys(build_steps(config, {}, (), APPLIANCE_GROWTH)) == ["b", "heater"]
    assert keys(build_steps(config, {"heater": "morning"}, (), APPLIANCE_GROWTH)) == [
        "heater",
        "b",
    ]


def test_each_charger_group_entry_is_replaced_by_its_ampere_steps() -> None:
    config = make_config("a", "b", priority=("a", "ev", "b", "@g2"))

    def ampere_step(name: str) -> Step:
        return Step(ApplianceStepKey(name), False, 4.0, APPLIANCE_GROWTH)

    assert keys(build_steps(config, {}, (), APPLIANCE_GROWTH)) == ["a", "b"]
    steps = build_steps(
        config,
        {},
        (),
        APPLIANCE_GROWTH,
        ampere_steps_by_group={"ev": [ampere_step("ev")], "g2": [ampere_step("g2")]},
    )
    assert keys(steps) == ["a", "ev", "b", "g2"]


def charger(charger_id: str, min_a: int, max_a: int, reserve_w: int = 4000) -> Charger:
    return Charger(
        charger_id, min_current_a=min_a, max_current_a=max_a, power_reserve_w=reserve_w
    )


def test_ampere_steps_are_interleaved_between_chargers() -> None:
    """One per ampere, first of each charger, then second."""
    chargers = [charger("a", 6, 8), charger("b", 10, 11), charger("c", 6, 6)]

    steps = ampere_steps(
        chargers,
        {},
        may_charge={"a", "b", "c"},
        on_trial=(),
        bypassed=(),
        growth=AMPERE_STEP_GROWTH,
    )

    assert [(step.key.charger_id, step.key.index) for step in steps] == [
        ("a", 0),
        ("b", 0),
        ("c", 0),
        ("a", 1),
        ("b", 1),
        ("a", 2),
    ]


def test_only_the_first_ampere_step_has_the_power_reserve() -> None:
    """All of them get the growth of the ampere steps."""
    steps = ampere_steps(
        [charger("a", 6, 8, reserve_w=3500)],
        {"a": 2},
        {"a"},
        (),
        (),
        AMPERE_STEP_GROWTH,
    )

    assert steps == [
        Step(AmpereStepKey("a", 0), True, 3500, AMPERE_STEP_GROWTH),
        Step(AmpereStepKey("a", 1), True, None, AMPERE_STEP_GROWTH),
        Step(AmpereStepKey("a", 2), False, None, AMPERE_STEP_GROWTH),
    ]


def test_ampere_steps_of_chargers_that_may_not_charge_or_are_bypassed() -> None:
    steps = ampere_steps(
        [charger("a", 6, 6), charger("b", 6, 6)],
        {"a": 1},
        may_charge={"b"},
        on_trial=(),
        bypassed={"a"},
        growth=AMPERE_STEP_GROWTH,
    )

    assert [(step.can_turn_on, step.can_turn_off) for step in steps] == [
        (False, False),
        (True, True),
    ]


def test_charger_on_trial_can_only_get_its_first_ampere_step() -> None:
    steps = ampere_steps(
        [charger("a", 6, 8)],
        {"a": 1},
        may_charge={"a"},
        on_trial={"a"},
        bypassed=(),
        growth=AMPERE_STEP_GROWTH,
    )

    assert [step.can_turn_on for step in steps] == [True, False, False]
