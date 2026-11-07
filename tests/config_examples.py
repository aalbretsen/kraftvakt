"""Example configurations shared by the tests."""

from typing import Any


def full_config_data() -> dict[str, Any]:
    """Return a complete and valid configuration as JSON-friendly data."""
    return {
        "general": {
            "power_sensor": "sensor.han_power",
            "power_limit_kw": 9.5,
            "regulation_window_s": 30,
            "regulation_interval": 2,
            "wait_at_limit_min": 4,
            "penalty_threshold_kw": 0.5,
        },
        "appliances": [
            {
                "id": "a1",
                "entity_id": "switch.varmtvannsbereder",
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
                "power_reserve_kw": None,
                "variants": [
                    {
                        "id": "v1",
                        "label": "Morgen",
                        "condition": {
                            "type": "template",
                            "value": "{{ 5 <= now().hour < 8 }}",
                        },
                    }
                ],
            },
            {
                "id": "a2",
                "entity_id": "climate.bad",
                "turn_on": {"mode": "default"},
                "turn_off": {"mode": "default"},
                "power_reserve_kw": 0.8,
                "variants": [],
            },
        ],
        "priority": [
            {"type": "appliance", "appliance_id": "a1", "variant_id": "v1"},
            {"type": "ev_charging"},
            {"type": "appliance", "appliance_id": "a2", "variant_id": None},
            {"type": "appliance", "appliance_id": "a1", "variant_id": None},
        ],
        "charging": {
            "enabled": True,
            "one_at_a_time": False,
            "chargers": [
                {
                    "id": "c1",
                    "entity_id": "switch.lader_garasje",
                    "activate": {"mode": "default"},
                    "deactivate": {"mode": "default"},
                    "set_current": {
                        "mode": "custom",
                        "action": [
                            {
                                "action": "number.set_value",
                                "target": {"entity_id": "number.lader_garasje_strom"},
                                "data": {"value": "{{ current }}"},
                            }
                        ],
                    },
                    "min_current_a": 6,
                    "max_current_a": 32,
                    "charge_power_sensor": "sensor.lader_garasje_effekt",
                    "power_reserve_kw": 3.0,
                    "car_connected": {
                        "type": "entity",
                        "value": "binary_sensor.lader_garasje_bil",
                    },
                    "charging_window": {"start": "22:00", "end": "06:00"},
                }
            ],
        },
    }
