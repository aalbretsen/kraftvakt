"""Configuration model for Kraftvakt.

The configuration is everything the user sets up in the panel. It is
immutable: a change is made by building a new configuration and saving it.
"""

from __future__ import annotations

import copy
import re
import uuid
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import time
from enum import StrEnum
from typing import Any, Final

import voluptuous as vol
from homeassistant.core import valid_entity_id
from homeassistant.helpers import config_validation as cv


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


POWER_LIMIT_KW = Range(1, 50, 0.01)
TURN_ON_MARGIN_KW = Range(0.01, 1, 0.01)
REGULATION_WINDOW_S = Range(10, 600, 1)
REGULATION_INTERVAL = Range(1, 4, 1)
WAIT_AT_LIMIT_MIN = Range(0, 10, 1)
PENALTY_THRESHOLD_KW = Range(0, 10, 0.01)
APPLIANCE_POWER_RESERVE_KW = Range(0, None, 0.01)
CHARGER_POWER_RESERVE_KW = Range(0, 5, 0.01)
CHARGING_CURRENT_A = Range(1, None, 1)

# The ranges of the settings, by section and field, used both to validate the
# configuration and to tell the panel the limits.
SETTING_RANGES: Final[Mapping[str, Mapping[str, Range]]] = {
    "general": {
        "power_limit_kw": POWER_LIMIT_KW,
        "turn_on_margin_kw": TURN_ON_MARGIN_KW,
        "regulation_window_s": REGULATION_WINDOW_S,
        "regulation_interval": REGULATION_INTERVAL,
        "wait_at_limit_min": WAIT_AT_LIMIT_MIN,
        "penalty_threshold_kw": PENALTY_THRESHOLD_KW,
    },
    "appliances": {"power_reserve_kw": APPLIANCE_POWER_RESERVE_KW},
    "chargers": {
        "min_current_a": CHARGING_CURRENT_A,
        "max_current_a": CHARGING_CURRENT_A,
        "power_reserve_kw": CHARGER_POWER_RESERVE_KW,
    },
}


class ActionMode(StrEnum):
    """Whether an action uses the default action for the entity or a custom one."""

    DEFAULT = "default"
    CUSTOM = "custom"


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

    def to_dict(self) -> dict[str, Any]:
        """Return the action as JSON-friendly data."""
        if self.mode is ActionMode.DEFAULT:
            return {"mode": self.mode.value}
        return {"mode": self.mode.value, "action": list(self.steps)}


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
    power_limit_kw: float = 10.0
    turn_on_margin_kw: float = 0.1
    regulation_window_s: int = 60
    regulation_interval: int = 1
    wait_at_limit_min: int = 5
    penalty_threshold_kw: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Return the general parameters as JSON-friendly data."""
        return {
            "power_sensor": self.power_sensor,
            "power_limit_kw": self.power_limit_kw,
            "turn_on_margin_kw": self.turn_on_margin_kw,
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
    """The user's switches for a charger."""

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


def parse_config(data: Mapping[str, Any]) -> KraftvaktConfig:
    """Read and validate a configuration from the panel.

    Missing entries in the priority list are added at the bottom.
    Raises ConfigValidationError with every issue found if the configuration
    is invalid. An incomplete configuration is valid. Must be called
    from the event loop, since Home Assistant validates templates there.
    """
    config = _complete_priority(KraftvaktConfig.from_dict(data))
    issues = validate_config(config) + action_and_template_issues(config)
    if issues:
        raise ConfigValidationError(issues)
    return config


def validate_config(config: KraftvaktConfig) -> list[Issue]:
    """Return every rule the configuration breaks.

    The syntax of custom actions and templates is checked separately by
    action_and_template_issues, since it needs the event loop.
    """
    return [
        *_general_issues(config.general),
        *(
            Issue("duplicate_id", "appliances", appliance_id)
            for appliance_id in _duplicate_ids(config.appliances)
        ),
        *(issue for item in config.appliances for issue in _appliance_issues(item)),
        *(
            Issue("duplicate_id", "chargers", charger_id)
            for charger_id in _duplicate_ids(config.charging.chargers)
        ),
        *(
            issue
            for item in config.charging.chargers
            for issue in _charger_issues(item)
        ),
        *_unique_entity_issues(config),
        *_priority_issues(config),
    ]


