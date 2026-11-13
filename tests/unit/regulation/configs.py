"""Compact configurations for the regulation tests.

Priority entries are written as ``"a"`` for appliance ``a`` itself and
``"a:morning"`` for its variant ``morning``. ``"@g"`` is the entry of the group of
chargers ``g``, and ``"ev"`` the entry of the group ``make_config`` makes.
Charging windows are written as ``"22:00-06:00"``.
"""

from datetime import time

from custom_components.kraftvakt.config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    Charger,
    ChargerGroup,
    ChargingWindow,
    Condition,
    ConditionType,
    GeneralConfig,
    KraftvaktConfig,
    OverrideEnd,
    PriorityEntry,
    Variant,
)

from .scenario import DECISION_INTERVAL

DEFAULT_ACTION = ActionConfig(ActionMode.DEFAULT)


def appliance(
    appliance_id: str,
    *,
    reserve_w: int | None = None,
    variants: tuple[str, ...] = (),
) -> Appliance:
    """Return an appliance whose variants have the given ids, in that order."""
    return Appliance(
        id=appliance_id,
        entity_id=f"switch.{appliance_id}",
        turn_on=DEFAULT_ACTION,
        turn_off=DEFAULT_ACTION,
        power_reserve_w=reserve_w,
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


def charger(
    charger_id: str,
    *,
    min_a: int = 6,
    max_a: int = 16,
    reserve_w: int = 4000,
    window: str | None = None,
    override_ends: OverrideEnd = OverrideEnd.MANUAL,
) -> Charger:
    """Return a charger with default actions and the given charging window."""
    charging_window = None
    if window is not None:
        start, end = (time.fromisoformat(text) for text in window.split("-"))
        charging_window = ChargingWindow(start, end)
    return Charger(
        id=charger_id,
        entity_id=f"switch.{charger_id}",
        activate=DEFAULT_ACTION,
        deactivate=DEFAULT_ACTION,
        set_current=DEFAULT_ACTION,
        min_current_a=min_a,
        max_current_a=max_a,
        power_reserve_w=reserve_w,
        actively_charging=Condition(
            ConditionType.POWER_SENSOR, f"sensor.{charger_id}_power"
        ),
        charging_window=charging_window,
        override_ends=override_ends,
    )


DEFAULT_GROUP = "ev"


def charger_group(
    group_id: str, *chargers: Charger, one_at_a_time: bool = True
) -> ChargerGroup:
    """Return a group of the chargers, named after its id."""
    return ChargerGroup(
        id=group_id, name=group_id, one_at_a_time=one_at_a_time, chargers=chargers
    )


def priority_entry(text: str) -> PriorityEntry:
    """Return the entry written as ``"a"``, ``"a:variant"``, ``"@g"`` or ``"ev"``."""
    if text == "ev":
        return PriorityEntry.for_charger_group(DEFAULT_GROUP)
    if text.startswith("@"):
        return PriorityEntry.for_charger_group(text[1:])
    appliance_id, _, variant_id = text.partition(":")
    return PriorityEntry.for_appliance(appliance_id, variant_id or None)


def make_config(
    *appliances: Appliance | str,
    priority: tuple[str, ...] | None = None,
    limit_w: int = 10_000,
    wait_at_limit_s: int = 300,
    threshold_w: int = 1000,
    appliance_repeat: tuple[float, int] = (0.5, 4),
    charger_repeat: tuple[float, int] = (1.0, 5),
    chargers: tuple[Charger, ...] = (),
    one_at_a_time: bool = True,
    groups: tuple[ChargerGroup, ...] = (),
) -> KraftvaktConfig:
    """Return a configuration with the appliances in the given priority order.

    An appliance given as a string has no reserve and no variants. The
    chargers are put in one group, ``"ev"``, before the `groups`. Without an
    explicit priority, the appliances come first in the given order, then the
    group ``"ev"`` when there are chargers, and the variants last.
    """
    built = tuple(
        appliance(item) if isinstance(item, str) else item for item in appliances
    )
    if priority is None:
        priority = (
            *(item.id for item in built),
            *(("ev",) if chargers else ()),
            *(f"{item.id}:{variant.id}" for item in built for variant in item.variants),
        )
    return KraftvaktConfig(
        general=GeneralConfig(
            power_sensor="sensor.power",
            power_limit_w=limit_w,
            regulation_window_s=int(DECISION_INTERVAL.total_seconds()),
            wait_at_limit_s=wait_at_limit_s,
            appliance_repeat_increment_factor=appliance_repeat[0],
            appliance_repeat_increments=appliance_repeat[1],
            charger_repeat_increment_factor=charger_repeat[0],
            charger_repeat_increments=charger_repeat[1],
            penalty_threshold_w=threshold_w,
        ),
        appliances=built,
        priority=tuple(priority_entry(text) for text in priority),
        charger_groups=(
            *(
                (charger_group(DEFAULT_GROUP, *chargers, one_at_a_time=one_at_a_time),)
                if chargers
                else ()
            ),
            *groups,
        ),
    )
