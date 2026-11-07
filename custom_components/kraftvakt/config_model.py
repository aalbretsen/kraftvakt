"""Configuration model for Kraftvakt.

The configuration is everything the user sets up in the panel (GEN-011). It is
immutable: a change is made by building a new configuration and saving it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import StrEnum
from typing import Any


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


POWER_LIMIT_KW = Range(1, 50, 0.01)
REGULATION_WINDOW_S = Range(10, 600, 1)
REGULATION_INTERVAL = Range(1, 4, 1)
WAIT_AT_LIMIT_MIN = Range(0, 10, 1)
PENALTY_THRESHOLD_KW = Range(0, 10, 0.01)
APPLIANCE_POWER_RESERVE_KW = Range(0, None, 0.01)
CHARGER_POWER_RESERVE_KW = Range(0, 5, 0.01)
CHARGING_CURRENT_A = Range(1, None, 1)


class ActionMode(StrEnum):
    """Whether an action uses the default action for the entity or a custom one."""

    DEFAULT = "default"
    CUSTOM = "custom"


class ConditionType(StrEnum):
    """How a true/false value is given (GEN-009)."""

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


@dataclass(frozen=True, slots=True)
class Condition:
    """A true/false value from a boolean entity or a template (GEN-009)."""

    type: ConditionType
    value: str


@dataclass(frozen=True, slots=True)
class Variant:
    """An extra entry of an appliance in the priority list (APP-006)."""

    id: str
    label: str
    condition: Condition


@dataclass(frozen=True, slots=True)
class Appliance:
    """A device that Kraftvakt turns on and off (APP-001 to APP-006)."""

    id: str
    entity_id: str | None = None
    turn_on: ActionConfig | None = None
    turn_off: ActionConfig | None = None
    power_reserve_kw: float | None = None
    variants: tuple[Variant, ...] = ()


@dataclass(frozen=True, slots=True)
class PriorityEntry:
    """An entry in the priority list (APP-001, APP-005, APP-008)."""

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


@dataclass(frozen=True, slots=True)
class ChargingWindow:
    """Time of day when a charger may charge, possibly across midnight (LAD-025)."""

    start: time
    end: time


@dataclass(frozen=True, slots=True)
class Charger:
    """An EV charger (LAD-003 to LAD-010, LAD-025)."""

    id: str
    entity_id: str | None = None
    activate: ActionConfig | None = None
    deactivate: ActionConfig | None = None
    set_current: ActionConfig | None = None
    min_current_a: int = 6
    max_current_a: int = 16
    charge_power_sensor: str | None = None
    power_reserve_kw: float = 4.0
    car_connected: Condition | None = None
    charging_window: ChargingWindow | None = None


@dataclass(frozen=True, slots=True)
class ChargingConfig:
    """Settings shared by all chargers (LAD-001 to LAD-003)."""

    enabled: bool = False
    one_at_a_time: bool = True
    chargers: tuple[Charger, ...] = ()


@dataclass(frozen=True, slots=True)
class GeneralConfig:
    """General parameters (GUI-008)."""

    power_sensor: str | None = None
    power_limit_kw: float = 10.0
    regulation_window_s: int = 60
    regulation_interval: int = 1
    wait_at_limit_min: int = 5
    penalty_threshold_kw: float = 1.0


@dataclass(frozen=True, slots=True)
class KraftvaktConfig:
    """The whole configuration."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    appliances: tuple[Appliance, ...] = ()
    priority: tuple[PriorityEntry, ...] = ()
    charging: ChargingConfig = field(default_factory=ChargingConfig)


@dataclass(frozen=True, slots=True)
class ChargerSwitches:
    """The user's switches for a charger (ENT-003, ENT-004)."""

    excluded: bool = False
    window_override: bool = False


@dataclass(frozen=True, slots=True)
class Issue:
    """A validation error or a missing setting.

    ``section`` is the part of the configuration (``general``, ``appliances``,
    ``priority``, ``charging`` or ``chargers``), ``target`` the id of an appliance
    or charger, and ``field`` the setting, with ``variants.<id>`` in front for a
    variant.
    """

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
