"""Example configurations shared by the tests."""

import json
from typing import Any


def with_second_charger(data: dict[str, Any]) -> dict[str, Any]:
    """Add a copy of the first EV charger, with its own entities, to its group, so one at a time and dynamic charging order apply."""
    chargers = data["charger_groups"][0]["chargers"]
    chargers.append(json.loads(json.dumps(chargers[0]).replace("garage", "carport").replace('"c1"', '"c2"')))
    return data


def full_config_data() -> dict[str, Any]:
    """Return a complete and valid configuration as JSON-friendly data."""
    return {
        "general": {
            "power_sensor": "sensor.han_power",
            "power_limit_w": 9500,
            "turn_on_margin_w": 200,
            "regulation_window_updates": 15,
            "power_sensor_interval_s": 2.0,
            "wait_at_limit_s": 240,
            "wait_curve_steepness": 4.5,
            "wait_curve_pivot": 85,
            "appliance_repeat_increment_factor": 0.75,
            "appliance_repeat_increments": 3,
            "ampere_damping_s": 120,
            "charger_waiting_factor": 3,
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
                "essential": False,
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
                "display_power": {"type": "power_sensor", "value": "sensor.water_heater_power"},
                "display_temperature": None,
            },
            {
                "id": "a2",
                "entity_id": "climate.bathroom",
                "turn_on": {"mode": "default"},
                "turn_off": {"mode": "default"},
                "essential": False,
                "power_reserve_w": 800,
                "variants": [],
                "display_power": None,
                "display_temperature": {"type": "template", "value": "{{ state_attr(entity_id, 'temperature') }}"},
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
                "dynamic_order": True,
                "chargers": [
                    {
                        "id": "c1",
                        "device_id": "garage_charger",
                        "switched_by": "on_off_entity",
                        "on_off_entity": "switch.garage_charger",
                        "activate": None,
                        "deactivate": None,
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
                            "type": "entity",
                            "value": "binary_sensor.garage_charger_charging",
                        },
                        "charging_power": {
                            "type": "power_sensor",
                            "value": "sensor.garage_charger_power",
                        },
                        "min_current_power_w": 3000,
                        "car_connected": {
                            "type": "state",
                            "value": "sensor.garage_charger_status",
                            "states": ["disconnected"],
                            "states_are_true": False,
                        },
                        "charging_window": {"start": "22:00", "end": "06:00"},
                        "charge_until_disconnected": True,
                        "cloud_controlled": True,
                        "start_delay_s": 120,
                        "override_ends": "car_disconnected",
                        "deactivate_on_fault": True,
                        "fault_flag": {"type": "template", "value": "{{ is_state('sensor.garage_charger_status', 'error') }}"},
                    }
                ],
            }
        ],
    }
