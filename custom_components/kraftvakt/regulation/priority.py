"""The order of slots built from the priority list."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ..config_model import Appliance, Charger, KraftvaktConfig, PriorityEntryType
from .charging import fictive_appliance_count
from .model import ApplianceSlotKey, ChargerSlotKey, Slot
from .waiting import APPLIANCE_CYCLING, FICTIVE_APPLIANCE_CYCLING


def current_variant(
    appliance: Appliance, variant_conditions: Mapping[str, bool]
) -> str | None:
    """Return the id of the current variant, or None for the appliance itself.

    The current variant is the one with the topmost true condition.
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

    Only the entry of the current variant of each appliance gets a slot. The EV charging
    entry is replaced by `charger_slots`.
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


def fictive_slots(
    chargers: Sequence[Charger],
    fictive_on: Mapping[str, int],
    may_charge: Collection[str],
    bypassed: Collection[str],
) -> list[Slot]:
    """Return the fictive appliances of the chargers, interleaved.

    `chargers` are in the current charging priority. Each charger gets its
    first fictive appliance in that order, then its second, and so on. Only the
    first one has the power reserve of the charger. Only chargers in
    `may_charge` can get more turned on, and the fictive appliances of bypassed
    chargers are not switched off above the limit.
    """
    rounds = max(map(fictive_appliance_count, chargers), default=0)
    return [
        Slot(
            key=ChargerSlotKey(charger.id, index),
            is_on=index < fictive_on.get(charger.id, 0),
            power_reserve_kw=charger.power_reserve_kw if index == 0 else None,
            cycling=FICTIVE_APPLIANCE_CYCLING,
            can_turn_on=charger.id in may_charge,
            can_turn_off=charger.id not in bypassed,
        )
        for index in range(rounds)
        for charger in chargers
        if index < fictive_appliance_count(charger)
    ]
