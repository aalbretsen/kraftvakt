"""Tests for the configuration model: defaults, limits and serialization."""

import pytest

from custom_components.kraftvakt.config_model import (
    CHARGER_POWER_RESERVE_KW,
    POWER_LIMIT_KW,
    REGULATION_WINDOW_S,
    Charger,
    ChargerSwitches,
    Issue,
    KraftvaktConfig,
    Range,
)


def test_stored_config_without_turn_on_margin_gets_the_default() -> None:
    """Configurations saved before the setting existed."""
    config = KraftvaktConfig.from_dict({"general": {"power_limit_kw": 8.0}})

    assert config.general.turn_on_margin_kw == 0.1


def test_defaults_follow_requirements() -> None:
    config = KraftvaktConfig()

    assert config.general.power_sensor is None
    assert config.general.power_limit_kw == 10.0
    assert config.general.turn_on_margin_kw == 0.1
    assert config.general.regulation_window_s == 60
    assert config.general.regulation_interval == 1
    assert config.general.wait_at_limit_min == 5
    assert config.general.penalty_threshold_kw == 1.0
    assert config.appliances == ()
    assert config.priority == ()
    assert config.charging.enabled is False
    assert config.charging.one_at_a_time is True
    assert config.charging.chargers == ()


def test_charger_defaults() -> None:
    charger = Charger(id="c1")

    assert charger.min_current_a == 6
    assert charger.max_current_a == 16
    assert charger.power_reserve_kw == 4.0
    assert charger.car_connected is None
    assert charger.charging_window is None


def test_charger_switches_default_off() -> None:
    assert ChargerSwitches() == ChargerSwitches(excluded=False, window_override=False)


@pytest.mark.parametrize(
    ("value_range", "value", "expected"),
    [
        (POWER_LIMIT_KW, 1, True),
        (POWER_LIMIT_KW, 50, True),
        (POWER_LIMIT_KW, 0.99, False),
        (POWER_LIMIT_KW, 50.01, False),
        (REGULATION_WINDOW_S, 9, False),
        (REGULATION_WINDOW_S, 600, True),
        (Range(0, None, 0.01), 1000, True),
        (Range(0, None, 0.01), -0.01, False),
    ],
)
def test_range_contains(value_range: Range, value: float, expected: bool) -> None:
    assert value_range.contains(value) is expected


@pytest.mark.parametrize(
    ("value_range", "value", "expected"),
    [
        (POWER_LIMIT_KW, 10.1, True),
        (POWER_LIMIT_KW, 9.99, True),
        (POWER_LIMIT_KW, 10.005, False),
        (CHARGER_POWER_RESERVE_KW, 3.3, True),
        (REGULATION_WINDOW_S, 60, True),
        (REGULATION_WINDOW_S, 60.5, False),
    ],
)
def test_range_matches_step(value_range: Range, value: float, expected: bool) -> None:
    assert value_range.matches_step(value) is expected


def test_issue_to_dict_leaves_out_empty_keys() -> None:
    assert Issue("missing_power_sensor", "general").to_dict() == {
        "code": "missing_power_sensor",
        "section": "general",
    }
    assert Issue("missing_action", "appliances", "a1", "turn_on").to_dict() == {
        "code": "missing_action",
        "section": "appliances",
        "target": "a1",
        "field": "turn_on",
    }
