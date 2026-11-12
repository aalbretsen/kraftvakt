"""Tests for validation of the configuration."""

from collections.abc import Callable
from typing import Any

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.config_model import (
    ConfigValidationError,
    Issue,
    KraftvaktConfig,
    PriorityEntry,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
)
from custom_components.kraftvakt.config_validation import (
    parse_config,
    validate_config,
)
from tests.config_examples import full_config_data

type Mutation = Callable[[dict[str, Any]], None]


def _issues_after(mutate: Mutation) -> list[Issue]:
    data = full_config_data()
    mutate(data)
    return validate_config(read_config(data))


def _set(path: str, value: Any) -> Mutation:
    """Return a mutation that sets the value at a dotted path, e.g. appliances.0.id."""

    def mutate(data: dict[str, Any]) -> None:
        *parents, last = path.split(".")
        node: Any = data
        for key in parents:
            node = node[int(key)] if isinstance(node, list) else node[key]
        if isinstance(node, list):
            node[int(last)] = value
        else:
            node[last] = value

    return mutate


def test_full_config_is_valid() -> None:
    assert _issues_after(lambda data: None) == []


def test_default_config_is_valid() -> None:
    assert validate_config(KraftvaktConfig()) == []


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("power_limit_w", 1000, None),
        ("power_limit_w", 50_000, None),
        ("power_limit_w", 999, "out_of_range"),
        ("power_limit_w", 50_001, "out_of_range"),
        ("regulation_window_s", 10, None),
        ("regulation_window_s", 600, None),
        ("regulation_window_s", 9, "out_of_range"),
        ("regulation_window_s", 601, "out_of_range"),
        ("regulation_interval", 4, None),
        ("regulation_interval", 0, "out_of_range"),
        ("regulation_interval", 5, "out_of_range"),
        ("wait_at_limit_s", 0, None),
        ("wait_at_limit_s", 600, None),
        ("wait_at_limit_s", 601, "out_of_range"),
        ("turn_on_margin_w", 1, None),
        ("turn_on_margin_w", 1000, None),
        ("turn_on_margin_w", 0, "out_of_range"),
        ("turn_on_margin_w", 1001, "out_of_range"),
        ("wait_curve_steepness", 1.5, None),
        ("wait_curve_steepness", 9, None),
        ("wait_curve_steepness", 1, "out_of_range"),
        ("wait_curve_steepness", 9.5, "out_of_range"),
        ("wait_curve_steepness", 2.25, "invalid_resolution"),
        ("wait_curve_pivot", 50, None),
        ("wait_curve_pivot", 99, None),
        ("wait_curve_pivot", 49, "out_of_range"),
        ("wait_curve_pivot", 100, "out_of_range"),
        ("appliance_cycling_step_factor", 0.25, None),
        ("appliance_cycling_step_factor", 1, None),
        ("appliance_cycling_step_factor", 0, "out_of_range"),
        ("appliance_cycling_step_factor", 1.25, "out_of_range"),
        ("appliance_cycling_step_factor", 0.3, "invalid_resolution"),
        ("appliance_cycling_steps", 1, None),
        ("appliance_cycling_steps", 9, None),
        ("appliance_cycling_steps", 0, "out_of_range"),
        ("appliance_cycling_steps", 10, "out_of_range"),
        ("charger_cycling_step_factor", 0.75, None),
        ("charger_cycling_step_factor", 0.2, "out_of_range"),
        ("charger_cycling_steps", 9, None),
        ("charger_cycling_steps", 10, "out_of_range"),
        ("penalty_threshold_w", 0, None),
        ("penalty_threshold_w", 10_000, None),
        ("penalty_threshold_w", -1, "out_of_range"),
        ("power_sensor", "sensor.other", None),
        ("power_sensor", "not an entity", "invalid_entity_id"),
    ],
)
def test_general_ranges(field: str, value: Any, code: str | None) -> None:
    expected = [] if code is None else [Issue(code, "general", None, field)]

    assert _issues_after(_set(f"general.{field}", value)) == expected


