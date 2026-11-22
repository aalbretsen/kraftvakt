"""Amina S with Zigbee2MQTT, whose entities are named in English in every language."""

from __future__ import annotations

from typing import Final

from ..profile import ChargerProfile, DeviceMatch, ProfileEntity, entity_action, entity_condition, power_sensor_condition

PROFILE: Final = ChargerProfile(
    name="Amina S (Zigbee2MQTT)",
    device=DeviceMatch(integration="mqtt", manufacturer="Amina Distribution AS", model_id="amina S"),
    on_off_entity=ProfileEntity("switch"),
    set_current=entity_action(ProfileEntity("number", name="Charge limit")),
    car_connected=entity_condition(ProfileEntity("binary_sensor", name="Ev connected")),
    charging_power=power_sensor_condition(ProfileEntity("sensor", name="Total active power")),
    actively_charging=entity_condition(ProfileEntity("binary_sensor", name="Charging")),
    start_delay_s=60,
    deactivate_on_fault=True,
    fault_flag=entity_condition(ProfileEntity("binary_sensor", name="Alarm active")),
)
