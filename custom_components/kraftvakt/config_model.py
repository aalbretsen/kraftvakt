"""Configuration model for Kraftvakt.

The configuration is everything the user sets up in the panel (GEN-011). It is
immutable: a change is made by building a new configuration and saving it.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
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

    def to_dict(self) -> dict[str, Any]:
        """Return the action as JSON-friendly data."""
        if self.mode is ActionMode.DEFAULT:
            return {"mode": self.mode.value}
        return {"mode": self.mode.value, "action": list(self.steps)}


@dataclass(frozen=True, slots=True)
class Condition:
    """A true/false value from a boolean entity or a template (GEN-009)."""

    type: ConditionType
    value: str

    def to_dict(self) -> dict[str, Any]:
        """Return the condition as JSON-friendly data."""
        return {"type": self.type.value, "value": self.value}


@dataclass(frozen=True, slots=True)
class Variant:
    """An extra entry of an appliance in the priority list (APP-006)."""

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
    """A device that Kraftvakt turns on and off (APP-001 to APP-006)."""

    id: str
    entity_id: str | None = None
    turn_on: ActionConfig | None = None
    turn_off: ActionConfig | None = None
    power_reserve_kw: float | None = None
    variants: tuple[Variant, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the appliance as JSON-friendly data."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "turn_on": _optional_dict(self.turn_on),
            "turn_off": _optional_dict(self.turn_off),
            "power_reserve_kw": self.power_reserve_kw,
            "variants": [variant.to_dict() for variant in self.variants],
        }


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
    """Time of day when a charger may charge, possibly across midnight (LAD-025)."""

    start: time
    end: time

    def to_dict(self) -> dict[str, str]:
        """Return the window as JSON-friendly data with times as HH:MM."""
        return {"start": _format_time(self.start), "end": _format_time(self.end)}


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
            "power_reserve_kw": self.power_reserve_kw,
            "car_connected": _optional_dict(self.car_connected),
            "charging_window": _optional_dict(self.charging_window),
        }


@dataclass(frozen=True, slots=True)
class ChargingConfig:
    """Settings shared by all chargers (LAD-001 to LAD-003)."""

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
    """General parameters (GUI-008)."""

    power_sensor: str | None = None
    power_limit_kw: float = 10.0
    regulation_window_s: int = 60
    regulation_interval: int = 1
    wait_at_limit_min: int = 5
    penalty_threshold_kw: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Return the general parameters as JSON-friendly data."""
        return {
            "power_sensor": self.power_sensor,
            "power_limit_kw": self.power_limit_kw,
            "regulation_window_s": self.regulation_window_s,
            "regulation_interval": self.regulation_interval,
            "wait_at_limit_min": self.wait_at_limit_min,
            "penalty_threshold_kw": self.penalty_threshold_kw,
        }


@dataclass(frozen=True, slots=True)
class KraftvaktConfig:
    """The whole configuration."""

    general: GeneralConfig = field(default_factory=GeneralConfig)
    appliances: tuple[Appliance, ...] = ()
    priority: tuple[PriorityEntry, ...] = ()
    charging: ChargingConfig = field(default_factory=ChargingConfig)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> KraftvaktConfig:
        """Read a configuration from JSON-friendly data.

        Missing settings get their default values and unknown keys are ignored.
        Raises ConfigValidationError if a value has the wrong type or format.
        """
        reader = _Reader()
        config = reader.config(data)
        if reader.issues:
            raise ConfigValidationError(reader.issues)
        return config

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
    """The user's switches for a charger (ENT-003, ENT-004)."""

    excluded: bool = False
    window_override: bool = False

    def to_dict(self) -> dict[str, bool]:
        """Return the switches as JSON-friendly data."""
        return {"excluded": self.excluded, "window_override": self.window_override}


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


class ConfigValidationError(ValueError):
    """Raised when a configuration is invalid. Holds every issue found."""

    def __init__(self, issues: list[Issue]) -> None:
        """Create the error from the issues found."""
        super().__init__(", ".join(issue.code for issue in issues))
        self.issues = issues


def new_id() -> str:
    """Return a short unique id for an appliance, variant or charger."""
    return uuid.uuid4().hex[:12]


def charger_switches_from_dict(
    data: Mapping[str, Any],
) -> dict[str, ChargerSwitches]:
    """Read the charger switches, keyed by charger id, from JSON-friendly data.

    Raises ConfigValidationError if a value has the wrong type.
    """
    reader = _Reader()
    switches = reader.charger_switches(data)
    if reader.issues:
        raise ConfigValidationError(reader.issues)
    return switches


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


_TIME_PATTERN = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?")


