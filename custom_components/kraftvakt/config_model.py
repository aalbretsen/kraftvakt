"""Configuration model for Kraftvakt.

The configuration is immutable: a change is made by building a new
configuration and saving it.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field, fields, replace
from datetime import time, timedelta
from enum import Enum, StrEnum
from typing import Any, Final


@dataclass(frozen=True, slots=True)
class Range:
    minimum: float
    maximum: float | None
    resolution: float

    def contains(self, value: float) -> bool:
        return value >= self.minimum and (self.maximum is None or value <= self.maximum)

    def matches_resolution(self, value: float) -> bool:
        multiple = value / self.resolution
        return abs(multiple - round(multiple)) < 1e-6

    def to_dict(self) -> dict[str, float | None]:
        return {"min": self.minimum, "max": self.maximum, "resolution": self.resolution}


POWER_LIMIT_MAX_W: Final = 50_000
POWER_LIMIT_W = Range(1000, POWER_LIMIT_MAX_W, 1)
REGULATION_WINDOW_S = Range(10, 120, 1)
REGULATION_WINDOW_CHOICES: Final = 12
CHARGING_CURRENT_A = Range(1, None, 1)

SETTING_RANGES: Final[Mapping[str, Mapping[str, Range]]] = {
    "general": {
        "power_limit_w": POWER_LIMIT_W,
        "turn_on_margin_w": Range(1, 1000, 1),
        "regulation_window_updates": Range(1, None, 1),
        "power_sensor_interval_s": Range(0.1, REGULATION_WINDOW_S.maximum, 0.1),
        "wait_at_limit_s": Range(0, 600, 1),
        "wait_curve_steepness": Range(1.5, 9, 0.5),
        "wait_curve_pivot": Range(50, 99, 1),
        "appliance_repeat_increment_factor": Range(0.25, 1, 0.25),
        "appliance_repeat_increments": Range(1, 9, 1),
        "ampere_damping_s": Range(60, 1800, 1),
        "charger_waiting_factor": Range(1, 5, 1),
        "penalty_threshold_w": Range(0, 10_000, 1),
        "command_repeat_interval_min": Range(10, 60, 1),
        "action_timeout_s": Range(10, 300, 1),
        "power_sensor_timeout_s": Range(10, 3600, 1),
    },
    "appliances": {"power_reserve_w": Range(0, None, 1)},
    "chargers": {
        "min_current_a": CHARGING_CURRENT_A,
        "max_current_a": CHARGING_CURRENT_A,
        "min_current_power_w": Range(1000, 5000, 1),
        "start_delay_s": Range(0, 900, 1),
    },
}


class ActionKind(StrEnum):
    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_CURRENT = "set_current"


class ActionMode(StrEnum):
    """How an action is given.

    `ENTITY` runs the default action of another entity, and is offered only for
    setting the charging current. `DOMAIN` runs an action that belongs to the
    domain of the entity, with values the user has chosen. A charger has no
    entity of its own, so its actions are only `ENTITY` and `CUSTOM`.
    """

    DEFAULT = "default"
    CUSTOM = "custom"
    ENTITY = "entity"
    DOMAIN = "domain"


class ConditionType(StrEnum):
    """How a true/false value, or a measured value, is given.

    `STATE` is the states of an entity, offered for the conditions of a
    charger. `POWER_SENSOR` gives a power. `TEMPERATURE_SENSOR` gives a temperature to
    show, and `CURRENT_TEMPERATURE` and `TARGET_TEMPERATURE` give the current
    and the set temperature of a thermostat. A template may give a power or a
    temperature instead.
    """

    ENTITY = "entity"
    STATE = "state"
    TEMPLATE = "template"
    POWER_SENSOR = "power_sensor"
    TEMPERATURE_SENSOR = "temperature_sensor"
    CURRENT_TEMPERATURE = "current_temperature"
    TARGET_TEMPERATURE = "target_temperature"


VARIANT_CONDITION_TYPES: Final = (ConditionType.ENTITY, ConditionType.TEMPLATE)
CHARGER_CONDITION_TYPES: Final = (ConditionType.ENTITY, ConditionType.STATE, ConditionType.TEMPLATE)
POWER_TYPES: Final = (ConditionType.POWER_SENSOR, ConditionType.TEMPLATE)
THERMOSTAT_TEMPERATURE_TYPES: Final = (ConditionType.CURRENT_TEMPERATURE, ConditionType.TARGET_TEMPERATURE)
TEMPERATURE_TYPES: Final = (ConditionType.TEMPERATURE_SENSOR, *THERMOSTAT_TEMPERATURE_TYPES, ConditionType.TEMPLATE)


class SwitchedBy(StrEnum):
    """How a charger turns charging on and off.

    `ON_OFF_ENTITY` runs the default actions of its on/off entity, `ACTIONS`
    its custom actions to activate and deactivate, and `CURRENT` sets the
    charging current, where 0 A stops it.
    """

    ON_OFF_ENTITY = "on_off_entity"
    ACTIONS = "actions"
    CURRENT = "current"


class OverrideEnd(StrEnum):
    """What ends the override of a charger's charging window, besides the user."""

    MANUAL = "manual"
    CHARGING_STOPPED = "charging_stopped"
    CAR_DISCONNECTED = "car_disconnected"


