"""The order of slots built from the priority list (4.1, APP-007)."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ..config_model import Appliance, KraftvaktConfig, PriorityEntryType
from .model import APPLIANCE_CYCLING, ApplianceSlotKey, Slot


def current_variant(
    appliance: Appliance, variant_conditions: Mapping[str, bool]
) -> str | None:
    """Return the id of the current variant, or None for the appliance itself.

    The current variant is the one with the topmost true condition (APP-007).
    """
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
    charger_slots: Sequence[Slot] = (),
) -> list[Slot]:
    """Return the slots in priority order, highest priority first.

    Only the entry of the current variant of each appliance gets a slot
    (APP-007). The EV charging entry is replaced by `charger_slots` (APP-005).
    """
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
                power_reserve_kw=appliances[appliance_id].power_reserve_kw,
                cycling=APPLIANCE_CYCLING,
            )
        )
    return slots