@pytest.mark.parametrize(
    ("value", "code"),
    [(0, None), (100_000, None), (-1, "out_of_range")],
)
def test_appliance_power_reserve(value: float, code: str | None) -> None:
    expected = (
        [] if code is None else [Issue(code, "appliances", "a2", "power_reserve_w")]
    )

    assert _issues_after(_set("appliances.1.power_reserve_w", value)) == expected


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("power_reserve_w", 0, None),
        ("power_reserve_w", 5000, None),
        ("power_reserve_w", 5001, "out_of_range"),
        ("min_current_a", 1, None),
        ("min_current_a", 0, "out_of_range"),
        ("entity_id", "switch", "invalid_entity_id"),
        (
            "actively_charging",
            {"type": "power_sensor", "value": "Sensor.X"},
            "invalid_entity_id",
        ),
        ("actively_charging", {"type": "power_sensor", "value": ""}, "required"),
        ("set_current", {"mode": "entity", "entity_id": "number.x"}, None),
        ("set_current", {"mode": "entity", "entity_id": "Number"}, "invalid_entity_id"),
    ],
)
def test_charger_settings(field: str, value: Any, code: str | None) -> None:
    expected = [] if code is None else [Issue(code, "chargers", "c1", field)]

    assert _issues_after(_set(f"charging.chargers.0.{field}", value)) == expected


def test_min_current_may_equal_max() -> None:
    assert _issues_after(_set("charging.chargers.0.max_current_a", 6)) == []


def test_max_current_must_be_at_least_one() -> None:
    assert _issues_after(_set("charging.chargers.0.max_current_a", 0)) == [
        Issue("out_of_range", "chargers", "c1", "max_current_a"),
        Issue("min_current_above_max", "chargers", "c1", "min_current_a"),
    ]


def test_min_current_above_max_is_rejected() -> None:
    assert _issues_after(_set("charging.chargers.0.max_current_a", 5)) == [
        Issue("min_current_above_max", "chargers", "c1", "min_current_a")
    ]


def test_charging_window_start_must_differ_from_end() -> None:
    issues = _issues_after(
        _set("charging.chargers.0.charging_window", {"start": "22:00", "end": "22:00"})
    )

    assert issues == [
        Issue("window_start_equals_end", "chargers", "c1", "charging_window")
    ]


def test_charging_window_in_whole_minutes() -> None:
    issues = _issues_after(
        _set(
            "charging.chargers.0.charging_window",
            {"start": "22:00:30", "end": "06:00"},
        )
    )

    assert issues == [Issue("invalid_resolution", "chargers", "c1", "charging_window")]


def test_charging_window_across_midnight_is_valid() -> None:
    window = {"start": "23:30", "end": "00:15"}

    assert _issues_after(_set("charging.chargers.0.charging_window", window)) == []


@pytest.mark.parametrize(
    ("condition", "code"),
    [
        ({"type": "entity", "value": "binary_sensor.car"}, None),
        ({"type": "entity", "value": "car"}, "invalid_entity_id"),
        ({"type": "entity", "value": ""}, "required"),
        ({"type": "template", "value": "  "}, "required"),
        ({"type": "template", "value": "{{ true }}"}, None),
    ],
)
def test_car_connected_condition(condition: dict[str, str], code: str | None) -> None:
    expected = [] if code is None else [Issue(code, "chargers", "c1", "car_connected")]

    assert (
        _issues_after(_set("charging.chargers.0.car_connected", condition)) == expected
    )


def test_variant_condition_must_have_value() -> None:
    issues = _issues_after(
        _set("appliances.0.variants.0.condition", {"type": "template", "value": ""})
    )

    assert issues == [Issue("required", "appliances", "a1", "variants.v1.condition")]


def test_variant_label_must_not_be_empty() -> None:
    assert _issues_after(_set("appliances.0.variants.0.label", "   ")) == [
        Issue("empty_label", "appliances", "a1", "variants.v1.label")
    ]


def test_variant_labels_must_be_unique_per_appliance() -> None:
    def mutate(data: dict[str, Any]) -> None:
        variant = data["appliances"][0]["variants"][0]
        data["appliances"][0]["variants"].append(
            {**variant, "id": "v2", "label": "Morning "}
        )
        data["appliances"][1]["variants"].append({**variant, "id": "v3"})
        data["priority"] += [
            {"type": "appliance", "appliance_id": "a1", "variant_id": "v2"},
            {"type": "appliance", "appliance_id": "a2", "variant_id": "v3"},
        ]

    assert _issues_after(mutate) == [
        Issue("duplicate_label", "appliances", "a1", "variants.v1.label"),
        Issue("duplicate_label", "appliances", "a1", "variants.v2.label"),
    ]


