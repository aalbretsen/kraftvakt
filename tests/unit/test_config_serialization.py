"""Tests for reading and writing the configuration as JSON-friendly data."""

from datetime import time
from typing import Any

import pytest

from custom_components.kraftvakt.config_model import (
    ActionConfig,
    ActionMode,
    ApplianceSwitches,
    ChargerSwitches,
    ChargingWindow,
    Condition,
    ConditionType,
    ConfigValidationError,
    Issue,
    KraftvaktConfig,
    PriorityEntry,
    switches_to_dict,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
    read_switches,
)
from tests.config_examples import full_config_data


def test_full_config_round_trips() -> None:
    data = full_config_data()

    assert read_config(data).to_dict() == data


def test_full_config_is_read_into_model() -> None:
    config = read_config(full_config_data())

    appliance = config.appliances[0]
    assert appliance.turn_on == ActionConfig(ActionMode.DEFAULT)
    assert appliance.turn_off is not None
    assert appliance.turn_off.mode is ActionMode.CUSTOM
    assert appliance.variants[0].condition == Condition(
        ConditionType.TEMPLATE, "{{ 5 <= now().hour < 8 }}"
    )
    assert config.priority[1] == PriorityEntry.ev_charging()
    charger = config.charging.chargers[0]
    assert charger.charging_window == ChargingWindow(time(22, 0), time(6, 0))
    assert charger.car_connected == Condition(
        ConditionType.ENTITY, "binary_sensor.garage_charger_car"
    )


def test_empty_data_gives_default_config() -> None:
    assert read_config({}) == KraftvaktConfig()


def test_default_config_round_trips() -> None:
    data = KraftvaktConfig().to_dict()

    assert read_config(data).to_dict() == data


def test_missing_settings_get_defaults() -> None:
    config = read_config(
        {"appliances": [{"id": "a1"}], "charging": {"chargers": [{"id": "c1"}]}}
    )

    appliance = config.appliances[0]
    assert appliance.entity_id is None
    assert appliance.turn_on is None
    assert appliance.power_reserve_w is None
    charger = config.charging.chargers[0]
    assert (charger.min_current_a, charger.max_current_a) == (6, 16)
    assert charger.power_reserve_w == 4000


def test_empty_strings_count_as_not_set() -> None:
    config = read_config(
        {"general": {"power_sensor": ""}, "appliances": [{"id": "a1", "entity_id": ""}]}
    )

    assert config.general.power_sensor is None
    assert config.appliances[0].entity_id is None


def test_missing_ids_are_generated() -> None:
    config = read_config(
        {
            "appliances": [
                {"variants": [{"label": "x", "condition": {"type": "template"}}]},
                {},
            ]
        }
    )

    first, second = config.appliances
    assert first.id
    assert second.id
    assert first.id != second.id
    assert first.variants[0].id


def test_custom_action_keeps_editor_normalization() -> None:
    steps = [{"action": "switch.turn_on", "target": {}, "data": {}, "metadata": {}}]
    config = read_config(
        {"appliances": [{"id": "a1", "turn_on": {"mode": "custom", "action": steps}}]}
    )

    assert config.to_dict()["appliances"][0]["turn_on"] == {
        "mode": "custom",
        "action": steps,
    }


def test_single_custom_action_step_becomes_list() -> None:
    step = {"action": "switch.turn_on"}
    config = read_config(
        {"appliances": [{"id": "a1", "turn_on": {"mode": "custom", "action": step}}]}
    )

    assert config.appliances[0].turn_on == ActionConfig(ActionMode.CUSTOM, (step,))


def test_custom_action_without_steps_is_empty() -> None:
    config = read_config({"appliances": [{"id": "a1", "turn_on": {"mode": "custom"}}]})

    assert config.appliances[0].turn_on == ActionConfig(ActionMode.CUSTOM)


def test_time_with_seconds_is_read() -> None:
    config = read_config(
        {
            "charging": {
                "chargers": [
                    {
                        "id": "c1",
                        "charging_window": {"start": "22:00:00", "end": "6:30:15"},
                    }
                ]
            }
        }
    )

    window = config.charging.chargers[0].charging_window
    assert window == ChargingWindow(time(22, 0), time(6, 30, 15))
    assert window.to_dict() == {"start": "22:00", "end": "06:30:15"}


def test_whole_number_floats_are_read_as_integers() -> None:
    config = read_config({"general": {"regulation_window_s": 60.0}})

    assert config.general.regulation_window_s == 60
    assert isinstance(config.general.regulation_window_s, int)