class PriorityEntryType(StrEnum):
    APPLIANCE = "appliance"
    CHARGER_GROUP = "charger_group"


@dataclass(frozen=True, slots=True)
class ActionConfig:
    """An action that turns something on or off or sets the charging current.

    A custom action keeps its steps exactly as the action editor produced them.
    A domain action has the key of the domain action and a value per
    parameter, `None` while the user has not chosen it.
    """

    mode: ActionMode
    steps: tuple[dict[str, Any], ...] = ()
    entity_id: str | None = None
    domain_action: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        match self.mode:
            case ActionMode.DEFAULT:
                return {"mode": self.mode.value}
            case ActionMode.ENTITY:
                return {"mode": self.mode.value, "entity_id": self.entity_id}
            case ActionMode.DOMAIN:
                return {
                    "mode": self.mode.value,
                    "domain_action": self.domain_action,
                    "data": dict(self.data),
                }
        return {"mode": self.mode.value, "action": list(self.steps)}

    @property
    def is_missing(self) -> bool:
        """Return whether the action has nothing to run yet."""
        match self.mode:
            case ActionMode.CUSTOM:
                return not self.steps
            case ActionMode.ENTITY:
                return self.entity_id is None
            case ActionMode.DOMAIN:
                return any(_is_unset(value) for value in self.data.values())
        return False


def _is_unset(value: Any) -> bool:
    """A value of a domain action is unset while it is not chosen, an empty template or a temperature source without an entity."""
    if isinstance(value, Mapping):
        return not value.get("value")
    return value is None or value == ""


@dataclass(frozen=True, slots=True)
class Condition:
    """A true/false value from a boolean entity, the states of an entity or a template, or a value from a sensor.

    `value` is the entity or the template. For a state, `states` are the
    chosen states, which count as true, or as false when `states_are_true`
    is not set, and every other state as the opposite.
    """

    type: ConditionType
    value: str
    states: tuple[str, ...] = ()
    states_are_true: bool = True

    def to_dict(self) -> dict[str, Any]:
        if self.type is ConditionType.STATE:
            return _fields_to_dict(self)
        return {"type": self.type.value, "value": self.value}


APPLIANCE_ACTION_KINDS: Final[Mapping[str, ActionKind]] = {
    "turn_on": ActionKind.TURN_ON,
    "turn_off": ActionKind.TURN_OFF,
}

APPLIANCE_ACTION_MODES: Final = (ActionMode.DEFAULT, ActionMode.DOMAIN, ActionMode.CUSTOM)

CHARGER_ACTION_MODES: Final[Mapping[str, tuple[ActionMode, ...]]] = {
    "activate": (ActionMode.CUSTOM,),
    "deactivate": (ActionMode.CUSTOM,),
    "set_current": (ActionMode.ENTITY, ActionMode.CUSTOM),
}

CHARGER_ACTION_KINDS: Final[Mapping[str, ActionKind]] = {
    "activate": ActionKind.TURN_ON,
    "deactivate": ActionKind.TURN_OFF,
    "set_current": ActionKind.SET_CURRENT,
}


