"""The order of slots built from the priority list."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ..config_model import Appliance, Charger, KraftvaktConfig, PriorityEntryType
from .charging import fictive_appliance_count
from .model import ApplianceSlotKey, ChargerSlotKey, Slot
from .waiting import CyclingSteps


def current_variant(
    appliance: Appliance, variant_conditions: Mapping[str, bool]
) -> str | None:
    """Return the variant with the topmost true condition, or None for the appliance."""
    return next(
        (
            variant.id
            for variant in appliance.variants
            if variant_conditions.get(variant.id, False)
        ),
        None,
    )


def build_slots(
    config: KraftvaktConfig,
    current_variants: Mapping[str, str | None],
    appliances_on: Collection[str],
    cycling: CyclingSteps,
    charger_slots: Sequence[Slot] = (),
) -> list[Slot]:
    """Return the slots in priority order, highest priority first."""
    appliances = {appliance.id: appliance for appliance in config.appliances}
    slots: list[Slot] = []
    for entry in config.priority:
        if entry.type is PriorityEntryType.EV_CHARGING:
            slots.extend(charger_slots)
            continue
        appliance_id = entry.appliance_id
        if (
            appliance_id is None
            or current_variants.get(appliance_id) != entry.variant_id
        ):
            continue
        slots.append(
            Slot(
                key=ApplianceSlotKey(appliance_id),
                is_on=appliance_id in appliances_on,
                power_reserve_w=appliances[appliance_id].power_reserve_w,
                cycling=cycling,
            )
        )
    return slots


def fictive_slots(
    chargers: Sequence[Charger],
    fictive_on: Mapping[str, int],
    may_charge: Collection[str],
    on_trial: Collection[str],
    bypassed: Collection[str],
    cycling: CyclingSteps,
) -> list[Slot]:
    """Return the fictive appliances of the chargers, interleaved."""
    rounds = max(map(fictive_appliance_count, chargers), default=0)
    return [
        Slot(
            key=ChargerSlotKey(charger.id, index),
            is_on=index < fictive_on.get(charger.id, 0),
            power_reserve_w=charger.power_reserve_w if index == 0 else None,
            cycling=cycling,
            can_turn_on=charger.id in may_charge
            and (index == 0 or charger.id not in on_trial),
            can_turn_off=charger.id not in bypassed,
        )
        for index in range(rounds)
        for charger in chargers
        if index < fictive_appliance_count(charger)
    ]
