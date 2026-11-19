"""Unit tests for the steps built from the priority list."""

from datetime import UTC, datetime

from custom_components.kraftvakt.config_model import Charger
from custom_components.kraftvakt.regulation.charging import ChargerReading, ChargingState
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

from .configs import appliance, make_config


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

    steps = build_steps(config, current_variants={}, appliances_on={"b"})

    assert steps == [
        Step(ApplianceStepKey("a"), False, 2500),
        Step(ApplianceStepKey("b"), True, None),
        Step(ApplianceStepKey("c"), False, None),
    ]


def test_appliance_that_is_on_and_settling_holds_its_reserve() -> None:
    config = make_config(appliance("a", reserve_w=2500), appliance("b", reserve_w=1000))
    settling = {ApplianceStepKey("a"), ApplianceStepKey("b")}

    steps = build_steps(config, {}, {"a"}, settling=settling)

    assert [step.holds_reserve for step in steps] == [True, False]


def test_only_the_current_variant_gets_a_slot() -> None:
    """The other entries of the appliance are skipped."""
    config = make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
    )

    assert keys(build_steps(config, {}, ())) == ["b", "heater"]
    assert keys(build_steps(config, {"heater": "morning"}, ())) == [
        "heater",
        "b",
    ]


def test_each_charger_group_entry_is_replaced_by_its_ampere_steps() -> None:
    config = make_config("a", "b", priority=("a", "ev", "b", "@g2"))

    def ampere_step(name: str) -> Step:
        return Step(ApplianceStepKey(name), False, 4.0)

    assert keys(build_steps(config, {}, ())) == ["a", "b"]
    steps = build_steps(
        config,
        {},
        (),
        ampere_steps_by_group={"ev": [ampere_step("ev")], "g2": [ampere_step("g2")]},
    )
    assert keys(steps) == ["a", "ev", "b", "g2"]


def charger(charger_id: str, min_a: int, max_a: int, min_current_power_w: int = 4000) -> Charger:
    return Charger(charger_id, min_current_a=min_a, max_current_a=max_a, min_current_power_w=min_current_power_w)


def charging_state(
    ampere_steps_on: dict[str, int],
    may_charge: set[str],
    *,
    held_at_min: set[str] | None = None,
    actively_charging: set[str] | None = None,
    starting: set[str] | None = None,
    measured_power_per_ampere_w: dict[str, float] | None = None,
) -> ChargingState:
    return ChargingState(
        ampere_steps_on=ampere_steps_on,
        may_charge=may_charge,
        held_at_min=held_at_min or set(),
        last_readings={charger_id: ChargerReading(actively_charging=True) for charger_id in actively_charging or ()},
        starting=dict.fromkeys(starting or (), datetime(2026, 1, 1, tzinfo=UTC)),
        measured_power_per_ampere_w=measured_power_per_ampere_w or {},
    )


def test_ampere_steps_are_interleaved_between_chargers() -> None:
    """One per ampere, first of each charger, then second."""
    chargers = [charger("a", 6, 8), charger("b", 10, 11), charger("c", 6, 6)]

    steps = ampere_steps("ev", [chargers], charging_state({}, {"a", "b", "c"}))

    assert [(step.key.charger_id, step.key.index) for step in steps] == [
        ("a", 0),
        ("b", 0),
        ("c", 0),
        ("a", 1),
        ("b", 1),
        ("a", 2),
    ]


def test_first_ampere_step_needs_the_power_at_minimum_current_and_the_others_the_power_per_ampere() -> None:
    """Before the power per ampere is measured, it is the power at minimum current divided by the minimum current."""
    chargers = [charger("a", 6, 8, min_current_power_w=3600), charger("b", 6, 7, min_current_power_w=1380)]
    state = charging_state({"a": 2}, {"a", "b"}, actively_charging={"a"}, measured_power_per_ampere_w={"a": 700})

    steps = ampere_steps("ev", [chargers], state)

    assert steps == [
        Step(AmpereStepKey("a", 0), True, 3600, can_turn_off=True, group_id="ev"),
        Step(AmpereStepKey("b", 0), False, 1380, can_turn_off=False, group_id="ev"),
        Step(AmpereStepKey("a", 1), True, 700, can_turn_off=True, group_id="ev"),
        Step(AmpereStepKey("b", 1), False, 230, can_turn_off=False, group_id="ev"),
        Step(AmpereStepKey("a", 2), False, 700, can_turn_off=True, group_id="ev"),
    ]


def test_ampere_steps_of_chargers_that_may_not_charge_or_be_switched_off() -> None:
    steps = ampere_steps("ev", [[charger("a", 6, 6), charger("b", 6, 6)]], charging_state({"a": 1}, {"b"}, actively_charging={"b"}))

    assert [(step.can_turn_on, step.can_turn_off) for step in steps] == [
        (False, False),
        (True, True),
    ]


def test_charger_held_at_minimum_can_only_get_its_first_ampere_step() -> None:
    steps = ampere_steps("ev", [[charger("a", 6, 8)]], charging_state({"a": 1}, {"a"}, held_at_min={"a"}))

    assert [step.can_turn_on for step in steps] == [True, False, False]


def test_only_the_first_ampere_step_of_a_starting_charger_holds_its_reserve() -> None:
    state = charging_state({"a": 1}, {"a", "b"}, held_at_min={"a"}, starting={"a"})

    steps = ampere_steps("ev", [[charger("a", 6, 7), charger("b", 6, 6)]], state)

    assert [step.holds_reserve for step in steps] == [True, False, False]


def test_ampere_step_that_is_on_and_settling_holds_its_reserve() -> None:
    settling = {AmpereStepKey("a", 1), AmpereStepKey("a", 2)}

    steps = ampere_steps("ev", [[charger("a", 6, 8)]], charging_state({"a": 2}, {"a"}), settling)

    assert [step.holds_reserve for step in steps] == [False, True, False]
