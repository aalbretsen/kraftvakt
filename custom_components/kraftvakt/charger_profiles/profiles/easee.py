"""Easee chargers with the Easee integration from HACS.

The integration has no entity for the charging current or a connected car, so the profile uses its services and its status sensor.
Every command goes through the Easee cloud and is sent on even when nothing changes, and charging starts with a delay, so the charger is cloud-controlled.
"""

from __future__ import annotations

from typing import Any, Final

from ..profile import (
    ChargerProfile,
    DeviceMatch,
    ProfileEntity,
    custom_action,
    power_sensor_condition,
    template_condition,
)


def _service(service: str, **data: Any) -> dict[str, Any]:
    return {"action": f"easee.{service}", "data": {"device_id": "{{ device_id(entity_id) }}", **data}}


_STATUS: Final = ProfileEntity("sensor", translation_key="easee_status")

# The access level lasts, so a car plugged in while the charger is deactivated does not start charging by itself.
# Authorizing one charging session would not do: a charger stays activated when the car leaves, and is not activated again when it comes back.
PROFILE: Final = ChargerProfile(
    name="Easee",
    device=DeviceMatch(integration="easee"),
    entity=ProfileEntity("switch", translation_key="is_enabled"),
    activate=custom_action(_service("set_charger_access", access_level="open_for_all")),
    deactivate=custom_action(_service("set_charger_access", access_level="whitelist")),
    set_current=custom_action(_service("set_charger_dynamic_limit", current="{{ current }}")),
    car_connected=template_condition(
        "{% set status = states('$status') %}{{ none if status in ['offline', 'unknown', 'unavailable'] else status != 'disconnected' }}",
        status=_STATUS,
    ),
    charging_power=power_sensor_condition(ProfileEntity("sensor", translation_key="power")),
    done_flag=template_condition(
        "{% set status = states('$status') %}{{ none if status in ['offline', 'unknown', 'unavailable'] else status == 'completed' }}",
        status=_STATUS,
    ),
    cloud_controlled=True,
    deactivate_on_fault=True,
    # An erratic car is a fault too, so the user sees why it does not charge. It ends when the car is disconnected.
    fault_flag=template_condition(
        "{{ states('$status') in ['error', 'error_temperature_too_high', 'error_dead_powerboard', 'error_overcurrent', 'error_pen_fault', 'erratic_ev'] }}",
        status=_STATUS,
    ),
)
