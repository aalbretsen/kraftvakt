"""Tests for whether the configuration is complete enough to start (REG-016)."""

from custom_components.kraftvakt.config_model import (
    Issue,
    KraftvaktConfig,
    missing_items,
)
from tests.config_examples import full_config_data


def _missing(data: dict) -> list[Issue]:
    return missing_items(KraftvaktConfig.from_dict(data))


def test_full_config_is_complete() -> None:
    assert _missing(full_config_data()) == []


def test_default_config_misses_power_sensor() -> None:
    assert missing_items(KraftvaktConfig()) == [
        Issue("missing_power_sensor", "general", None, "power_sensor")
    ]


def test_appliance_needs_entity_and_both_actions() -> None:
    data = full_config_data()
    data["appliances"].append(
        {"id": "a3", "turn_off": {"mode": "custom", "action": []}}
    )

    assert _missing(data) == [
        Issue("missing_entity", "appliances", "a3", "entity_id"),
        Issue("missing_action", "appliances", "a3", "turn_on"),
        Issue("missing_action", "appliances", "a3", "turn_off"),
    ]


def test_charger_needs_entity_actions_and_charge_power_sensor() -> None:
    data = full_config_data()
    data["charging"]["chargers"].append(
        {"id": "c2", "activate": {"mode": "default"}, "set_current": {"mode": "custom"}}
    )

    assert _missing(data) == [
        Issue("missing_entity", "chargers", "c2", "entity_id"),
        Issue("missing_action", "chargers", "c2", "deactivate"),
        Issue("missing_action", "chargers", "c2", "set_current"),
        Issue("missing_charge_power_sensor", "chargers", "c2", "charge_power_sensor"),
    ]


def test_chargers_do_not_count_while_charging_is_disabled() -> None:
    data = full_config_data()
    data["charging"]["enabled"] = False
    data["charging"]["chargers"].append({"id": "c2"})

    assert _missing(data) == []


def test_optional_settings_are_not_required() -> None:
    data = full_config_data()
    data["appliances"][1]["power_reserve_kw"] = None
    charger = data["charging"]["chargers"][0]
    charger["car_connected"] = None
    charger["charging_window"] = None
    del charger["min_current_a"]
    del charger["max_current_a"]
    del charger["power_reserve_kw"]

    assert _missing(data) == []


def test_car_connected_is_required_with_one_charger_at_a_time() -> None:
    """LAD-002, LAD-010, T25: otherwise chargers without a car take turns."""
    data = full_config_data()
    data["charging"]["one_at_a_time"] = True
    data["charging"]["chargers"][0]["car_connected"] = None

    assert _missing(data) == [
        Issue("missing_car_connected", "chargers", "c1", "car_connected")
    ]
