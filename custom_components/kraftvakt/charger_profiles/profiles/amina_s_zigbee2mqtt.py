"""Amina S with Zigbee2MQTT, whose entities are named in English in every language."""

from __future__ import annotations

from typing import Final

from ..profile import DEFAULT_ACTION, ChargerProfile, DeviceMatch, ProfileEntity, entity_action, entity_condition

PROFILE: Final = ChargerProfile(
    name="Amina S (Zigbee2MQTT)",
    device=DeviceMatch(integration="mqtt", manufacturer="Amina Distribution AS", model_id="amina S"),
    entity=ProfileEntity("switch"),
    activate=DEFAULT_ACTION,
    deactivate=DEFAULT_ACTION,
    set_current=entity_action(ProfileEntity("number", name="Charge limit")),
    car_connected=entity_condition(ProfileEntity("binary_sensor", name="Ev connected")),
    actively_charging=entity_condition(ProfileEntity("binary_sensor", name="Charging")),
    grace_period_s=120,
    deactivate_on_fault=True,
    fault_flag=entity_condition(ProfileEntity("binary_sensor", name="Alarm active")),
)