def action_and_template_issues(config: KraftvaktConfig) -> list[Issue]:
    """Return custom actions and templates that Home Assistant cannot parse.

    Must be called from the event loop, since Home Assistant validates
    templates there.
    """
    issues = []
    for section, target, field_name, action in _custom_actions(config):
        try:
            cv.SCRIPT_SCHEMA(copy.deepcopy(list(action.steps)))
        except vol.Invalid:
            issues.append(Issue("invalid_action", section, target, field_name))
    for section, target, field_name, condition in _conditions(config):
        if condition.type is ConditionType.TEMPLATE and condition.value:
            try:
                cv.template(condition.value)
            except vol.Invalid:
                issues.append(Issue("invalid_template", section, target, field_name))
    return issues


def missing_items(config: KraftvaktConfig) -> list[Issue]:
    """Return what is missing before the regulation can start.

    Chargers count only while charging is enabled. When only one charger
    may charge at a time, each charger needs «car connected». Without it,
    chargers without a car would take turns being activated.
    """
    missing = []
    if config.general.power_sensor is None:
        missing.append(Issue("missing_power_sensor", "general", None, "power_sensor"))
    for appliance in config.appliances:
        missing += _missing_entity_and_actions(
            "appliances", appliance, ("turn_on", "turn_off")
        )
    if config.charging.enabled:
        for charger in config.charging.chargers:
            missing += _missing_entity_and_actions(
                "chargers", charger, ("activate", "deactivate", "set_current")
            )
            if charger.charge_power_sensor is None:
                missing.append(
                    Issue(
                        "missing_charge_power_sensor",
                        "chargers",
                        charger.id,
                        "charge_power_sensor",
                    )
                )
            if config.charging.one_at_a_time and charger.car_connected is None:
                missing.append(
                    Issue(
                        "missing_car_connected", "chargers", charger.id, "car_connected"
                    )
                )
    return missing


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