@dataclass(frozen=True, slots=True)
class ActionField:
    """An action of an appliance or a charger, with the field issues address."""

    field: str
    kind: ActionKind
    action: ActionConfig | None


@dataclass(frozen=True, slots=True)
class Variant:
    """An extra entry of an appliance in the priority list.

    `actions` holds only the actions the variant overrides, `None` while an
    overridden action is not set.
    """

    id: str
    label: str
    condition: Condition
    actions: Mapping[str, ActionConfig | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class Appliance:
    """A device that Kraftvakt turns on and off.

    An essential appliance is kept on, and turned off only in a penalty.
    The display values are only shown on the status page.
    """

    id: str
    entity_id: str | None = None
    turn_on: ActionConfig | None = None
    turn_off: ActionConfig | None = None
    essential: bool = False
    power_reserve_w: int | None = None
    variants: tuple[Variant, ...] = ()
    display_power: Condition | None = None
    display_temperature: Condition | None = None

    @property
    def controlled_entity(self) -> str | None:
        """Return the entity Kraftvakt turns on and off."""
        return self.entity_id

    def overriding_variant(self, variant_id: str | None, name: str) -> Variant | None:
        """Return the variant if it overrides the action `name`."""
        return next(
            (variant for variant in self.variants if variant.id == variant_id and name in variant.actions),
            None,
        )

    def action(self, variant_id: str | None, name: str) -> ActionConfig | None:
        """Return the action `name` that the variant, or else the appliance, uses."""
        variant = self.overriding_variant(variant_id, name)
        return getattr(self, name) if variant is None else variant.actions[name]

    def action_fields(self) -> Iterator[ActionField]:
        """Return the actions of the appliance and those the variants override."""
        for name, kind in APPLIANCE_ACTION_KINDS.items():
            yield ActionField(name, kind, getattr(self, name))
        for variant in self.variants:
            for name, kind in APPLIANCE_ACTION_KINDS.items():
                if name in variant.actions:
                    yield ActionField(f"variants.{variant.id}.{name}", kind, variant.actions[name])

    def conditions(self) -> Iterator[tuple[str, Condition]]:
        """Return each condition and display value that is given, with the field issues address."""
        for variant in self.variants:
            yield f"variants.{variant.id}.condition", variant.condition
        for field_name in ("display_power", "display_temperature"):
            condition = getattr(self, field_name)
            if condition is not None:
                yield field_name, condition

    def display_sensors(self) -> Iterator[tuple[str, str]]:
        """Return each display value given as a sensor, with its field, which must belong to the device of the appliance's entity."""
        for field_name, condition in self.conditions():
            if field_name.startswith("display_") and condition.type is not ConditionType.TEMPLATE and condition.value:
                yield field_name, condition.value

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class PriorityEntry:
    type: PriorityEntryType
    appliance_id: str | None = None
    variant_id: str | None = None
    group_id: str | None = None

    @classmethod
    def for_appliance(cls, appliance_id: str, variant_id: str | None = None) -> PriorityEntry:
        return cls(PriorityEntryType.APPLIANCE, appliance_id, variant_id)

    @classmethod
    def for_charger_group(cls, group_id: str) -> PriorityEntry:
        return cls(PriorityEntryType.CHARGER_GROUP, group_id=group_id)

    def to_dict(self) -> dict[str, Any]:
        if self.type is PriorityEntryType.CHARGER_GROUP:
            return {"type": self.type.value, "group_id": self.group_id}
        return {
            "type": self.type.value,
            "appliance_id": self.appliance_id,
            "variant_id": self.variant_id,
        }


@dataclass(frozen=True, slots=True)
class ChargingWindow:
    """Time of day when a charger may charge, possibly across midnight."""

    start: time
    end: time

    def to_dict(self) -> dict[str, str]:
        """Return the window as JSON-friendly data with times as HH:MM."""
        return {"start": _format_time(self.start), "end": _format_time(self.end)}


@dataclass(frozen=True, slots=True)
class Charger:
    """An EV charger, which is a device in Home Assistant.

    The on/off entity, and the actions to activate and deactivate, are kept
    while the charger is switched another way, but not used.
    """

    id: str
    device_id: str | None = None
    switched_by: SwitchedBy = SwitchedBy.ON_OFF_ENTITY
    on_off_entity: str | None = None
    activate: ActionConfig | None = None
    deactivate: ActionConfig | None = None
    set_current: ActionConfig | None = None
    min_current_a: int = 6
    max_current_a: int = 16
    min_current_power_w: int = 4157
    car_connected: Condition | None = None
    actively_charging: Condition | None = None
    charging_power: Condition | None = None
    charging_window: ChargingWindow | None = None
    charge_until_disconnected: bool = False
    override_ends: OverrideEnd = OverrideEnd.MANUAL
    cloud_controlled: bool = False
    start_delay_s: int = 300
    deactivate_on_fault: bool = False
    fault_flag: Condition | None = None

    @property
    def switched_by_current(self) -> bool:
        return self.switched_by is SwitchedBy.CURRENT

    @property
    def controlled_entity(self) -> str | None:
        """Return the entity Kraftvakt turns on and off, if the charger is switched by one."""
        return self.on_off_entity if self.switched_by is SwitchedBy.ON_OFF_ENTITY else None

    def action(self, kind: ActionKind) -> ActionConfig | None:
        """Return the action that runs for the kind: to turn on or off with an on/off entity, its default action."""
        if kind is ActionKind.SET_CURRENT:
            return self.set_current
        if self.switched_by is SwitchedBy.ON_OFF_ENTITY:
            return None if self.on_off_entity is None else ActionConfig(ActionMode.ENTITY, entity_id=self.on_off_entity)
        return self.activate if kind is ActionKind.TURN_ON else self.deactivate

    def action_fields(self) -> Iterator[ActionField]:
        """Return the actions the user gives that the charger uses."""
        for name, kind in CHARGER_ACTION_KINDS.items():
            if kind is ActionKind.SET_CURRENT or self.switched_by is SwitchedBy.ACTIONS:
                yield ActionField(name, kind, getattr(self, name))

    def conditions(self) -> Iterator[tuple[str, Condition]]:
        """Return each condition that is given, with the field issues address."""
        for field_name in ("car_connected", "actively_charging", "charging_power", "fault_flag"):
            condition = getattr(self, field_name)
            if condition is not None:
                yield field_name, condition

    def device_entities(self) -> Iterator[tuple[str, str]]:
        """Return each field and entity that must belong to the device."""
        if self.controlled_entity is not None:
            yield "on_off_entity", self.controlled_entity
        if self.set_current is not None and self.set_current.entity_id is not None:
            yield "set_current", self.set_current.entity_id
        for field_name, condition in self.conditions():
            if condition.type is not ConditionType.TEMPLATE and condition.value:
                yield field_name, condition.value

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ChargerGroup:
    """A named group of chargers with its own place in the priority list.

    The chargers are in the configured charging priority.
    """

    id: str
    name: str = ""
    one_at_a_time: bool = True
    dynamic_order: bool = False
    chargers: tuple[Charger, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class GeneralConfig:
    power_sensor: str | None = None
    power_limit_w: int = 10_000
    turn_on_margin_w: int = 100
    regulation_window_updates: int | None = None
    power_sensor_interval_s: float | None = None
    wait_at_limit_s: int = 300
    wait_curve_steepness: float = 6.0
    wait_curve_pivot: int = 80
    appliance_repeat_increment_factor: float = 0.5
    appliance_repeat_increments: int = 4
    ampere_damping_s: int = 300
    charger_waiting_factor: int = 2
    penalty_threshold_w: int = 100
    command_repeat_interval_min: int = 30
    action_timeout_s: int = 60
    power_sensor_timeout_s: int = 300

    @property
    def regulation_window_length(self) -> timedelta | None:
        """Return how long a regulation window lasts when the power sensor reports at its interval, None while either is not set."""
        if self.regulation_window_updates is None or self.power_sensor_interval_s is None:
            return None
        return timedelta(seconds=self.regulation_window_updates * self.power_sensor_interval_s)

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


def regulation_window_options(power_sensor_interval_s: float) -> list[int]:
    """Return the numbers of updates a regulation window may have, for a power sensor that reports at the interval.

    They are multiples of the fewest updates that last the shortest window,
    as many as the choices allow within the longest window.
    """
    fewest = max(1, math.ceil(REGULATION_WINDOW_S.minimum / power_sensor_interval_s - 1e-9))
    longest = REGULATION_WINDOW_S.maximum or REGULATION_WINDOW_S.minimum
    return [fewest * multiple for multiple in range(1, REGULATION_WINDOW_CHOICES + 1) if fewest * multiple * power_sensor_interval_s <= longest + 1e-9]


@dataclass(frozen=True, slots=True)
class KraftvaktConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    appliances: tuple[Appliance, ...] = ()
    priority: tuple[PriorityEntry, ...] = ()
    charger_groups: tuple[ChargerGroup, ...] = ()

    @property
    def chargers(self) -> tuple[Charger, ...]:
        return tuple(charger for group in self.charger_groups for charger in group.chargers)

    def with_charger(self, charger: Charger) -> KraftvaktConfig:
        """Return the configuration with the charger of the same id replaced."""
        groups = tuple(
            replace(
                group,
                chargers=tuple(charger if existing.id == charger.id else existing for existing in group.chargers),
            )
            for group in self.charger_groups
        )
        return replace(self, charger_groups=groups)

    def items(self) -> Iterator[tuple[str, Appliance | Charger]]:
        """Return the appliances and the chargers with the section they are in."""
        for appliance in self.appliances:
            yield "appliances", appliance
        for charger in self.chargers:
            yield "chargers", charger

    def to_dict(self) -> dict[str, Any]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ApplianceSwitches:
    excluded: bool = False

    def to_dict(self) -> dict[str, bool]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ChargerSwitches:
    excluded: bool = False
    window_override: bool = False

    def to_dict(self) -> dict[str, bool]:
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class Issue:
    """A validation error or a missing setting."""

    code: str
    section: str
    target: str | None = None
    field: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Return the issue as a dict without empty keys."""
        result = {"code": self.code, "section": self.section}
        if self.target is not None:
            result["target"] = self.target
        if self.field is not None:
            result["field"] = self.field
        return result


class ConfigValidationError(ValueError):
    """Raised when a configuration is invalid. Holds every issue found."""

    def __init__(self, issues: list[Issue]) -> None:
        super().__init__(", ".join(issue.code for issue in issues))
        self.issues = issues


def new_id() -> str:
    """Return a short unique id for an appliance, variant, charger or group."""
    return uuid.uuid4().hex[:12]


type ItemSwitches = ApplianceSwitches | ChargerSwitches


def appliance_switches_for(config: KraftvaktConfig, switches: Mapping[str, ApplianceSwitches]) -> dict[str, ApplianceSwitches]:
    """Return the switches for exactly the appliances in the configuration."""
    return _switches_for(config.appliances, switches, ApplianceSwitches())


def charger_switches_for(config: KraftvaktConfig, switches: Mapping[str, ChargerSwitches]) -> dict[str, ChargerSwitches]:
    """Return the switches for exactly the chargers in the configuration."""
    return _switches_for(config.chargers, switches, ChargerSwitches())


def switches_to_dict(
    switches: Mapping[str, ItemSwitches],
) -> dict[str, dict[str, bool]]:
    """Return the switches of appliances or chargers as JSON-friendly data."""
    return {item_id: state.to_dict() for item_id, state in switches.items()}


def _switches_for[T: ItemSwitches](items: Iterable[Appliance | Charger], switches: Mapping[str, T], default: T) -> dict[str, T]:
    return {item.id: switches.get(item.id, default) for item in items}


def _fields_to_dict(item: Any) -> dict[str, Any]:
    return {attribute.name: _to_json(getattr(item, attribute.name)) for attribute in fields(item)}


def _to_json(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_to_json(item) for item in value]
    if isinstance(value, Mapping):
        return {key: _to_json(item) for key, item in value.items()}
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _format_time(value: time) -> str:
    if value.second:
        return value.strftime("%H:%M:%S")
    return value.strftime("%H:%M")


@dataclass(frozen=True, slots=True)
class IssueLocation:
    """Where in the configuration an issue is: section, item and field prefix."""

    section: str
    target: str | None = None
    prefix: str = ""

    def issue(self, code: str, field_name: str | None = None) -> Issue:
        name = None if field_name is None else f"{self.prefix}{field_name}"
        return Issue(code, self.section, self.target, name)
