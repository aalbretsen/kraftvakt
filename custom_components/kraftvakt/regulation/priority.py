"""The order of steps built from the priority list."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ..config_model import Appliance, Charger, KraftvaktConfig, PriorityEntryType
from .charging import ampere_step_count
from .model import AmpereStepKey, ApplianceStepKey, Step
from .waiting import RepeatedTurnOnGrowth


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


def build_steps(
    config: KraftvaktConfig,
    current_variants: Mapping[str, str | None],
    appliances_on: Collection[str],
    growth: RepeatedTurnOnGrowth,
    ampere_steps_by_group: Mapping[str, Sequence[Step]] | None = None,
    excluded_appliances: Collection[str] = (),
) -> list[Step]:
    """Return the steps in priority order, highest priority first.

    `ampere_steps_by_group` has the ampere steps of each group of chargers, by
    the id of the group, to put at the entry of the group.
    """
    ampere_steps_by_group = ampere_steps_by_group or {}
    appliances = {appliance.id: appliance for appliance in config.appliances}
    steps: list[Step] = []
    for entry in config.priority:
        if entry.type is PriorityEntryType.CHARGER_GROUP:
            steps.extend(ampere_steps_by_group.get(entry.group_id or "", ()))
            continue
        appliance_id = entry.appliance_id
        if (
            appliance_id is None
            or current_variants.get(appliance_id) != entry.variant_id
        ):
            continue
        steps.append(
            Step(
                key=ApplianceStepKey(appliance_id),
                is_on=appliance_id in appliances_on,
                power_reserve_w=appliances[appliance_id].power_reserve_w,
                growth=growth,
                can_turn_on=appliance_id not in excluded_appliances,
            )
        )
    return steps


def ampere_steps(
    chargers: Sequence[Charger],
    ampere_steps_on: Mapping[str, int],
    may_charge: Collection[str],
    on_trial: Collection[str],
    bypassed: Collection[str],
    growth: RepeatedTurnOnGrowth,
) -> list[Step]:
    rounds = max(map(ampere_step_count, chargers), default=0)
    return [
        Step(
            key=AmpereStepKey(charger.id, index),
            is_on=index < ampere_steps_on.get(charger.id, 0),
            power_reserve_w=charger.power_reserve_w if index == 0 else None,
            growth=growth,
            can_turn_on=charger.id in may_charge
            and (index == 0 or charger.id not in on_trial),
            can_turn_off=charger.id not in bypassed,
        )
        for index in range(rounds)
        for charger in chargers
        if index < ampere_step_count(charger)
    ]
