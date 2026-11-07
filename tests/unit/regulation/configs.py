"""Compact configurations for the regulation tests.

Priority entries are written as ``"a"`` for appliance ``a`` itself and
``"a:morning"`` for its variant ``morning``. ``"ev"`` is the EV charging entry.
"""

from custom_components.kraftvakt.config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    Condition,
    ConditionType,
    GeneralConfig,
    KraftvaktConfig,
    PriorityEntry,
    Variant,
)

DEFAULT_ACTION = ActionConfig(ActionMode.DEFAULT)


def appliance(
    appliance_id: str,
    *,
    reserve: float | None = None,
    variants: tuple[str, ...] = (),
) -> Appliance:
    """Return an appliance whose variants have the given ids, in that order."""
    return Appliance(
        id=appliance_id,
        entity_id=f"switch.{appliance_id}",
        turn_on=DEFAULT_ACTION,
        turn_off=DEFAULT_ACTION,
        power_reserve_kw=reserve,
        variants=tuple(
            Variant(
                id=variant_id,
                label=variant_id,
                condition=Condition(
                    ConditionType.ENTITY, f"binary_sensor.{variant_id}"
                ),
            )
            for variant_id in variants
        ),
    )


def priority_entry(text: str) -> PriorityEntry:
    """Return the priority entry written as ``"a"``, ``"a:variant"`` or ``"ev"``."""
    if text == "ev":
        return PriorityEntry.ev_charging()
    appliance_id, _, variant_id = text.partition(":")
    return PriorityEntry.for_appliance(appliance_id, variant_id or None)


def make_config(
    *appliances: Appliance | str,
    priority: tuple[str, ...] | None = None,
    limit_kw: float = 10.0,
    wait_at_limit_min: int = 5,
) -> KraftvaktConfig:
    """Return a configuration with the appliances in the given priority order.

    An appliance given as a string has no reserve and no variants. Without an
    explicit priority, the appliances come first in the given order and their
    variants last.
    """
    built = tuple(
        appliance(item) if isinstance(item, str) else item for item in appliances
    )
    if priority is None:
        priority = (
            *(item.id for item in built),
            *(f"{item.id}:{variant.id}" for item in built for variant in item.variants),
        )
    return KraftvaktConfig(
        general=GeneralConfig(
            power_sensor="sensor.power",
            power_limit_kw=limit_kw,
            wait_at_limit_min=wait_at_limit_min,
        ),
        appliances=built,
        priority=tuple(priority_entry(text) for text in priority),
    )
