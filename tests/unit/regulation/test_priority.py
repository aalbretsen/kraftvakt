"""Unit tests for the slots built from the priority list."""

from custom_components.kraftvakt.config_model import Charger
from custom_components.kraftvakt.regulation.model import (
    ApplianceSlotKey,
    ChargerSlotKey,
    Slot,
)
from custom_components.kraftvakt.regulation.priority import (
    build_slots,
    current_variant,
    fictive_slots,
)
from custom_components.kraftvakt.regulation.waiting import CyclingSteps

from .configs import appliance, make_config

APPLIANCE_CYCLING = CyclingSteps.from_seconds(120, 900)
FICTIVE_APPLIANCE_CYCLING = CyclingSteps.from_seconds(300, 1800)


def keys(slots: list[Slot]) -> list[str]:
    return [slot.key.appliance_id for slot in slots]


def test_appliance_without_true_condition_is_its_own_current_variant() -> None:
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {}) is None
    assert current_variant(heater, {"morning": False, "evening": False}) is None


def test_topmost_true_condition_gives_current_variant() -> None:
    """The variant of the topmost true expression applies."""
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {"evening": True}) == "evening"
    assert current_variant(heater, {"morning": True, "evening": True}) == "morning"


def test_slots_follow_the_priority_list() -> None:
    config = make_config(appliance("a", reserve_w=2500), "b", "c")

    slots = build_slots(
        config, current_variants={}, appliances_on={"b"}, cycling=APPLIANCE_CYCLING
    )

    assert slots == [
        Slot(ApplianceSlotKey("a"), False, 2500, APPLIANCE_CYCLING),
        Slot(ApplianceSlotKey("b"), True, None, APPLIANCE_CYCLING),
        Slot(ApplianceSlotKey("c"), False, None, APPLIANCE_CYCLING),
    ]


def test_only_the_current_variant_gets_a_slot() -> None:
    """The other entries of the appliance are skipped."""
    config = make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
    )

    assert keys(build_slots(config, {}, (), APPLIANCE_CYCLING)) == ["b", "heater"]
    assert keys(build_slots(config, {"heater": "morning"}, (), APPLIANCE_CYCLING)) == [
        "heater",
        "b",
    ]


def test_ev_charging_entry_is_replaced_by_charger_slots() -> None:
    config = make_config("a", "b", priority=("a", "ev", "b"))
    charger_slot = Slot(ApplianceSlotKey("charger"), False, 4.0, APPLIANCE_CYCLING)

    assert keys(build_slots(config, {}, (), APPLIANCE_CYCLING)) == ["a", "b"]
    slots = build_slots(config, {}, (), APPLIANCE_CYCLING, charger_slots=[charger_slot])
    assert keys(slots) == [
        "a",
        "charger",
        "b",
    ]


def charger(charger_id: str, min_a: int, max_a: int, reserve_w: int = 4000) -> Charger:
    return Charger(
        charger_id, min_current_a=min_a, max_current_a=max_a, power_reserve_w=reserve_w
    )


def test_fictive_appliances_are_interleaved_between_chargers() -> None:
    """One per ampere, first of each charger, then second."""
    chargers = [charger("a", 6, 8), charger("b", 10, 11), charger("c", 6, 6)]

    slots = fictive_slots(
        chargers,
        {},
        may_charge={"a", "b", "c"},
        on_trial=(),
        bypassed=(),
        cycling=FICTIVE_APPLIANCE_CYCLING,
    )

    assert [(slot.key.charger_id, slot.key.index) for slot in slots] == [
        ("a", 0),
        ("b", 0),
        ("c", 0),
        ("a", 1),
        ("b", 1),
        ("a", 2),
    ]


def test_only_the_first_fictive_appliance_has_the_power_reserve() -> None:
    """All of them get the cycling steps of the fictive appliances."""
    slots = fictive_slots(
        [charger("a", 6, 8, reserve_w=3500)],
        {"a": 2},
        {"a"},
        (),
        (),
        FICTIVE_APPLIANCE_CYCLING,
    )

    assert slots == [
        Slot(ChargerSlotKey("a", 0), True, 3500, FICTIVE_APPLIANCE_CYCLING),
        Slot(ChargerSlotKey("a", 1), True, None, FICTIVE_APPLIANCE_CYCLING),
        Slot(ChargerSlotKey("a", 2), False, None, FICTIVE_APPLIANCE_CYCLING),
    ]


def test_fictive_appliances_of_chargers_that_may_not_charge_or_are_bypassed() -> None:
    slots = fictive_slots(
        [charger("a", 6, 6), charger("b", 6, 6)],
        {"a": 1},
        may_charge={"b"},
        on_trial=(),
        bypassed={"a"},
        cycling=FICTIVE_APPLIANCE_CYCLING,
    )

    assert [(slot.can_turn_on, slot.can_turn_off) for slot in slots] == [
        (False, False),
        (True, True),
    ]


def test_charger_on_trial_can_only_get_its_first_fictive_appliance() -> None:
    slots = fictive_slots(
        [charger("a", 6, 8)],
        {"a": 1},
        may_charge={"a"},
        on_trial={"a"},
        bypassed=(),
        cycling=FICTIVE_APPLIANCE_CYCLING,
    )

    assert [slot.can_turn_on for slot in slots] == [True, False, False]