def test_entity_is_unique_across_appliances_and_chargers() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["appliances"][1]["entity_id"] = "switch.water_heater"
        data["charging"]["chargers"][0]["entity_id"] = "switch.water_heater"

    assert _issues_after(mutate) == [
        Issue("duplicate_entity", "appliances", "a1", "entity_id"),
        Issue("duplicate_entity", "appliances", "a2", "entity_id"),
        Issue("duplicate_entity", "chargers", "c1", "entity_id"),
    ]


def test_entity_uniqueness_ignores_sensors_and_conditions() -> None:
    def mutate(data: dict[str, Any]) -> None:
        charger = data["charging"]["chargers"][0]
        charger["actively_charging"] = {
            "type": "power_sensor",
            "value": "sensor.han_power",
        }
        charger["car_connected"] = {"type": "entity", "value": "climate.bathroom"}

    assert _issues_after(mutate) == []


def test_unset_entities_are_not_duplicates() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["appliances"][0]["entity_id"] = None
        data["appliances"][1]["entity_id"] = None

    assert _issues_after(mutate) == []


def test_ids_must_be_unique() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["appliances"][1]["id"] = "a1"
        data["appliances"][0]["variants"].append(
            {**data["appliances"][0]["variants"][0], "label": "Evening"}
        )
        data["charging"]["chargers"].append(
            {**data["charging"]["chargers"][0], "entity_id": "switch.charger_2"}
        )
        data["priority"] = [
            entry for entry in data["priority"] if entry.get("appliance_id") != "a2"
        ]

    assert Issue("duplicate_id", "appliances", "a1") in _issues_after(mutate)
    assert Issue("duplicate_id", "appliances", "a1", "variants.v1") in _issues_after(
        mutate
    )
    assert Issue("duplicate_id", "chargers", "c1") in _issues_after(mutate)


def test_priority_entry_for_unknown_variant_is_rejected() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["appliances"][0]["variants"] = []

    assert _issues_after(mutate) == [
        Issue("unknown_priority_entry", "priority", "a1", "variants.v1")
    ]


def test_priority_entry_for_unknown_appliance_is_rejected() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["priority"].append({"type": "appliance", "appliance_id": "gone"})

    assert _issues_after(mutate) == [
        Issue("unknown_priority_entry", "priority", "gone")
    ]


def test_duplicate_priority_entry_is_rejected() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["priority"] += [{"type": "ev_charging"}, data["priority"][0]]

    assert _issues_after(mutate) == [
        Issue("duplicate_priority_entry", "priority", "a1", "variants.v1"),
        Issue("duplicate_priority_entry", "priority"),
    ]


def test_ev_charging_entry_only_when_charging_is_enabled() -> None:
    assert _issues_after(_set("charging.enabled", False)) == [
        Issue("ev_charging_disabled", "priority")
    ]


def test_missing_priority_entries_are_reported() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["priority"] = data["priority"][2:]

    assert _issues_after(mutate) == [
        Issue("missing_priority_entry", "priority", "a1", "variants.v1"),
        Issue("missing_priority_entry", "priority"),
    ]


def test_disabled_chargers_are_still_validated() -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["charging"]["enabled"] = False
        data["charging"]["chargers"][0]["max_current_a"] = 1
        data["priority"].remove({"type": "ev_charging"})

    assert _issues_after(mutate) == [
        Issue("min_current_above_max", "chargers", "c1", "min_current_a")
    ]


async def test_parse_config_accepts_full_config(hass: HomeAssistant) -> None:
    data = full_config_data()

    assert parse_config(data).to_dict() == data


async def test_parse_config_adds_missing_priority_entries_at_bottom(
    hass: HomeAssistant,
) -> None:
    data = full_config_data()
    data["appliances"][0]["variants"].append(
        {
            "id": "v2",
            "label": "Evening",
            "condition": {"type": "entity", "value": "input_boolean.evening"},
        }
    )
    data["priority"] = data["priority"][1:]

    config = parse_config(data)

    assert config.priority[-2:] == (
        PriorityEntry.for_appliance("a1", "v1"),
        PriorityEntry.for_appliance("a1", "v2"),
    )


