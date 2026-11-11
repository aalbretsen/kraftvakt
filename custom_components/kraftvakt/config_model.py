"""Configuration model for Kraftvakt.

The configuration is immutable: a change is made by building a new
configuration and saving it.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import time
from enum import StrEnum
from typing import Any, Final


@dataclass(frozen=True, slots=True)
class Range:
    """Valid range and resolution of a numeric setting."""

    minimum: float
    maximum: float | None
    step: float

    def contains(self, value: float) -> bool:
        """Return whether the value lies within the range."""
        return value >= self.minimum and (self.maximum is None or value <= self.maximum)

    def matches_step(self, value: float) -> bool:
        """Return whether the value is a whole multiple of the step."""
        steps = value / self.step
        return abs(steps - round(steps)) < 1e-6

    def to_dict(self) -> dict[str, float | None]:
        """Return the range as JSON-friendly data for the panel."""
        return {"min": self.minimum, "max": self.maximum, "step": self.step}


POWER_LIMIT_W = Range(1000, 50_000, 1)
TURN_ON_MARGIN_W = Range(1, 1000, 1)
REGULATION_WINDOW_S = Range(10, 600, 1)
REGULATION_INTERVAL = Range(1, 4, 1)
WAIT_AT_LIMIT_S = Range(0, 600, 1)
WAIT_CURVE_STEEPNESS = Range(1.5, 9, 0.5)
WAIT_CURVE_PIVOT = Range(50, 99, 1)
CYCLING_STEP_FACTOR = Range(0.25, 1, 0.25)
CYCLING_STEPS = Range(1, 9, 1)
PENALTY_THRESHOLD_W = Range(0, 10_000, 1)
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
        "appliance_cycling_step_factor": CYCLING_STEP_FACTOR,
        "appliance_cycling_steps": CYCLING_STEPS,
        "charger_cycling_step_factor": CYCLING_STEP_FACTOR,
        "charger_cycling_steps": CYCLING_STEPS,
        "penalty_threshold_w": PENALTY_THRESHOLD_W,
    },
    "appliances": {"power_reserve_w": APPLIANCE_POWER_RESERVE_W},
    "chargers": {
        "min_current_a": CHARGING_CURRENT_A,
        "max_current_a": CHARGING_CURRENT_A,
        "power_reserve_w": CHARGER_POWER_RESERVE_W,
    },
}


class ActionMode(StrEnum):
    """How an action is given.

    `ENTITY` runs the default action of another entity, and is offered only for
    setting the charging current.
    """

    DEFAULT = "default"
    CUSTOM = "custom"
    ENTITY = "entity"


class ConditionType(StrEnum):
    """How a true/false value is given."""

    ENTITY = "entity"
    TEMPLATE = "template"


class PriorityEntryType(StrEnum):
    """Kind of entry in the priority list."""

    APPLIANCE = "appliance"
    EV_CHARGING = "ev_charging"


@dataclass(frozen=True, slots=True)
class ActionConfig:
    """An action that turns something on or off or sets the charging current.

    A custom action keeps its steps exactly as the action editor produced them.
    """

    mode: ActionMode
    steps: tuple[dict[str, Any], ...] = ()
    entity_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the action as JSON-friendly data."""
        if self.mode is ActionMode.DEFAULT:
            return {"mode": self.mode.value}
        if self.mode is ActionMode.ENTITY:
            return {"mode": self.mode.value, "entity_id": self.entity_id}
        return {"mode": self.mode.value, "action": list(self.steps)}

    @property
    def is_missing(self) -> bool:
        """Return whether the action has nothing to run yet."""
        if self.mode is ActionMode.CUSTOM:
            return not self.steps
        return self.mode is ActionMode.ENTITY and self.entity_id is None