def _issues(data: dict[str, Any]) -> list[Issue]:
    with pytest.raises(ConfigValidationError) as error:
        read_config(data)
    return error.value.issues


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"general": []}, Issue("invalid_type", "general")),
        (
            {"general": {"power_limit_w": "10"}},
            Issue("invalid_type", "general", None, "power_limit_w"),
        ),
        (
            {"general": {"power_limit_w": True}},
            Issue("invalid_type", "general", None, "power_limit_w"),
        ),
        (
            {"general": {"regulation_window_s": 60.5}},
            Issue("not_integer", "general", None, "regulation_window_s"),
        ),
        (
            {"general": {"power_sensor": 5}},
            Issue("invalid_type", "general", None, "power_sensor"),
        ),
        ({"appliances": {}}, Issue("invalid_type", "appliances")),
        ({"appliances": ["a1"]}, Issue("invalid_type", "appliances")),
        (
            {"appliances": [{"id": "a1", "turn_on": {"mode": "magic"}}]},
            Issue("invalid_type", "appliances", "a1", "turn_on"),
        ),
        (
            {"appliances": [{"id": "a1", "turn_on": "switch.turn_on"}]},
            Issue("invalid_type", "appliances", "a1", "turn_on"),
        ),
        (
            {
                "appliances": [
                    {"id": "a1", "turn_on": {"mode": "custom", "action": "x"}}
                ]
            },
            Issue("invalid_type", "appliances", "a1", "turn_on"),
        ),
        (
            {
                "appliances": [
                    {"id": "a1", "turn_on": {"mode": "custom", "action": ["x"]}}
                ]
            },
            Issue("invalid_type", "appliances", "a1", "turn_on"),
        ),
        (
            {"appliances": [{"id": "a1", "variants": [{"id": "v1", "label": "x"}]}]},
            Issue("required", "appliances", "a1", "variants.v1.condition"),
        ),
        (
            {
                "appliances": [
                    {
                        "id": "a1",
                        "variants": [
                            {"id": "v1", "condition": {"type": "state", "value": "x"}}
                        ],
                    }
                ]
            },
            Issue("invalid_type", "appliances", "a1", "variants.v1.condition"),
        ),
        (
            {"charging": {"chargers": [{"id": "c1", "car_connected": "sensor.x"}]}},
            Issue("invalid_type", "chargers", "c1", "car_connected"),
        ),
        ({"priority": [{"type": "appliance"}]}, Issue("invalid_type", "priority")),
        ({"priority": [{"type": "other"}]}, Issue("invalid_type", "priority")),
        (
            {"charging": {"enabled": "yes"}},
            Issue("invalid_type", "charging", None, "enabled"),
        ),
        (
            {"charging": {"chargers": [{"id": "c1", "min_current_a": 6.5}]}},
            Issue("not_integer", "chargers", "c1", "min_current_a"),
        ),
        (
            {
                "charging": {
                    "chargers": [
                        {"id": "c1", "car_connected": {"type": "entity", "value": 1}}
                    ]
                }
            },
            Issue("invalid_type", "chargers", "c1", "car_connected"),
        ),
        (
            {
                "charging": {
                    "chargers": [
                        {
                            "id": "c1",
                            "car_connected": {"type": "power_sensor", "value": "x"},
                        }
                    ]
                }
            },
            Issue("invalid_type", "chargers", "c1", "car_connected"),
        ),
        (
            {
                "charging": {
                    "chargers": [{"id": "c1", "charging_window": {"start": "22:00"}}]
                }
            },
            Issue("invalid_time", "chargers", "c1", "charging_window"),
        ),
        (
            {
                "charging": {
                    "chargers": [
                        {
                            "id": "c1",
                            "charging_window": {"start": "24:00", "end": "06:00"},
                        }
                    ]
                }
            },
            Issue("invalid_time", "chargers", "c1", "charging_window"),
        ),
        (
            {
                "charging": {
                    "chargers": [
                        {
                            "id": "c1",
                            "charging_window": {"start": "kl 22", "end": "06:00"},
                        }
                    ]
                }
            },
            Issue("invalid_time", "chargers", "c1", "charging_window"),
        ),
    ],
)
def test_wrong_types_are_rejected(data: dict[str, Any], expected: Issue) -> None:
    assert _issues(data) == [expected]


def test_all_type_errors_are_reported_together() -> None:
    issues = _issues({"general": {"power_limit_w": "x", "wait_at_limit_s": "y"}})

    assert {issue.field for issue in issues} == {"power_limit_w", "wait_at_limit_s"}


def test_charger_switches_round_trip() -> None:
    data = {
        "c1": {"excluded": True, "window_override": False},
        "c2": {"excluded": False, "window_override": True},
    }

    switches = read_switches(data, ChargerSwitches, "chargers")

    assert switches["c1"] == ChargerSwitches(excluded=True)
    assert switches_to_dict(switches) == data


def test_appliance_switches_round_trip() -> None:
    data = {"a1": {"excluded": True}, "a2": {"excluded": False}}

    switches = read_switches(data, ApplianceSwitches, "appliances")

    assert switches["a1"] == ApplianceSwitches(excluded=True)
    assert switches_to_dict(switches) == data


def test_switches_get_defaults() -> None:
    assert read_switches({"c1": {}}, ChargerSwitches, "chargers") == {
        "c1": ChargerSwitches()
    }


def test_switches_with_wrong_type_are_rejected() -> None:
    with pytest.raises(ConfigValidationError) as error:
        read_switches({"a1": {"excluded": "on"}}, ApplianceSwitches, "appliances")

    assert error.value.issues == [Issue("invalid_type", "appliances", "a1", "excluded")]


def test_domain_action_round_trips() -> None:
    action = {
        "mode": "domain",
        "domain_action": "climate_hvac_mode_and_temperature",
        "data": {"hvac_mode": "heat", "temperature": None},
    }
    config = read_config({"appliances": [{"id": "a1", "turn_on": action}]})

    assert config.appliances[0].turn_on == ActionConfig(
        ActionMode.DOMAIN,
        domain_action="climate_hvac_mode_and_temperature",
        data={"hvac_mode": "heat", "temperature": None},
    )
    assert config.to_dict()["appliances"][0]["turn_on"] == action


@pytest.mark.parametrize(
    "action",
    [
        {"mode": "domain", "data": {}},
        {"mode": "domain", "domain_action": "climate_hvac_mode", "data": []},
    ],
)
def test_malformed_domain_action_is_a_type_error(action: dict[str, Any]) -> None:
    with pytest.raises(ConfigValidationError) as error:
        read_config({"appliances": [{"id": "a1", "turn_on": action}]})

    assert error.value.issues == [Issue("invalid_type", "appliances", "a1", "turn_on")]
