"""Tests for the configuration model: defaults, limits and serialization."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.config_model import (
    POWER_LIMIT_W,
    REGULATION_WINDOW_S,
    Charger,
    ChargerGroup,
    ChargerSwitches,
    GeneralConfig,
    Issue,
    KraftvaktConfig,
    Range,
    regulation_window_options,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
)


def test_stored_config_without_turn_on_margin_gets_the_default() -> None:
    """Configurations saved before the setting existed."""
    config = read_config({"general": {"power_limit_w": 8000}})

    assert config.general.turn_on_margin_w == 100


def test_defaults_follow_requirements() -> None:
    config = KraftvaktConfig()

    assert config.general.power_sensor is None
    assert config.general.power_limit_w == 10_000
    assert config.general.turn_on_margin_w == 100
    assert config.general.regulation_window_updates is None
    assert config.general.power_sensor_interval_s is None
    assert config.general.regulation_window_length is None
    assert config.general.regulation_interval == 1
    assert config.general.wait_at_limit_s == 300
    assert config.general.penalty_threshold_w == 100
    assert config.general.appliance_repeat_increment_factor == 0.5
    assert config.general.appliance_repeat_increments == 4
    assert config.general.command_repeat_interval_min == 30
    assert config.appliances == ()
    assert config.priority == ()
    assert config.charger_groups == ()


def test_charger_group_defaults() -> None:
    group = ChargerGroup(id="g1")

    assert group.name == ""
    assert group.one_at_a_time is True
    assert group.chargers == ()


def test_charger_defaults() -> None:
    charger = Charger(id="c1")

    assert charger.min_current_a == 6
    assert charger.max_current_a == 16
    assert charger.min_current_power_w == 4157
    assert charger.car_connected is None
    assert charger.charging_window is None


def test_charger_switches_default_off() -> None:
    assert ChargerSwitches() == ChargerSwitches(excluded=False, window_override=False)


@pytest.mark.parametrize(
    ("value_range", "value", "expected"),
    [
        (POWER_LIMIT_W, 1000, True),
        (POWER_LIMIT_W, 50_000, True),
        (POWER_LIMIT_W, 999, False),
        (POWER_LIMIT_W, 50_001, False),
        (REGULATION_WINDOW_S, 9, False),
        (REGULATION_WINDOW_S, 120, True),
        (REGULATION_WINDOW_S, 121, False),
        (Range(0, None, 0.01), 1000, True),
        (Range(0, None, 0.01), -0.01, False),
    ],
)
def test_range_contains(value_range: Range, value: float, expected: bool) -> None:
    assert value_range.contains(value) is expected


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


@pytest.mark.parametrize(
    ("interval_s", "expected"),
    [
        (10, list(range(1, 13))),
        (2, list(range(5, 61, 5))),
        (2.5, list(range(4, 49, 4))),
        (3, list(range(4, 41, 4))),
        (15, list(range(1, 9))),
        (130, []),
    ],
)
def test_regulation_window_options_are_multiples_of_the_fewest_updates_that_last_10_seconds(interval_s: float, expected: list[int]) -> None:
    """At most twelve choices, and no window longer than 120 seconds."""
    assert regulation_window_options(interval_s) == expected


def test_regulation_window_length_is_the_updates_at_the_interval() -> None:
    assert GeneralConfig(regulation_window_updates=5, power_sensor_interval_s=2.5).regulation_window_length == timedelta(seconds=12.5)