def charger_switches_for(
    config: KraftvaktConfig, switches: Mapping[str, ChargerSwitches]
) -> dict[str, ChargerSwitches]:
    """Return the switches for exactly the chargers in the configuration.

    Chargers without stored switches get the default positions, and switches
    for chargers that are no longer configured are left out.
    """
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
            turn_on_margin_kw=self._number(
                values, "turn_on_margin_kw", defaults.turn_on_margin_kw, location
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


def _general_issues(general: GeneralConfig) -> list[Issue]:
    location = _Location("general")
    return [
        *_entity_format_issues(location, "power_sensor", general.power_sensor),
        *_ranges_issues(location, general),
    ]


def _appliance_issues(appliance: Appliance) -> list[Issue]:
    location = _Location("appliances", appliance.id)
    issues = [
        *_entity_format_issues(location, "entity_id", appliance.entity_id),
        *_ranges_issues(location, appliance),
    ]
    issues += [
        location.issue("duplicate_id", f"variants.{variant_id}")
        for variant_id in _duplicate_ids(appliance.variants)
    ]
    labels = Counter(variant.label.strip() for variant in appliance.variants)
    for variant in appliance.variants:
        variant_location = replace(location, prefix=f"variants.{variant.id}.")
        label = variant.label.strip()
        if not label:
            issues.append(variant_location.issue("empty_label", "label"))
        elif labels[label] > 1:
            issues.append(variant_location.issue("duplicate_label", "label"))
        issues += _condition_issues(variant_location, "condition", variant.condition)
    return issues


def _charger_issues(charger: Charger) -> list[Issue]:
    location = _Location("chargers", charger.id)
    issues = [
        *_entity_format_issues(location, "entity_id", charger.entity_id),
        *_entity_format_issues(
            location, "charge_power_sensor", charger.charge_power_sensor
        ),
        *_ranges_issues(location, charger),
    ]
    if charger.min_current_a > charger.max_current_a:
        issues.append(location.issue("min_current_above_max", "min_current_a"))
    if charger.car_connected is not None:
        issues += _condition_issues(location, "car_connected", charger.car_connected)
    window = charger.charging_window
    if window is not None:
        if window.start.second or window.end.second:
            issues.append(location.issue("invalid_resolution", "charging_window"))
        if window.start == window.end:
            issues.append(location.issue("window_start_equals_end", "charging_window"))
    return issues


def _condition_issues(
    location: _Location, field_name: str, condition: Condition
) -> list[Issue]:
    if not condition.value.strip():
        return [location.issue("required", field_name)]
    if condition.type is ConditionType.ENTITY:
        return _entity_format_issues(location, field_name, condition.value)
    return []


def _entity_format_issues(
    location: _Location, field_name: str, entity_id: str | None
) -> list[Issue]:
    if entity_id is None or valid_entity_id(entity_id):
        return []
    return [location.issue("invalid_entity_id", field_name)]


def _ranges_issues(
    location: _Location, item: GeneralConfig | Appliance | Charger
) -> list[Issue]:
    """Check the settings of the item that have a range in SETTING_RANGES.

    Optional settings that are not given are not checked.
    """
    return [
        issue
        for field_name, value_range in SETTING_RANGES[location.section].items()
        if (value := getattr(item, field_name)) is not None
        for issue in _range_issues(location, field_name, value, value_range)
    ]


def _range_issues(
    location: _Location, field_name: str, value: float, value_range: Range
) -> list[Issue]:
    if not value_range.contains(value):
        return [location.issue("out_of_range", field_name)]
    if not value_range.matches_step(value):
        return [location.issue("invalid_resolution", field_name)]
    return []


def _duplicate_ids(items: Iterable[Appliance | Variant | Charger]) -> list[str]:
    counts = Counter(item.id for item in items)
    return [item_id for item_id, count in counts.items() if count > 1]


def _unique_entity_issues(config: KraftvaktConfig) -> list[Issue]:
    """Each entity may identify only one appliance or charger."""
    owners = [
        *(("appliances", item.id, item.entity_id) for item in config.appliances),
        *(("chargers", item.id, item.entity_id) for item in config.charging.chargers),
    ]
    counts = Counter(entity_id for _, _, entity_id in owners if entity_id)
    return [
        Issue("duplicate_entity", section, target, "entity_id")
        for section, target, entity_id in owners
        if entity_id and counts[entity_id] > 1
    ]


def _priority_issues(config: KraftvaktConfig) -> list[Issue]:
    """The priority list holds every appliance and variant exactly once.

    It holds EV charging exactly once when charging is enabled.
    """
    expected = _expected_priority(config)
    counts = Counter(config.priority)
    issues = []
    for entry, count in counts.items():
        location = _priority_location(entry)
        if entry not in expected:
            code = (
                "ev_charging_disabled"
                if entry.type is PriorityEntryType.EV_CHARGING
                else "unknown_priority_entry"
            )
            issues.append(location.issue(code, _priority_field(entry)))
        elif count > 1:
            issues.append(
                location.issue("duplicate_priority_entry", _priority_field(entry))
            )
    issues += [
        _priority_location(entry).issue(
            "missing_priority_entry", _priority_field(entry)
        )
        for entry in expected
        if entry not in counts
    ]
    return issues


def _complete_priority(config: KraftvaktConfig) -> KraftvaktConfig:
    """Add missing entries at the bottom of the priority list."""
    missing = [
        entry for entry in _expected_priority(config) if entry not in config.priority
    ]
    return replace(config, priority=(*config.priority, *missing))


def _expected_priority(config: KraftvaktConfig) -> list[PriorityEntry]:
    expected = []
    for appliance in config.appliances:
        expected.append(PriorityEntry.for_appliance(appliance.id))
        expected += [
            PriorityEntry.for_appliance(appliance.id, variant.id)
            for variant in appliance.variants
        ]
    if config.charging.enabled:
        expected.append(PriorityEntry.ev_charging())
    return expected


def _priority_location(entry: PriorityEntry) -> _Location:
    return _Location("priority", entry.appliance_id)


def _priority_field(entry: PriorityEntry) -> str | None:
    return None if entry.variant_id is None else f"variants.{entry.variant_id}"


def _custom_actions(
    config: KraftvaktConfig,
) -> Iterable[tuple[str, str, str, ActionConfig]]:
    for appliance in config.appliances:
        for field_name in ("turn_on", "turn_off"):
            action = getattr(appliance, field_name)
            if action is not None and action.steps:
                yield "appliances", appliance.id, field_name, action
    for charger in config.charging.chargers:
        for field_name in ("activate", "deactivate", "set_current"):
            action = getattr(charger, field_name)
            if action is not None and action.steps:
                yield "chargers", charger.id, field_name, action


def _conditions(config: KraftvaktConfig) -> Iterable[tuple[str, str, str, Condition]]:
    for appliance in config.appliances:
        for variant in appliance.variants:
            yield (
                "appliances",
                appliance.id,
                f"variants.{variant.id}.condition",
                variant.condition,
            )
    for charger in config.charging.chargers:
        if charger.car_connected is not None:
            yield "chargers", charger.id, "car_connected", charger.car_connected


def _missing_entity_and_actions(
    section: str, item: Appliance | Charger, action_fields: tuple[str, ...]
) -> list[Issue]:
    missing = []
    if item.entity_id is None:
        missing.append(Issue("missing_entity", section, item.id, "entity_id"))
    for field_name in action_fields:
        action = getattr(item, field_name)
        if action is None or (action.mode is ActionMode.CUSTOM and not action.steps):
            missing.append(Issue("missing_action", section, item.id, field_name))
    return missing
