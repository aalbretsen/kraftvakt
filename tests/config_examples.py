"""Example configurations shared by the tests."""

from typing import Any


def full_config_data() -> dict[str, Any]:
    """Return a complete and valid configuration as JSON-friendly data."""
    return {
        "general": {
            "power_sensor": "sensor.han_power",
            "power_limit_w": 9500,
            "turn_on_margin_w": 200,
            "regulation_window_s": 30,
            "regulation_interval": 2,
            "wait_at_limit_s": 240,
            "wait_curve_steepness": 4.5,
            "wait_curve_pivot": 85,
            "appliance_repeat_increment_factor": 0.75,
            "appliance_repeat_increments": 3,
            "charger_repeat_increment_factor": 0.25,
            "charger_repeat_increments": 9,
            "penalty_threshold_w": 500,
            "command_repeat_interval_min": 45,
            "action_timeout_s": 90,
            "power_sensor_timeout_s": 120,
        },
        "appliances": [
            {
                "id": "a1",
                "entity_id": "switch.water_heater",
                "turn_on": {"mode": "default"},
                "turn_off": {
                    "mode": "custom",
                    "action": [
                        {
                            "action": "switch.turn_off",
                            "target": {"entity_id": "{{ entity_id }}"},
                            "data": {},
                        }
                    ],
                },
                "power_reserve_w": None,
                "variants": [
                    {
                        "id": "v1",
                        "label": "Morning",
                        "condition": {
                            "type": "template",
                            "value": "{{ 5 <= now().hour < 8 }}",
                        },
                        "actions": {"turn_off": {"mode": "default"}},
                    }
                ],
            },
            {
                "id": "a2",
                "entity_id": "climate.bathroom",
                "turn_on": {"mode": "default"},
                "turn_off": {"mode": "default"},
                "power_reserve_w": 800,
                "variants": [],
            },
        ],
        "priority": [
            {"type": "appliance", "appliance_id": "a1", "variant_id": "v1"},
            {"type": "charger_group", "group_id": "g1"},
            {"type": "appliance", "appliance_id": "a2", "variant_id": None},
            {"type": "appliance", "appliance_id": "a1", "variant_id": None},
        ],
        "charger_groups": [
            {
                "id": "g1",
                "name": "EV chargers",
                "one_at_a_time": False,
                "chargers": [
                    {
                        "id": "c1",
                        "device_id": "garage_charger",
                        "entity_id": "switch.garage_charger",
                        "activate": {"mode": "default"},
                        "deactivate": {"mode": "default"},
                        "set_current": {
                            "mode": "custom",
                            "action": [
                                {
                                    "action": "number.set_value",
                                    "target": {"entity_id": "number.garage_charger_current"},
                                    "data": {"value": "{{ current }}"},
                                }
                            ],
                        },
                        "min_current_a": 6,
                        "max_current_a": 32,
                        "actively_charging": {
                            "type": "power_sensor",
                            "value": "sensor.garage_charger_power",
                        },
                        "power_reserve_w": 3000,
                        "car_connected": {
                            "type": "entity",
                            "value": "binary_sensor.garage_charger_car",
                        },
                        "charging_window": {"start": "22:00", "end": "06:00"},
                        "finish_after_window": True,
                        "override_ends": "car_disconnected",
                    }
                ],
            }
        ],
    }
