"""Validation and completeness of the configuration."""

from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import replace
from typing import Any

import voluptuous as vol
from homeassistant.core import valid_entity_id
from homeassistant.helpers import config_validation as cv

from .config_model import (
    SETTING_RANGES,
    ActionConfig,
    Appliance,
    Charger,
    ChargerGroup,
    Condition,
    ConditionType,
    ConfigValidationError,
    GeneralConfig,
    Issue,
    IssueLocation,
    KraftvaktConfig,
    PriorityEntry,
    PriorityEntryType,
    Range,
    Variant,
)
from .config_reader import ConfigReader


def parse_config(data: Mapping[str, Any]) -> KraftvaktConfig:
    """Read and validate a configuration from the panel.

    Raises ConfigValidationError with every issue found. A value of the wrong
    type is read as the default, so the other rules are still checked. Must be
    called from the event loop, since Home Assistant validates templates there.
    """
    reader = ConfigReader()
    config = _complete_priority(reader.config(data))
    unreadable = {(issue.section, issue.target, issue.field) for issue in reader.issues}
    issues = reader.issues + [
        issue
        for issue in validate_config(config) + action_and_template_issues(config)
        if (issue.section, issue.target, issue.field) not in unreadable
    ]
    if issues:
        raise ConfigValidationError(issues)
    return config


