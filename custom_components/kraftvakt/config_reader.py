"""Reading the stored and the received configuration into the model.

Home Assistant's editors may normalize the data from the panel, so missing
and empty values are tolerated and get defaults. A value of the wrong type is
an issue and is read as its default.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import time
from typing import Any

from .config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    Charger,
    ChargerSwitches,
    ChargingConfig,
    ChargingWindow,
    Condition,
    ConditionType,
    ConfigValidationError,
    GeneralConfig,
    Issue,
    IssueLocation,
    KraftvaktConfig,
    PriorityEntry,
    PriorityEntryType,
    Variant,
    new_id,
)


def read_config(data: Mapping[str, Any]) -> KraftvaktConfig:
    """Read a configuration from JSON-friendly data.

    Missing settings get their default values and unknown keys are ignored.
    Raises ConfigValidationError if a value has the wrong type or format.
    """
    reader = ConfigReader()
    config = reader.config(data)
    if reader.issues:
        raise ConfigValidationError(reader.issues)
    return config


def read_charger_switches(
    data: Mapping[str, Any],
) -> dict[str, ChargerSwitches]:
    """Read the charger switches, keyed by charger id, from JSON-friendly data.

    Raises ConfigValidationError if a value has the wrong type.
    """
    reader = ConfigReader()
    switches = reader.charger_switches(data)
    if reader.issues:
        raise ConfigValidationError(reader.issues)
    return switches


_TIME_PATTERN = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?")


class ConfigReader:
    """Reads JSON-friendly data into the model and collects type errors."""

    def __init__(self) -> None:
        """Start without issues."""
        self.issues: list[Issue] = []

    def config(self, data: Any) -> KraftvaktConfig:
        """Return the configuration in the data."""
        root = self._mapping(data, IssueLocation("general"), None)
        return KraftvaktConfig(
            general=self._general(root.get("general")),
            appliances=tuple(
                self._appliance(item)
                for item in self._list(
                    root.get("appliances"), IssueLocation("appliances")
                )
            ),
            priority=tuple(
                entry
                for item in self._list(root.get("priority"), IssueLocation("priority"))
                if (entry := self._priority_entry(item)) is not None
            ),
            charging=self._charging(root.get("charging")),
        )

    def charger_switches(self, data: Any) -> dict[str, ChargerSwitches]:
        """Return the charger switches in the data, by charger id."""
        location = IssueLocation("chargers")
        switches = {}
        for charger_id, item in self._mapping(data, location, None).items():
            charger_location = IssueLocation("chargers", str(charger_id))
            values = self._mapping(item, charger_location, None)
            switches[str(charger_id)] = ChargerSwitches(
                excluded=self._bool(values, "excluded", False, charger_location),
                window_override=self._bool(
                    values, "window_override", False, charger_location
                ),
            )
        return switches

    def _general(self, data: Any) -> GeneralConfig:
        location = IssueLocation("general")
        values = self._mapping(data, location, None)
        defaults = GeneralConfig()
        return GeneralConfig(
            power_sensor=self._text(values, "power_sensor", location),
            power_limit_w=self._integer(
                values, "power_limit_w", defaults.power_limit_w, location
            ),
            turn_on_margin_w=self._integer(
                values, "turn_on_margin_w", defaults.turn_on_margin_w, location
            ),
            regulation_window_s=self._integer(
                values, "regulation_window_s", defaults.regulation_window_s, location
            ),
            regulation_interval=self._integer(
                values, "regulation_interval", defaults.regulation_interval, location
            ),
            wait_at_limit_s=self._integer(
                values, "wait_at_limit_s", defaults.wait_at_limit_s, location
            ),
            wait_curve_steepness=self._number(
                values,
                "wait_curve_steepness",
                defaults.wait_curve_steepness,
                location,
            ),
            wait_curve_pivot=self._integer(
                values, "wait_curve_pivot", defaults.wait_curve_pivot, location
            ),
            appliance_cycling_step_factor=self._number(
                values,
                "appliance_cycling_step_factor",
                defaults.appliance_cycling_step_factor,
                location,
            ),
            appliance_cycling_steps=self._integer(
                values,
                "appliance_cycling_steps",
                defaults.appliance_cycling_steps,
                location,
            ),
            charger_cycling_step_factor=self._number(
                values,
                "charger_cycling_step_factor",
                defaults.charger_cycling_step_factor,
                location,
            ),
            charger_cycling_steps=self._integer(
                values,
                "charger_cycling_steps",
                defaults.charger_cycling_steps,
                location,
            ),
            penalty_threshold_w=self._integer(
                values, "penalty_threshold_w", defaults.penalty_threshold_w, location
            ),
        )

    def _appliance(self, data: Any) -> Appliance:
        values = self._mapping(data, IssueLocation("appliances"), None)
        appliance_id = self._id(values, IssueLocation("appliances"))
        location = IssueLocation("appliances", appliance_id)
        return Appliance(
            id=appliance_id,
            entity_id=self._text(values, "entity_id", location),
            turn_on=self._action(values, "turn_on", location),
            turn_off=self._action(values, "turn_off", location),
            power_reserve_w=self._integer(values, "power_reserve_w", None, location),
            variants=tuple(
                self._variant(item, appliance_id)
                for item in self._list(values.get("variants"), location, "variants")
            ),
        )

    def _variant(self, data: Any, appliance_id: str) -> Variant:
        appliance_location = IssueLocation("appliances", appliance_id)
        values = self._mapping(data, appliance_location, "variants")
        variant_id = self._id(values, appliance_location)
        location = IssueLocation("appliances", appliance_id, f"variants.{variant_id}.")
        if values.get("condition") is None:
            self.issues.append(location.issue("required", "condition"))
        condition = self._condition(values, "condition", location)
        return Variant(
            id=variant_id,
            label=self._text(values, "label", location) or "",
            condition=condition or Condition(ConditionType.TEMPLATE, ""),
        )

    def _priority_entry(self, data: Any) -> PriorityEntry | None:
        location = IssueLocation("priority")
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
        location = IssueLocation("charging")
        values = self._mapping(data, location, None)
        return ChargingConfig(
            enabled=self._bool(values, "enabled", False, location),
            one_at_a_time=self._bool(values, "one_at_a_time", True, location),
            chargers=tuple(
                self._charger(item)
                for item in self._list(
                    values.get("chargers"), IssueLocation("chargers")
                )
            ),
        )

    def _charger(self, data: Any) -> Charger:
        values = self._mapping(data, IssueLocation("chargers"), None)
        charger_id = self._id(values, IssueLocation("chargers"))
        location = IssueLocation("chargers", charger_id)
        defaults = Charger(id=charger_id)
        return Charger(
            id=charger_id,
            entity_id=self._text(values, "entity_id", location),
            activate=self._action(values, "activate", location),
            deactivate=self._action(values, "deactivate", location),
            set_current=self._action(
                values, "set_current", location, entity_allowed=True
            ),
            min_current_a=self._integer(
                values, "min_current_a", defaults.min_current_a, location
            ),
            max_current_a=self._integer(
                values, "max_current_a", defaults.max_current_a, location
            ),
            charge_power_sensor=self._text(values, "charge_power_sensor", location),
            power_reserve_w=self._integer(
                values, "power_reserve_w", defaults.power_reserve_w, location
            ),
            car_connected=self._condition(values, "car_connected", location),
            charging_window=self._charging_window(values, location),
        )

    def _action(
        self,
        values: Mapping[str, Any],
        key: str,
        location: IssueLocation,
        *,
        entity_allowed: bool = False,
    ) -> ActionConfig | None:
        action = values.get(key)
        if action is None:
            return None
        if isinstance(action, Mapping):
            if action.get("mode") == ActionMode.DEFAULT:
                return ActionConfig(ActionMode.DEFAULT)
            entity_id = action.get("entity_id") or None
            if (
                entity_allowed
                and action.get("mode") == ActionMode.ENTITY
                and (entity_id is None or isinstance(entity_id, str))
            ):
                return ActionConfig(ActionMode.ENTITY, entity_id=entity_id)
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
        self, values: Mapping[str, Any], key: str, location: IssueLocation
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
        self, values: Mapping[str, Any], location: IssueLocation
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

    def _id(self, values: Mapping[str, Any], location: IssueLocation) -> str:
        return self._text(values, "id", location) or new_id()

    def _text(
        self, values: Mapping[str, Any], key: str, location: IssueLocation
    ) -> str | None:
        value = values.get(key)
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            self.issues.append(location.issue("invalid_type", key))
            return None
        return value

    def _bool(
        self,
        values: Mapping[str, Any],
        key: str,
        default: bool,
        location: IssueLocation,
    ) -> bool:
        value = values.get(key, default)
        if not isinstance(value, bool):
            self.issues.append(location.issue("invalid_type", key))
            return default
        return value

    def _number[T: float | None](
        self, values: Mapping[str, Any], key: str, default: T, location: IssueLocation
    ) -> float | T:
        value = values.get(key)
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int | float):
            self.issues.append(location.issue("invalid_type", key))
            return default
        return float(value)

    def _integer[T: int | None](
        self, values: Mapping[str, Any], key: str, default: T, location: IssueLocation
    ) -> int | T:
        value = self._number(values, key, None, location)
        if value is None:
            return default
        if not value.is_integer():
            self.issues.append(location.issue("not_integer", key))
            return default
        return int(value)

    def _mapping(
        self, data: Any, location: IssueLocation, key: str | None
    ) -> Mapping[str, Any]:
        if data is None:
            return {}
        if not isinstance(data, Mapping):
            self.issues.append(location.issue("invalid_type", key))
            return {}
        return data

    def _list(
        self, data: Any, location: IssueLocation, key: str | None = None
    ) -> list[Any]:
        if data is None:
            return []
        if not isinstance(data, list):
            self.issues.append(location.issue("invalid_type", key))
            return []
        return data
