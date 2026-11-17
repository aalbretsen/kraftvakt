"""Tests for whether the configuration is complete enough to start."""

import pytest

from custom_components.kraftvakt.config_model import (
    Issue,
    KraftvaktConfig,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
)
from custom_components.kraftvakt.config_validation import (
    missing_items,
)
from tests.config_examples import full_config_data


def _missing(data: dict) -> list[Issue]:
    return missing_items(read_config(data))


def test_full_config_is_complete() -> None:
    assert _missing(full_config_data()) == []


def test_default_config_misses_power_sensor() -> None:
    assert missing_items(KraftvaktConfig()) == [Issue("missing_power_sensor", "general", None, "power_sensor")]


def test_appliance_needs_entity_and_both_actions() -> None:
    data = full_config_data()
    data["appliances"].append({"id": "a3", "turn_off": {"mode": "custom"}})

    assert _missing(data) == [
        Issue("missing_entity", "appliances", "a3", "entity_id"),
        Issue("missing_action", "appliances", "a3", "turn_on"),
        Issue("missing_action", "appliances", "a3", "turn_off"),
    ]


def test_charger_needs_device_entity_actions_and_conditions() -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"].append({"id": "c2", "activate": {"mode": "default"}, "set_current": {"mode": "custom"}})

    assert _missing(data) == [
        Issue("missing_device", "chargers", "c2", "device_id"),
        Issue("missing_entity", "chargers", "c2", "entity_id"),
        Issue("missing_action", "chargers", "c2", "deactivate"),
        Issue("missing_action", "chargers", "c2", "set_current"),
        Issue("missing_car_connected", "chargers", "c2", "car_connected"),
        Issue("missing_charging_power", "chargers", "c2", "charging_power"),
    ]


def test_empty_charger_conditions_are_missing() -> None:
    data = full_config_data()
    charger = data["charger_groups"][0]["chargers"][0]
    charger["charging_power"] = {"type": "power_sensor", "value": ""}
    charger["car_connected"] = {"type": "template", "value": " "}

    assert _missing(data) == [
        Issue("missing_car_connected", "chargers", "c1", "car_connected"),
        Issue("missing_charging_power", "chargers", "c1", "charging_power"),
    ]


@pytest.mark.parametrize("one_at_a_time", [False, True])
def test_every_charger_needs_a_charging_power(one_at_a_time: bool) -> None:
    data = full_config_data()
    data["charger_groups"][0]["one_at_a_time"] = one_at_a_time
    data["charger_groups"][0]["chargers"][0]["charging_power"] = None

    assert _missing(data) == [Issue("missing_charging_power", "chargers", "c1", "charging_power")]


def test_charging_on_off_is_optional() -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"][0]["actively_charging"] = None

    assert _missing(data) == []


@pytest.mark.parametrize("flag", [None, {"type": "template", "value": " "}])
def test_deactivate_on_fault_needs_a_fault_flag(flag: dict[str, str] | None) -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"][0]["fault_flag"] = flag

    assert _missing(data) == [Issue("missing_fault_flag", "chargers", "c1", "fault_flag")]


def test_fault_flag_is_not_needed_while_deactivate_on_fault_is_off() -> None:
    data = full_config_data()
    charger = data["charger_groups"][0]["chargers"][0]
    charger["deactivate_on_fault"] = False
    charger["fault_flag"] = {"type": "entity", "value": ""}

    assert _missing(data) == []


def test_actions_to_activate_and_deactivate_are_not_needed_for_a_charger_switched_by_its_current() -> None:
    data = full_config_data()
    charger = data["charger_groups"][0]["chargers"][0]
    charger["switched_by_current"] = True
    charger["activate"] = None
    charger["deactivate"] = {"mode": "custom", "steps": []}

    assert _missing(data) == []


def test_charging_current_entity_must_be_chosen() -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"][0]["set_current"] = {"mode": "entity"}

    assert _missing(data) == [Issue("missing_action", "chargers", "c1", "set_current")]


def test_chargers_of_every_group_count() -> None:
    data = full_config_data()
    data["charger_groups"].append(
        {
            "id": "g2",
            "name": "Cabin",
            "one_at_a_time": False,
            "chargers": [{"id": "c2"}],
        }
    )

    assert _missing(data) == [
        Issue("missing_device", "chargers", "c2", "device_id"),
        Issue("missing_entity", "chargers", "c2", "entity_id"),
        Issue("missing_action", "chargers", "c2", "activate"),
        Issue("missing_action", "chargers", "c2", "deactivate"),
        Issue("missing_action", "chargers", "c2", "set_current"),
        Issue("missing_car_connected", "chargers", "c2", "car_connected"),
        Issue("missing_charging_power", "chargers", "c2", "charging_power"),
    ]


def test_optional_settings_are_not_required() -> None:
    data = full_config_data()
    data["appliances"][1]["power_reserve_w"] = None
    charger = data["charger_groups"][0]["chargers"][0]
    charger["cloud_controlled"] = False
    charger["charging_window"] = None
    del charger["min_current_a"]
    del charger["max_current_a"]
    del charger["min_current_power_w"]

    assert _missing(data) == []


def test_car_connected_is_required_for_every_charger() -> None:
    """Also with several chargers at a time, without cloud control and without a charging window."""
    data = full_config_data()
    data["charger_groups"][0]["one_at_a_time"] = False
    charger = data["charger_groups"][0]["chargers"][0]
    charger["car_connected"] = None
    charger["cloud_controlled"] = False
    charger["charging_window"] = None

    assert _missing(data) == [Issue("missing_car_connected", "chargers", "c1", "car_connected")]


def test_domain_action_needs_every_value_chosen() -> None:
    data = full_config_data()
    data["appliances"][0]["turn_on"] = {
        "mode": "domain",
        "domain_action": "climate_hvac_mode",
        "data": {"hvac_mode": None},
    }

    assert _missing(data) == [Issue("missing_action", "appliances", data["appliances"][0]["id"], "turn_on")]


def test_variant_needs_only_the_actions_it_overrides() -> None:
    data = full_config_data()
    data["appliances"][0]["variants"][0]["actions"] = {"turn_on": {"mode": "default"}}

    assert _missing(data) == []
    data["appliances"][0]["variants"][0]["actions"] = {"turn_off": None}

    assert _missing(data) == [Issue("missing_action", "appliances", "a1", "variants.v1.turn_off")]


def test_variant_needs_a_condition() -> None:
    data = full_config_data()
    data["appliances"][0]["variants"][0]["condition"]["value"] = " "

    assert _missing(data) == [Issue("missing_condition", "appliances", "a1", "variants.v1.condition")]