async def test_parse_config_adds_ev_charging_when_enabled(hass: HomeAssistant) -> None:
    data = full_config_data()
    data["priority"].remove({"type": "ev_charging"})

    assert parse_config(data).priority[-1] == PriorityEntry.ev_charging()


async def test_parse_config_accepts_incomplete_config(hass: HomeAssistant) -> None:
    config = parse_config({"appliances": [{"id": "a1"}]})

    assert config.priority == (PriorityEntry.for_appliance("a1"),)


async def test_parse_config_rejects_invalid_config(hass: HomeAssistant) -> None:
    data = full_config_data()
    data["general"]["power_limit_w"] = 60_000

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [
        Issue("out_of_range", "general", None, "power_limit_w")
    ]
    assert str(error.value) == "out_of_range"


async def test_parse_config_rejects_wrong_types(hass: HomeAssistant) -> None:
    with pytest.raises(ConfigValidationError):
        parse_config({"general": {"power_limit_w": "ti"}})


async def test_wrong_type_does_not_hide_the_other_issues(hass: HomeAssistant) -> None:
    """A value of the wrong type does not hide the other issues."""
    data = full_config_data()
    data["general"]["regulation_window_s"] = 10.5
    data["general"]["power_limit_w"] = 500
    data["appliances"][1]["entity_id"] = data["appliances"][0]["entity_id"]

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert {(issue.code, issue.field) for issue in error.value.issues} == {
        ("not_integer", "regulation_window_s"),
        ("out_of_range", "power_limit_w"),
        ("duplicate_entity", "entity_id"),
    }


async def test_wrong_type_is_reported_once(hass: HomeAssistant) -> None:
    """The default used in its place is not checked again."""
    data = full_config_data()
    data["appliances"][0]["power_reserve_w"] = "mye"

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [
        Issue("invalid_type", "appliances", "a1", "power_reserve_w")
    ]


@pytest.mark.parametrize(
    ("field", "action"),
    [
        ("activate", {"mode": "entity", "entity_id": "number.x"}),
        ("set_current", {"mode": "entity", "entity_id": 7}),
    ],
)
async def test_only_the_charging_current_may_be_given_as_an_entity(
    hass: HomeAssistant, field: str, action: dict[str, Any]
) -> None:
    data = full_config_data()
    data["charging"]["chargers"][0][field] = action

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [Issue("invalid_type", "chargers", "c1", field)]


async def test_charging_current_entity_is_kept(hass: HomeAssistant) -> None:
    data = full_config_data()
    action = {"mode": "entity", "entity_id": "number.charger_current"}
    data["charging"]["chargers"][0]["set_current"] = action

    config = parse_config(data)

    assert config.charging.chargers[0].to_dict()["set_current"] == action


async def test_parse_config_rejects_invalid_template(hass: HomeAssistant) -> None:
    data = full_config_data()
    data["appliances"][0]["variants"][0]["condition"]["value"] = "{{ 5 <= }}"
    data["charging"]["chargers"][0]["car_connected"] = {
        "type": "template",
        "value": "{% if %}",
    }

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [
        Issue("invalid_template", "appliances", "a1", "variants.v1.condition"),
        Issue("invalid_template", "chargers", "c1", "car_connected"),
    ]


async def test_parse_config_rejects_invalid_action(hass: HomeAssistant) -> None:
    data = full_config_data()
    data["appliances"][0]["actions"]["main"]["turn_off"]["action"] = [
        {"no_such_key": True}
    ]
    data["appliances"][0]["actions"]["v1"]["turn_on"] = {
        "mode": "custom",
        "action": [{"delay": "lenge"}],
    }
    data["charging"]["chargers"][0]["set_current"]["action"] = [{"delay": "lenge"}]

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [
        Issue("invalid_action", "appliances", "a1", "turn_off"),
        Issue("invalid_action", "appliances", "a1", "variants.v1.turn_on"),
        Issue("invalid_action", "chargers", "c1", "set_current"),
    ]


async def test_parse_config_does_not_change_actions(hass: HomeAssistant) -> None:
    data = full_config_data()
    original = data["appliances"][0]["actions"]["main"]["turn_off"]["action"][0]

    config = parse_config(data)

    assert config.appliances[0].actions_for(None).turn_off.steps[0] == original
    assert original["target"] == {"entity_id": "{{ entity_id }}"}