@dataclass(frozen=True, slots=True)
class Condition:
    """A true/false value from a boolean entity or a template."""

    type: ConditionType
    value: str

    def to_dict(self) -> dict[str, Any]:
        """Return the condition as JSON-friendly data."""
        return {"type": self.type.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class Variant:
    """An extra entry of an appliance in the priority list."""

    id: str
    label: str
    condition: Condition

    def to_dict(self) -> dict[str, Any]:
        """Return the variant as JSON-friendly data."""
        return {
            "id": self.id,
            "label": self.label,
            "condition": self.condition.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class Appliance:
    """A device that Kraftvakt turns on and off."""

    id: str
    entity_id: str | None = None
    turn_on: ActionConfig | None = None
    turn_off: ActionConfig | None = None
    power_reserve_w: int | None = None
    variants: tuple[Variant, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the appliance as JSON-friendly data."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "turn_on": _optional_dict(self.turn_on),
            "turn_off": _optional_dict(self.turn_off),
            "power_reserve_w": self.power_reserve_w,
            "variants": [variant.to_dict() for variant in self.variants],
        }


@dataclass(frozen=True, slots=True)
class PriorityEntry:
    """An entry in the priority list."""

    type: PriorityEntryType
    appliance_id: str | None = None
    variant_id: str | None = None

    @classmethod
    def for_appliance(
        cls, appliance_id: str, variant_id: str | None = None
    ) -> PriorityEntry:
        """Return the entry for an appliance or one of its variants."""
        return cls(PriorityEntryType.APPLIANCE, appliance_id, variant_id)

    @classmethod
    def ev_charging(cls) -> PriorityEntry:
        """Return the entry for EV charging."""
        return cls(PriorityEntryType.EV_CHARGING)

    def to_dict(self) -> dict[str, Any]:
        """Return the entry as JSON-friendly data."""
        if self.type is PriorityEntryType.EV_CHARGING:
            return {"type": self.type.value}
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
    entity_id: str | None = None
    activate: ActionConfig | None = None
    deactivate: ActionConfig | None = None
    set_current: ActionConfig | None = None
    min_current_a: int = 6
    max_current_a: int = 16
    charge_power_sensor: str | None = None
    power_reserve_w: int = 4000
    car_connected: Condition | None = None
    charging_window: ChargingWindow | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the charger as JSON-friendly data."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "activate": _optional_dict(self.activate),
            "deactivate": _optional_dict(self.deactivate),
            "set_current": _optional_dict(self.set_current),
            "min_current_a": self.min_current_a,
            "max_current_a": self.max_current_a,
            "charge_power_sensor": self.charge_power_sensor,
            "power_reserve_w": self.power_reserve_w,
            "car_connected": _optional_dict(self.car_connected),
            "charging_window": _optional_dict(self.charging_window),
        }


@dataclass(frozen=True, slots=True)
class ChargingConfig:
    """Settings shared by all chargers."""

    enabled: bool = False
    one_at_a_time: bool = True
    chargers: tuple[Charger, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the charging settings as JSON-friendly data."""
        return {
            "enabled": self.enabled,
            "one_at_a_time": self.one_at_a_time,
            "chargers": [charger.to_dict() for charger in self.chargers],
        }


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
    appliance_cycling_step_factor: float = 0.5
    appliance_cycling_steps: int = 4
    charger_cycling_step_factor: float = 1.0
    charger_cycling_steps: int = 5
    penalty_threshold_w: int = 100

    def to_dict(self) -> dict[str, Any]:
        """Return the general parameters as JSON-friendly data."""
        return {
            "power_sensor": self.power_sensor,
            "power_limit_w": self.power_limit_w,
            "turn_on_margin_w": self.turn_on_margin_w,
            "regulation_window_s": self.regulation_window_s,
            "regulation_interval": self.regulation_interval,
            "wait_at_limit_s": self.wait_at_limit_s,
            "wait_curve_steepness": self.wait_curve_steepness,
            "wait_curve_pivot": self.wait_curve_pivot,
            "appliance_cycling_step_factor": self.appliance_cycling_step_factor,
            "appliance_cycling_steps": self.appliance_cycling_steps,
            "charger_cycling_step_factor": self.charger_cycling_step_factor,
            "charger_cycling_steps": self.charger_cycling_steps,
            "penalty_threshold_w": self.penalty_threshold_w,
        }


@dataclass(frozen=True, slots=True)
class KraftvaktConfig:
    """The whole configuration."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    appliances: tuple[Appliance, ...] = ()
    priority: tuple[PriorityEntry, ...] = ()
    charging: ChargingConfig = field(default_factory=ChargingConfig)

    def to_dict(self) -> dict[str, Any]:
        """Return the configuration as JSON-friendly data."""
        return {
            "general": self.general.to_dict(),
            "appliances": [appliance.to_dict() for appliance in self.appliances],
            "priority": [entry.to_dict() for entry in self.priority],
            "charging": self.charging.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ChargerSwitches:
    """The user's switches for a charger."""

    excluded: bool = False
    window_override: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Return the switches as JSON-friendly data."""
        return {"excluded": self.excluded, "window_override": self.window_override}


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
    """Return a short unique id for an appliance, variant or charger."""
    return uuid.uuid4().hex[:12]


def charger_switches_for(
    config: KraftvaktConfig, switches: Mapping[str, ChargerSwitches]
) -> dict[str, ChargerSwitches]:
    """Return the switches for exactly the chargers in the configuration."""
    return {
        charger.id: switches.get(charger.id, ChargerSwitches())
        for charger in config.charging.chargers
    }


def charger_switches_to_dict(
    switches: Mapping[str, ChargerSwitches],
) -> dict[str, dict[str, bool]]:
    """Return the charger switches as JSON-friendly data."""
    return {charger_id: state.to_dict() for charger_id, state in switches.items()}


def _optional_dict(value: Any) -> Any:
    return None if value is None else value.to_dict()


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