def validate_config(config: KraftvaktConfig) -> list[Issue]:
    """Return every rule the configuration breaks.

    The syntax of custom actions and templates is checked by
    `action_and_template_issues()`, since it needs the event loop.
    """
    return [
        *_general_issues(config.general),
        *(
            Issue("duplicate_id", "appliances", appliance_id)
            for appliance_id in _duplicate_ids(config.appliances)
        ),
        *(issue for item in config.appliances for issue in _appliance_issues(item)),
        *(
            Issue("duplicate_id", "charger_groups", group_id)
            for group_id in _duplicate_ids(config.charger_groups)
        ),
        *_charger_group_issues(config.charger_groups),
        *(
            Issue("duplicate_id", "chargers", charger_id)
            for charger_id in _duplicate_ids(config.chargers)
        ),
        *(issue for item in config.chargers for issue in _charger_issues(item)),
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

    When only one charger may charge at a time, each charger needs «car
    connected». Without it, chargers without a car would take turns being
    activated.
    """
    missing = []
    if config.general.power_sensor is None:
        missing.append(Issue("missing_power_sensor", "general", None, "power_sensor"))
    for appliance in config.appliances:
        missing += _missing_entity_and_actions("appliances", appliance)
        missing += [
            Issue(
                "missing_condition",
                "appliances",
                appliance.id,
                f"variants.{variant.id}.condition",
            )
            for variant in appliance.variants
            if not variant.condition.value.strip()
        ]
    for group in config.charger_groups:
        for charger in group.chargers:
            if charger.device_id is None:
                missing.append(
                    Issue("missing_device", "chargers", charger.id, "device_id")
                )
            missing += _missing_entity_and_actions("chargers", charger)
            if charger.actively_charging is None:
                missing.append(
                    Issue(
                        "missing_actively_charging",
                        "chargers",
                        charger.id,
                        "actively_charging",
                    )
                )
            if group.one_at_a_time and charger.car_connected is None:
                missing.append(
                    Issue(
                        "missing_car_connected", "chargers", charger.id, "car_connected"
                    )
                )
    return missing


def _general_issues(general: GeneralConfig) -> list[Issue]:
    location = IssueLocation("general")
    return [
        *_entity_format_issues(location, "power_sensor", general.power_sensor),
        *_ranges_issues(location, general),
    ]


def _appliance_issues(appliance: Appliance) -> list[Issue]:
    location = IssueLocation("appliances", appliance.id)
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
        if variant.condition.value.strip():
            issues += _condition_issues(
                variant_location, "condition", variant.condition
            )
    return issues


def _charger_group_issues(groups: Iterable[ChargerGroup]) -> list[Issue]:
    names = Counter(group.name.strip() for group in groups)
    issues = []
    for group in groups:
        location = IssueLocation("charger_groups", group.id)
        name = group.name.strip()
        if not name:
            issues.append(location.issue("empty_name", "name"))
        elif names[name] > 1:
            issues.append(location.issue("duplicate_name", "name"))
    return issues


def _charger_issues(charger: Charger) -> list[Issue]:
    location = IssueLocation("chargers", charger.id)
    issues = [
        *_entity_format_issues(location, "entity_id", charger.entity_id),
        *_entity_format_issues(
            location,
            "set_current",
            charger.set_current.entity_id if charger.set_current else None,
        ),
        *_ranges_issues(location, charger),
    ]
    if charger.min_current_a > charger.max_current_a:
        issues.append(location.issue("min_current_above_max", "min_current_a"))
    for field_name in ("car_connected", "actively_charging"):
        condition = getattr(charger, field_name)
        if condition is not None:
            issues += _condition_issues(location, field_name, condition)
    window = charger.charging_window
    if window is not None:
        if window.start.second or window.end.second:
            issues.append(location.issue("invalid_resolution", "charging_window"))
        if window.start == window.end:
            issues.append(location.issue("window_start_equals_end", "charging_window"))
    return issues


def _condition_issues(
    location: IssueLocation, field_name: str, condition: Condition
) -> list[Issue]:
    if not condition.value.strip():
        return [location.issue("required", field_name)]
    if condition.type is ConditionType.TEMPLATE:
        return []
    return _entity_format_issues(location, field_name, condition.value)


def _entity_format_issues(
    location: IssueLocation, field_name: str, entity_id: str | None
) -> list[Issue]:
    if entity_id is None or valid_entity_id(entity_id):
        return []
    return [location.issue("invalid_entity_id", field_name)]


def _ranges_issues(
    location: IssueLocation, item: GeneralConfig | Appliance | Charger
) -> list[Issue]:
    return [
        issue
        for field_name, value_range in SETTING_RANGES[location.section].items()
        if (value := getattr(item, field_name)) is not None
        for issue in _range_issues(location, field_name, value, value_range)
    ]


def _range_issues(
    location: IssueLocation, field_name: str, value: float, value_range: Range
) -> list[Issue]:
    if not value_range.contains(value):
        return [location.issue("out_of_range", field_name)]
    if not value_range.matches_resolution(value):
        return [location.issue("invalid_resolution", field_name)]
    return []


def _duplicate_ids(
    items: Iterable[Appliance | Variant | Charger | ChargerGroup],
) -> list[str]:
    counts = Counter(item.id for item in items)
    return [item_id for item_id, count in counts.items() if count > 1]


def _unique_entity_issues(config: KraftvaktConfig) -> list[Issue]:
    owners = [
        *(("appliances", item.id, item.entity_id) for item in config.appliances),
        *(("chargers", item.id, item.entity_id) for item in config.chargers),
    ]
    counts = Counter(entity_id for _, _, entity_id in owners if entity_id)
    return [
        Issue("duplicate_entity", section, target, "entity_id")
        for section, target, entity_id in owners
        if entity_id and counts[entity_id] > 1
    ]


def _priority_issues(config: KraftvaktConfig) -> list[Issue]:
    expected = _expected_priority(config)
    counts = Counter(config.priority)
    issues = []
    for entry, count in counts.items():
        location = _priority_location(entry)
        if entry not in expected:
            issues.append(
                location.issue("unknown_priority_entry", _priority_field(entry))
            )
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
    expected += [
        PriorityEntry.for_charger_group(group.id) for group in config.charger_groups
    ]
    return expected


def _priority_location(entry: PriorityEntry) -> IssueLocation:
    if entry.type is PriorityEntryType.CHARGER_GROUP:
        return IssueLocation("priority", entry.group_id)
    return IssueLocation("priority", entry.appliance_id)


def _priority_field(entry: PriorityEntry) -> str | None:
    return None if entry.variant_id is None else f"variants.{entry.variant_id}"


def _custom_actions(
    config: KraftvaktConfig,
) -> Iterable[tuple[str, str, str, ActionConfig]]:
    for section, item in config.items():
        for action_field in item.action_fields():
            action = action_field.action
            if action is not None and action.steps:
                yield section, item.id, action_field.field, action


def _conditions(config: KraftvaktConfig) -> Iterable[tuple[str, str, str, Condition]]:
    for appliance in config.appliances:
        for variant in appliance.variants:
            yield (
                "appliances",
                appliance.id,
                f"variants.{variant.id}.condition",
                variant.condition,
            )
    for charger in config.chargers:
        for field_name in ("car_connected", "actively_charging"):
            condition = getattr(charger, field_name)
            if condition is not None:
                yield "chargers", charger.id, field_name, condition


def _missing_entity_and_actions(section: str, item: Appliance | Charger) -> list[Issue]:
    missing = []
    if item.entity_id is None:
        missing.append(Issue("missing_entity", section, item.id, "entity_id"))
    for action_field in item.action_fields():
        action = action_field.action
        if action is None or action.is_missing:
            missing.append(
                Issue("missing_action", section, item.id, action_field.field)
            )
    return missing
