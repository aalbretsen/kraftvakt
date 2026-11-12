"""Configuration model for Kraftvakt.

The configuration is immutable: a change is made by building a new
configuration and saving it.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field, fields, replace
from datetime import time
from enum import Enum, StrEnum
from typing import Any, Final


@dataclass(frozen=True, slots=True)
class Range:
    """Valid range and resolution of a numeric setting."""

    minimum: float
    maximum: float | None
    resolution: float

    def contains(self, value: float) -> bool:
        """Return whether the value lies within the range."""
        return value >= self.minimum and (self.maximum is None or value <= self.maximum)

    def matches_resolution(self, value: float) -> bool:
        """Return whether the value is a whole multiple of the resolution."""
        multiple = value / self.resolution
        return abs(multiple - round(multiple)) < 1e-6

    def to_dict(self) -> dict[str, float | None]:
        """Return the range as JSON-friendly data for the panel."""
        return {"min": self.minimum, "max": self.maximum, "resolution": self.resolution}


POWER_LIMIT_W = Range(1000, 50_000, 1)
TURN_ON_MARGIN_W = Range(1, 1000, 1)
REGULATION_WINDOW_S = Range(10, 600, 1)
REGULATION_INTERVAL = Range(1, 4, 1)
WAIT_AT_LIMIT_S = Range(0, 600, 1)
WAIT_CURVE_STEEPNESS = Range(1.5, 9, 0.5)
WAIT_CURVE_PIVOT = Range(50, 99, 1)
REPEAT_INCREMENT_FACTOR = Range(0.25, 1, 0.25)
REPEAT_INCREMENTS = Range(1, 9, 1)
PENALTY_THRESHOLD_W = Range(0, 10_000, 1)
COMMAND_REPEAT_INTERVAL_MIN = Range(10, 60, 1)
APPLIANCE_POWER_RESERVE_W = Range(0, None, 1)
CHARGER_POWER_RESERVE_W = Range(0, 5000, 1)
CHARGING_CURRENT_A = Range(1, None, 1)

SETTING_RANGES: Final[Mapping[str, Mapping[str, Range]]] = {
    "general": {
        "power_limit_w": POWER_LIMIT_W,
        "turn_on_margin_w": TURN_ON_MARGIN_W,
        "regulation_window_s": REGULATION_WINDOW_S,
        "regulation_interval": REGULATION_INTERVAL,
        "wait_at_limit_s": WAIT_AT_LIMIT_S,
        "wait_curve_steepness": WAIT_CURVE_STEEPNESS,
        "wait_curve_pivot": WAIT_CURVE_PIVOT,
        "appliance_repeat_increment_factor": REPEAT_INCREMENT_FACTOR,
        "appliance_repeat_increments": REPEAT_INCREMENTS,
        "charger_repeat_increment_factor": REPEAT_INCREMENT_FACTOR,
        "charger_repeat_increments": REPEAT_INCREMENTS,
        "penalty_threshold_w": PENALTY_THRESHOLD_W,
        "command_repeat_interval_min": COMMAND_REPEAT_INTERVAL_MIN,
    },
    "appliances": {"power_reserve_w": APPLIANCE_POWER_RESERVE_W},
    "chargers": {
        "min_current_a": CHARGING_CURRENT_A,
        "max_current_a": CHARGING_CURRENT_A,
        "power_reserve_w": CHARGER_POWER_RESERVE_W,
    },
}


class ActionKind(StrEnum):
    """What an action does."""

    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_CURRENT = "set_current"


class ActionMode(StrEnum):
    """How an action is given.

    `ENTITY` runs the default action of another entity, and is offered only for
    setting the charging current. `DOMAIN` runs an action that belongs to the
    domain of the entity, with values the user has chosen.
    """

    DEFAULT = "default"
    CUSTOM = "custom"
    ENTITY = "entity"
    DOMAIN = "domain"


class ConditionType(StrEnum):
    """How a true/false value is given.

    `POWER_SENSOR` is true above a fixed power, and is offered only for
    whether a charger is actively charging.
    """

    ENTITY = "entity"
    TEMPLATE = "template"
    POWER_SENSOR = "power_sensor"


class PriorityEntryType(StrEnum):
    """Kind of entry in the priority list."""

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
        """Return the action as JSON-friendly data."""
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
                return any(value is None for value in self.data.values())
        return False


@dataclass(frozen=True, slots=True)
class Condition:
    """A true/false value from a boolean entity, a template or a power sensor."""

    type: ConditionType
    value: str

    def to_dict(self) -> dict[str, Any]:
        """Return the condition as JSON-friendly data."""
        return _fields_to_dict(self)


APPLIANCE_ACTION_KINDS: Final[Mapping[str, ActionKind]] = {
    "turn_on": ActionKind.TURN_ON,
    "turn_off": ActionKind.TURN_OFF,
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
        """Return the variant as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class Appliance:
    """A device that Kraftvakt turns on and off."""

    id: str
    entity_id: str | None = None
    turn_on: ActionConfig | None = None
    turn_off: ActionConfig | None = None
    power_reserve_w: int | None = None
    variants: tuple[Variant, ...] = ()

    def overriding_variant(self, variant_id: str | None, name: str) -> Variant | None:
        """Return the variant if it overrides the action `name`."""
        return next(
            (
                variant
                for variant in self.variants
                if variant.id == variant_id and name in variant.actions
            ),
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
                    yield ActionField(
                        f"variants.{variant.id}.{name}", kind, variant.actions[name]
                    )

    def to_dict(self) -> dict[str, Any]:
        """Return the appliance as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class PriorityEntry:
    """An entry in the priority list."""

    type: PriorityEntryType
    appliance_id: str | None = None
    variant_id: str | None = None
    group_id: str | None = None

    @classmethod
    def for_appliance(
        cls, appliance_id: str, variant_id: str | None = None
    ) -> PriorityEntry:
        """Return the entry for an appliance or one of its variants."""
        return cls(PriorityEntryType.APPLIANCE, appliance_id, variant_id)

    @classmethod
    def for_charger_group(cls, group_id: str) -> PriorityEntry:
        """Return the entry for a group of chargers."""
        return cls(PriorityEntryType.CHARGER_GROUP, group_id=group_id)

    def to_dict(self) -> dict[str, Any]:
        """Return the entry as JSON-friendly data."""
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
    """An EV charger."""

    id: str
    device_id: str | None = None
    entity_id: str | None = None
    activate: ActionConfig | None = None
    deactivate: ActionConfig | None = None
    set_current: ActionConfig | None = None
    min_current_a: int = 6
    max_current_a: int = 16
    power_reserve_w: int = 4000
    car_connected: Condition | None = None
    actively_charging: Condition | None = None
    charging_window: ChargingWindow | None = None
    finish_after_window: bool = False

    def action_fields(self) -> Iterator[ActionField]:
        """Return the actions of the charger."""
        for name, kind in CHARGER_ACTION_KINDS.items():
            yield ActionField(name, kind, getattr(self, name))

    def device_entities(self) -> Iterator[tuple[str, str]]:
        """Return each field and entity that must belong to the device."""
        if self.entity_id is not None:
            yield "entity_id", self.entity_id
        if self.set_current is not None and self.set_current.entity_id is not None:
            yield "set_current", self.set_current.entity_id
        for field_name in ("car_connected", "actively_charging"):
            condition = getattr(self, field_name)
            if (
                condition is not None
                and condition.type is not ConditionType.TEMPLATE
                and condition.value
            ):
                yield field_name, condition.value

    def to_dict(self) -> dict[str, Any]:
        """Return the charger as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ChargerGroup:
    """A named group of chargers with its own place in the priority list.

    The chargers are in the configured charging priority.
    """

    id: str
    name: str = ""
    one_at_a_time: bool = True
    chargers: tuple[Charger, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the group as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class GeneralConfig:
    """General parameters."""

    power_sensor: str | None = None
    power_limit_w: int = 10_000
    turn_on_margin_w: int = 100
    regulation_window_s: int = 10
    regulation_interval: int = 1
    wait_at_limit_s: int = 300
    wait_curve_steepness: float = 6.0
    wait_curve_pivot: int = 80
    appliance_repeat_increment_factor: float = 0.5
    appliance_repeat_increments: int = 4
    charger_repeat_increment_factor: float = 1.0
    charger_repeat_increments: int = 5
    penalty_threshold_w: int = 100
    command_repeat_interval_min: int = 30

    def to_dict(self) -> dict[str, Any]:
        """Return the general parameters as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class KraftvaktConfig:
    """The whole configuration."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    appliances: tuple[Appliance, ...] = ()
    priority: tuple[PriorityEntry, ...] = ()
    charger_groups: tuple[ChargerGroup, ...] = ()

    @property
    def chargers(self) -> tuple[Charger, ...]:
        """Return the chargers of every group."""
        return tuple(
            charger for group in self.charger_groups for charger in group.chargers
        )

    def with_charger(self, charger: Charger) -> KraftvaktConfig:
        """Return the configuration with the charger of the same id replaced."""
        groups = tuple(
            replace(
                group,
                chargers=tuple(
                    charger if existing.id == charger.id else existing
                    for existing in group.chargers
                ),
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
        """Return the configuration as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ApplianceSwitches:
    """The user's switches for an appliance."""

    excluded: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Return the switches as JSON-friendly data."""
        return _fields_to_dict(self)


@dataclass(frozen=True, slots=True)
class ChargerSwitches:
    """The user's switches for a charger."""

    excluded: bool = False
    window_override: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Return the switches as JSON-friendly data."""
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
        """Create the error from the issues found."""
        super().__init__(", ".join(issue.code for issue in issues))
        self.issues = issues


def new_id() -> str:
    """Return a short unique id for an appliance, variant, charger or group."""
    return uuid.uuid4().hex[:12]


type ItemSwitches = ApplianceSwitches | ChargerSwitches


def appliance_switches_for(
    config: KraftvaktConfig, switches: Mapping[str, ApplianceSwitches]
) -> dict[str, ApplianceSwitches]:
    """Return the switches for exactly the appliances in the configuration."""
    return _switches_for(config.appliances, switches, ApplianceSwitches())


def charger_switches_for(
    config: KraftvaktConfig, switches: Mapping[str, ChargerSwitches]
) -> dict[str, ChargerSwitches]:
    """Return the switches for exactly the chargers in the configuration."""
    return _switches_for(config.chargers, switches, ChargerSwitches())


def switches_to_dict(
    switches: Mapping[str, ItemSwitches],
) -> dict[str, dict[str, bool]]:
    """Return the switches of appliances or chargers as JSON-friendly data."""
    return {item_id: state.to_dict() for item_id, state in switches.items()}


def _switches_for[T: ItemSwitches](
    items: Iterable[Appliance | Charger], switches: Mapping[str, T], default: T
) -> dict[str, T]:
    return {item.id: switches.get(item.id, default) for item in items}


def _fields_to_dict(item: Any) -> dict[str, Any]:
    """Return the fields of a dataclass as JSON-friendly data."""
    return {
        attribute.name: _to_json(getattr(item, attribute.name))
        for attribute in fields(item)
    }


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
        """Return the issue for a field at this location."""
        name = None if field_name is None else f"{self.prefix}{field_name}"
        return Issue(code, self.section, self.target, name)
