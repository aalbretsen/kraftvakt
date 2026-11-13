"""Reading the stored and the received configuration into the model.

Home Assistant's editors may normalize the data from the panel, so missing
and empty values are tolerated and get defaults. A value of the wrong type is
an issue and is read as its default.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import fields
from datetime import time
from typing import Any

from .config_model import (
    APPLIANCE_ACTION_KINDS,
    ActionConfig,
    ActionMode,
    Appliance,
    Charger,
    ChargerGroup,
    ChargingWindow,
    Condition,
    ConditionType,
    ConfigValidationError,
    GeneralConfig,
    Issue,
    IssueLocation,
    ItemSwitches,
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


def read_switches[T: ItemSwitches](
    data: Mapping[str, Any], switch_type: type[T], section: str
) -> dict[str, T]:
    """Read the switches of appliances or chargers by id from JSON-friendly data.

    Raises ConfigValidationError if a value has the wrong type.
    """
    reader = ConfigReader()
    switches = reader.switches(data, switch_type, section)
    if reader.issues:
        raise ConfigValidationError(reader.issues)
    return switches


_BOOLEAN_CONDITIONS = (ConditionType.ENTITY, ConditionType.TEMPLATE)
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
            charger_groups=tuple(
                self._charger_group(item)
                for item in self._list(
                    root.get("charger_groups"), IssueLocation("charger_groups")
                )
            ),
        )

    def switches[T: ItemSwitches](
        self, data: Any, switch_type: type[T], section: str
    ) -> dict[str, T]:
        """Return the switches in the data, by the id of the appliance or charger."""
        switches = {}
        defaults = switch_type()
        for item_id, item in self._mapping(data, IssueLocation(section), None).items():
            location = IssueLocation(section, str(item_id))
            values = self._mapping(item, location, None)
            switches[str(item_id)] = switch_type(
                **{
                    setting.name: self._bool(
                        values, setting.name, getattr(defaults, setting.name), location
                    )
                    for setting in fields(switch_type)
                }
            )
        return switches

    def _general(self, data: Any) -> GeneralConfig:
        location = IssueLocation("general")
        values = self._mapping(data, location, None)
        return GeneralConfig(
            **{
                setting.name: self._setting(
                    values, setting.name, setting.default, location
                )
                for setting in fields(GeneralConfig)
            }
        )

    def _setting(
        self,
        values: Mapping[str, Any],
        key: str,
        default: Any,
        location: IssueLocation,
    ) -> Any:
        """Read a setting as text, a whole number or a number, like its default."""
        if default is None:
            return self._text(values, key, location)
        if isinstance(default, int):
            return self._integer(values, key, default, location)
        return self._number(values, key, default, location)

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
        actions = self._mapping(values.get("actions"), location, "actions")
        return Variant(
            id=variant_id,
            label=self._text(values, "label", location) or "",
            condition=self._condition(values, "condition", location)
            or Condition(ConditionType.TEMPLATE, ""),
            actions={
                name: self._action(actions, name, location)
                for name in APPLIANCE_ACTION_KINDS
                if name in actions
            },
        )

    def _priority_entry(self, data: Any) -> PriorityEntry | None:
        location = IssueLocation("priority")
        values = self._mapping(data, location, None)
        entry_type = values.get("type")
        if entry_type == PriorityEntryType.CHARGER_GROUP:
            group_id = self._text(values, "group_id", location)
            if group_id is None:
                self.issues.append(location.issue("invalid_type"))
                return None
            return PriorityEntry.for_charger_group(group_id)
        appliance_id = self._text(values, "appliance_id", location)
        if entry_type != PriorityEntryType.APPLIANCE or appliance_id is None:
            self.issues.append(location.issue("invalid_type"))
            return None
        return PriorityEntry.for_appliance(
            appliance_id, self._text(values, "variant_id", location)
        )

    def _charger_group(self, data: Any) -> ChargerGroup:
        values = self._mapping(data, IssueLocation("charger_groups"), None)
        group_id = self._id(values, IssueLocation("charger_groups"))
        location = IssueLocation("charger_groups", group_id)
        defaults = ChargerGroup(id=group_id)
        return ChargerGroup(
            id=group_id,
            name=self._text(values, "name", location) or "",
            one_at_a_time=self._bool(
                values, "one_at_a_time", defaults.one_at_a_time, location
            ),
            chargers=tuple(
                self._charger(item)
                for item in self._list(values.get("chargers"), location, "chargers")
            ),
        )

    def _charger(self, data: Any) -> Charger:
        values = self._mapping(data, IssueLocation("chargers"), None)
        charger_id = self._id(values, IssueLocation("chargers"))
        location = IssueLocation("chargers", charger_id)
        defaults = Charger(id=charger_id)
        return Charger(
            id=charger_id,
            device_id=self._text(values, "device_id", location),
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
            power_reserve_w=self._integer(
                values, "power_reserve_w", defaults.power_reserve_w, location
            ),
            car_connected=self._condition(values, "car_connected", location),
            actively_charging=self._condition(
                values, "actively_charging", location, power_sensor_allowed=True
            ),
            charging_window=self._charging_window(values, location),
            finish_after_window=self._bool(
                values, "finish_after_window", defaults.finish_after_window, location
            ),
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
            domain_action = action.get("domain_action")
            data = action.get("data", {})
            if (
                action.get("mode") == ActionMode.DOMAIN
                and isinstance(domain_action, str)
                and isinstance(data, Mapping)
            ):
                return ActionConfig(
                    ActionMode.DOMAIN, domain_action=domain_action, data=dict(data)
                )
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
        self,
        values: Mapping[str, Any],
        key: str,
        location: IssueLocation,
        *,
        power_sensor_allowed: bool = False,
    ) -> Condition | None:
        condition = values.get(key)
        if condition is None:
            return None
        if not isinstance(condition, Mapping):
            self.issues.append(location.issue("invalid_type", key))
            return None
        condition_type = condition.get("type")
        value = condition.get("value", "")
        allowed = tuple(ConditionType) if power_sensor_allowed else _BOOLEAN_CONDITIONS
        if condition_type not in allowed or not isinstance(value, str):
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
