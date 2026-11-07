"""Unit tests for the slots built from the priority list (4.1, APP-007)."""

from custom_components.kraftvakt.regulation.model import ApplianceSlotKey, Slot
from custom_components.kraftvakt.regulation.priority import (
    build_slots,
    current_variant,
)
from custom_components.kraftvakt.regulation.waiting import APPLIANCE_CYCLING

from .configs import appliance, make_config


def keys(slots: list[Slot]) -> list[str]:
    return [slot.key.appliance_id for slot in slots]


def test_appliance_without_true_condition_is_its_own_current_variant() -> None:
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {}) is None
    assert current_variant(heater, {"morning": False, "evening": False}) is None


def test_topmost_true_condition_gives_current_variant() -> None:
    """APP-007: the variant of the topmost true expression applies."""
    heater = appliance("heater", variants=("morning", "evening"))

    assert current_variant(heater, {"evening": True}) == "evening"
    assert current_variant(heater, {"morning": True, "evening": True}) == "morning"


def test_slots_follow_the_priority_list() -> None:
    config = make_config(appliance("a", reserve=2.5), "b", "c")

    slots = build_slots(config, current_variants={}, appliances_on={"b"})

    assert slots == [
        Slot(ApplianceSlotKey("a"), False, 2.5, APPLIANCE_CYCLING),
        Slot(ApplianceSlotKey("b"), True, None, APPLIANCE_CYCLING),
        Slot(ApplianceSlotKey("c"), False, None, APPLIANCE_CYCLING),
    ]


def test_only_the_current_variant_gets_a_slot() -> None:
    """APP-007: the other entries of the appliance are skipped."""
    config = make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
    )

    assert keys(build_slots(config, {}, ())) == ["b", "heater"]
    assert keys(build_slots(config, {"heater": "morning"}, ())) == ["heater", "b"]


def test_ev_charging_entry_is_replaced_by_charger_slots() -> None:
    config = make_config("a", "b", priority=("a", "ev", "b"))
    charger_slot = Slot(ApplianceSlotKey("charger"), False, 4.0, APPLIANCE_CYCLING)

    assert keys(build_slots(config, {}, ())) == ["a", "b"]
    assert keys(build_slots(config, {}, (), charger_slots=[charger_slot])) == [
        "a",
        "charger",
        "b",
    ]
