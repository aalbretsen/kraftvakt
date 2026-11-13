"""Tests for whether the configuration is complete enough to start."""

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
    assert missing_items(KraftvaktConfig()) == [
        Issue("missing_power_sensor", "general", None, "power_sensor")
    ]


def test_appliance_needs_entity_and_both_actions() -> None:
    data = full_config_data()
    data["appliances"].append({"id": "a3", "turn_off": {"mode": "custom"}})

    assert _missing(data) == [
        Issue("missing_entity", "appliances", "a3", "entity_id"),
        Issue("missing_action", "appliances", "a3", "turn_on"),
        Issue("missing_action", "appliances", "a3", "turn_off"),
    ]


def test_charger_needs_device_entity_actions_and_actively_charging() -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"].append(
        {"id": "c2", "activate": {"mode": "default"}, "set_current": {"mode": "custom"}}
    )

    assert _missing(data) == [
        Issue("missing_device", "chargers", "c2", "device_id"),
        Issue("missing_entity", "chargers", "c2", "entity_id"),
        Issue("missing_action", "chargers", "c2", "deactivate"),
        Issue("missing_action", "chargers", "c2", "set_current"),
        Issue("missing_actively_charging", "chargers", "c2", "actively_charging"),
    ]


def test_empty_charger_conditions_are_missing() -> None:
    data = full_config_data()
    data["charger_groups"][0]["one_at_a_time"] = True
    charger = data["charger_groups"][0]["chargers"][0]
    charger["actively_charging"] = {"type": "power_sensor", "value": ""}
    charger["car_connected"] = {"type": "template", "value": " "}

    assert _missing(data) == [
        Issue("missing_actively_charging", "chargers", "c1", "actively_charging"),
        Issue("missing_car_connected", "chargers", "c1", "car_connected"),
    ]


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
        Issue("missing_actively_charging", "chargers", "c2", "actively_charging"),
    ]


def test_optional_settings_are_not_required() -> None:
    data = full_config_data()
    data["appliances"][1]["power_reserve_w"] = None
    charger = data["charger_groups"][0]["chargers"][0]
    charger["car_connected"] = None
    charger["charging_window"] = None
    del charger["min_current_a"]
    del charger["max_current_a"]
    del charger["power_reserve_w"]

    assert _missing(data) == []


def test_car_connected_is_required_with_one_charger_at_a_time() -> None:
    """Otherwise chargers without a car take turns."""
    data = full_config_data()
    data["charger_groups"][0]["one_at_a_time"] = True
    data["charger_groups"][0]["chargers"][0]["car_connected"] = None

    assert _missing(data) == [
        Issue("missing_car_connected", "chargers", "c1", "car_connected")
    ]


def test_car_connected_is_required_when_the_override_ends_on_disconnect() -> None:
    """Only with a charging window, where the override has an effect."""
    data = full_config_data()
    charger = data["charger_groups"][0]["chargers"][0]
    charger["car_connected"] = None
    charger["override_ends"] = "car_disconnected"

    assert _missing(data) == [
        Issue("missing_car_connected", "chargers", "c1", "car_connected")
    ]
    charger["charging_window"] = None
    assert _missing(data) == []
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "charging_stopped"
    assert _missing(data) == []


def test_domain_action_needs_every_value_chosen() -> None:
    data = full_config_data()
    data["appliances"][0]["turn_on"] = {
        "mode": "domain",
        "domain_action": "climate_hvac_mode",
        "data": {"hvac_mode": None},
    }

    assert _missing(data) == [
        Issue("missing_action", "appliances", data["appliances"][0]["id"], "turn_on")
    ]


def test_variant_needs_only_the_actions_it_overrides() -> None:
    data = full_config_data()
    data["appliances"][0]["variants"][0]["actions"] = {"turn_on": {"mode": "default"}}

    assert _missing(data) == []
    data["appliances"][0]["variants"][0]["actions"] = {"turn_off": None}

    assert _missing(data) == [
        Issue("missing_action", "appliances", "a1", "variants.v1.turn_off")
    ]


def test_variant_needs_a_condition() -> None:
    data = full_config_data()
    data["appliances"][0]["variants"][0]["condition"]["value"] = " "

    assert _missing(data) == [
        Issue("missing_condition", "appliances", "a1", "variants.v1.condition")
    ]