@dataclass(frozen=True, slots=True)
class _Location:
    """Where in the configuration a value is read from."""

    section: str
    target: str | None = None
    prefix: str = ""

    def issue(self, code: str, field_name: str | None = None) -> Issue:
        name = None if field_name is None else f"{self.prefix}{field_name}"
        return Issue(code, self.section, self.target, name)


class _Reader:
    """Reads JSON-friendly data into the model and collects type errors.

    The data comes from the panel and may be normalized by Home Assistant's
    editors, so missing and empty values are tolerated and get defaults.
    """

    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def config(self, data: Any) -> KraftvaktConfig:
        root = self._mapping(data, _Location("general"), None)
        return KraftvaktConfig(
            general=self._general(root.get("general")),
            appliances=tuple(
                self._appliance(item)
                for item in self._list(root.get("appliances"), _Location("appliances"))
            ),
            priority=tuple(
                entry
                for item in self._list(root.get("priority"), _Location("priority"))
                if (entry := self._priority_entry(item)) is not None
            ),
            charging=self._charging(root.get("charging")),
        )

    def charger_switches(self, data: Any) -> dict[str, ChargerSwitches]:
        location = _Location("chargers")
        switches = {}
        for charger_id, item in self._mapping(data, location, None).items():
            charger_location = _Location("chargers", str(charger_id))
            values = self._mapping(item, charger_location, None)
            switches[str(charger_id)] = ChargerSwitches(
                excluded=self._bool(values, "excluded", False, charger_location),
                window_override=self._bool(
                    values, "window_override", False, charger_location
                ),
            )
        return switches

    def _general(self, data: Any) -> GeneralConfig:
        location = _Location("general")
        values = self._mapping(data, location, None)
        defaults = GeneralConfig()
        return GeneralConfig(
            power_sensor=self._text(values, "power_sensor", location),
            power_limit_kw=self._number(
                values, "power_limit_kw", defaults.power_limit_kw, location
            ),
            regulation_window_s=self._integer(
                values, "regulation_window_s", defaults.regulation_window_s, location
            ),
            regulation_interval=self._integer(
                values, "regulation_interval", defaults.regulation_interval, location
            ),
            wait_at_limit_min=self._integer(
                values, "wait_at_limit_min", defaults.wait_at_limit_min, location
            ),
            penalty_threshold_kw=self._number(
                values, "penalty_threshold_kw", defaults.penalty_threshold_kw, location
            ),
        )

    def _appliance(self, data: Any) -> Appliance:
        values = self._mapping(data, _Location("appliances"), None)
        appliance_id = self._id(values, _Location("appliances"))
        location = _Location("appliances", appliance_id)
        return Appliance(
            id=appliance_id,
            entity_id=self._text(values, "entity_id", location),
            turn_on=self._action(values, "turn_on", location),
            turn_off=self._action(values, "turn_off", location),
            power_reserve_kw=self._number(values, "power_reserve_kw", None, location),
            variants=tuple(
                self._variant(item, appliance_id)
                for item in self._list(values.get("variants"), location, "variants")
            ),
        )

    def _variant(self, data: Any, appliance_id: str) -> Variant:
        appliance_location = _Location("appliances", appliance_id)
        values = self._mapping(data, appliance_location, "variants")
        variant_id = self._id(values, appliance_location)
        location = _Location("appliances", appliance_id, f"variants.{variant_id}.")
        if values.get("condition") is None:
            self.issues.append(location.issue("required", "condition"))
        condition = self._condition(values, "condition", location)
        return Variant(
            id=variant_id,
            label=self._text(values, "label", location) or "",
            condition=condition or Condition(ConditionType.TEMPLATE, ""),
        )

    def _priority_entry(self, data: Any) -> PriorityEntry | None:
        location = _Location("priority")
        values = self._mapping(data, location, None)
        entry_type = values.get("type")
        if entry_type == PriorityEntryType.EV_CHARGING:
            return PriorityEntry.ev_charging()
        appliance_id = self._text(values, "appliance_id", location)
        if entry_type != PriorityEntryType.APPLIANCE or appliance_id is None:
            self.issues.append(location.issue("invalid_type"))
            return None
        return PriorityEntry.for_appliance(
            appliance_id, self._text(values, "variant_id", location)
        )

    def _charging(self, data: Any) -> ChargingConfig:
        location = _Location("charging")
        values = self._mapping(data, location, None)
        return ChargingConfig(
            enabled=self._bool(values, "enabled", False, location),
            one_at_a_time=self._bool(values, "one_at_a_time", True, location),
            chargers=tuple(
                self._charger(item)
                for item in self._list(values.get("chargers"), _Location("chargers"))
            ),
        )

    def _charger(self, data: Any) -> Charger:
        values = self._mapping(data, _Location("chargers"), None)
        charger_id = self._id(values, _Location("chargers"))
        location = _Location("chargers", charger_id)
        defaults = Charger(id=charger_id)
        return Charger(
            id=charger_id,
            entity_id=self._text(values, "entity_id", location),
            activate=self._action(values, "activate", location),
            deactivate=self._action(values, "deactivate", location),
            set_current=self._action(values, "set_current", location),
            min_current_a=self._integer(
                values, "min_current_a", defaults.min_current_a, location
            ),
            max_current_a=self._integer(
                values, "max_current_a", defaults.max_current_a, location
            ),
            charge_power_sensor=self._text(values, "charge_power_sensor", location),
            power_reserve_kw=self._number(
                values, "power_reserve_kw", defaults.power_reserve_kw, location
            ),
            car_connected=self._condition(values, "car_connected", location),
            charging_window=self._charging_window(values, location),
        )

    def _action(
        self, values: Mapping[str, Any], key: str, location: _Location
    ) -> ActionConfig | None:
        action = values.get(key)
        if action is None:
            return None
        if isinstance(action, Mapping):
            if action.get("mode") == ActionMode.DEFAULT:
                return ActionConfig(ActionMode.DEFAULT)
            if action.get("mode") == ActionMode.CUSTOM:
                steps = action.get("action") or []
                if isinstance(steps, Mapping):
                    steps = [steps]
                if isinstance(steps, list) and all(
                    isinstance(step, Mapping) for step in steps
                ):
                    return ActionConfig(
                        ActionMode.CUSTOM, tuple(dict(step) for step in steps)
                    )
        self.issues.append(location.issue("invalid_type", key))
        return None

    def _condition(
        self, values: Mapping[str, Any], key: str, location: _Location
    ) -> Condition | None:
        condition = values.get(key)
        if condition is None:
            return None
        if not isinstance(condition, Mapping):
            self.issues.append(location.issue("invalid_type", key))
            return None
        condition_type = condition.get("type")
        value = condition.get("value", "")
        if condition_type not in tuple(ConditionType) or not isinstance(value, str):
            self.issues.append(location.issue("invalid_type", key))
            return None
        return Condition(ConditionType(condition_type), value)

    def _charging_window(
        self, values: Mapping[str, Any], location: _Location
    ) -> ChargingWindow | None:
        data = values.get("charging_window")
        if data is None:
            return None
        window = self._mapping(data, location, "charging_window")
        start = self._time(window.get("start"))
        end = self._time(window.get("end"))
        if start is None or end is None:
            self.issues.append(location.issue("invalid_time", "charging_window"))
            return None
        return ChargingWindow(start, end)

    def _time(self, value: Any) -> time | None:
        if not isinstance(value, str):
            return None
        match = _TIME_PATTERN.fullmatch(value)
        if match is None:
            return None
        hour, minute, second = (int(part or 0) for part in match.groups())
        if hour > 23 or minute > 59 or second > 59:
            return None
        return time(hour, minute, second)

    def _id(self, values: Mapping[str, Any], location: _Location) -> str:
        return self._text(values, "id", location) or new_id()

    def _text(
        self, values: Mapping[str, Any], key: str, location: _Location
    ) -> str | None:
        value = values.get(key)
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            self.issues.append(location.issue("invalid_type", key))
            return None
        return value

    def _bool(
        self, values: Mapping[str, Any], key: str, default: bool, location: _Location
    ) -> bool:
        value = values.get(key, default)
        if not isinstance(value, bool):
            self.issues.append(location.issue("invalid_type", key))
            return default
        return value

    def _number[T: float | None](
        self, values: Mapping[str, Any], key: str, default: T, location: _Location
    ) -> float | T:
        value = values.get(key)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int | float):
            self.issues.append(location.issue("invalid_type", key))
            return default
        return float(value)

    def _integer(
        self, values: Mapping[str, Any], key: str, default: int, location: _Location
    ) -> int:
        value = self._number(values, key, None, location)
        if value is None:
            return default
        if not value.is_integer():
            self.issues.append(location.issue("not_integer", key))
            return default
        return int(value)

    def _mapping(
        self, data: Any, location: _Location, key: str | None
    ) -> Mapping[str, Any]:
        if data is None:
            return {}
        if not isinstance(data, Mapping):
            self.issues.append(location.issue("invalid_type", key))
            return {}
        return data

    def _list(
        self, data: Any, location: _Location, key: str | None = None
    ) -> list[Any]:
        if data is None:
            return []
        if not isinstance(data, list):
            self.issues.append(location.issue("invalid_type", key))
            return []
        return data
