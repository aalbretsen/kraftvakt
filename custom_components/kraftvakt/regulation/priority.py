"""The order of steps built from the priority list."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence

from ..config_model import Appliance, Charger, KraftvaktConfig, PriorityEntryType
from .charging import ChargingState, ampere_step_count
from .model import AmpereStepKey, ApplianceStepKey, Step, StepKey


def current_variant(appliance: Appliance, variant_conditions: Mapping[str, bool]) -> str | None:
    """Return the variant with the topmost true condition, or None for the appliance."""
    return next(
        (variant.id for variant in appliance.variants if variant_conditions.get(variant.id, False)),
        None,
    )


def build_steps(
    config: KraftvaktConfig,
    current_variants: Mapping[str, str | None],
    appliances_on: Collection[str],
    ampere_steps_by_group: Mapping[str, Sequence[Step]] | None = None,
    excluded_appliances: Collection[str] = (),
    settling: Collection[StepKey] = (),
) -> list[Step]:
    """Return the steps in priority order, highest priority first.

    `ampere_steps_by_group` has the ampere steps of each group of chargers, by
    the id of the group, to put at the entry of the group. An essential
    appliance is no step, since only a penalty turns it off.
    """
    ampere_steps_by_group = ampere_steps_by_group or {}
    appliances = {appliance.id: appliance for appliance in config.appliances}
    steps: list[Step] = []
    for entry in config.priority:
        if entry.type is PriorityEntryType.CHARGER_GROUP:
            steps.extend(ampere_steps_by_group.get(entry.group_id or "", ()))
            continue
        appliance_id = entry.appliance_id
        if appliance_id is None or appliances[appliance_id].essential or current_variants.get(appliance_id) != entry.variant_id:
            continue
        key = ApplianceStepKey(appliance_id)
        is_on = appliance_id in appliances_on
        steps.append(
            Step(
                key=key,
                is_on=is_on,
                power_reserve_w=appliances[appliance_id].power_reserve_w,
                can_turn_on=appliance_id not in excluded_appliances,
                holds_reserve=is_on and key in settling,
            )
        )
    return steps


def ampere_steps(group_id: str, blocks: Sequence[Sequence[Charger]], charging: ChargingState, settling: Collection[StepKey] = ()) -> list[Step]:
    """Return the ampere steps of the group: those of each block interleaved, the first of each charger, then the second, one block after the other.

    The first ampere step of a charger needs its power at minimum current, and
    the others its power per ampere. A charger held at minimum may only have its
    first ampere step turned on, and only the ampere steps of a charger that may
    be switched off for room are. A step that is settling, and the first of a
    starting charger, hold their power reserve.
    """
    return [step for chargers in blocks for step in _interleaved(group_id, chargers, charging, settling)]


def _interleaved(group_id: str, chargers: Sequence[Charger], charging: ChargingState, settling: Collection[StepKey]) -> list[Step]:
    rounds = max(map(ampere_step_count, chargers), default=0)
    steps: list[Step] = []
    for index in range(rounds):
        for charger in chargers:
            if index >= ampere_step_count(charger):
                continue
            key = AmpereStepKey(charger.id, index)
            is_on = index < charging.ampere_steps_on.get(charger.id, 0)
            starting = index == 0 and charger.id in charging.starting
            steps.append(
                Step(
                    key=key,
                    is_on=is_on,
                    power_reserve_w=charger.min_current_power_w if index == 0 else charging.power_per_ampere_w(charger),
                    can_turn_on=charger.id in charging.may_charge and (index == 0 or charger.id not in charging.held_at_min),
                    can_turn_off=charging.may_switch_off(charger.id),
                    holds_reserve=is_on and (starting or key in settling),
                    group_id=group_id,
                )
            )
    return steps
