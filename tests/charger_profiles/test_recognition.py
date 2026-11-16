"""Recognising the profile of a device and filling a charger from it, whatever the profile."""

from dataclasses import replace

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.kraftvakt.charger_profiles import recognition
from custom_components.kraftvakt.charger_profiles.profile import ProfileEntity, entity_condition, template_condition
from custom_components.kraftvakt.charger_profiles.profiles import amina_s_zigbee2mqtt

from .conftest import Command, Device, DeviceEntity, charger_profile, register
from .profiles.test_amina_s_zigbee2mqtt import AMINA_S
from .profiles.test_easee import EASEE


async def test_device_without_a_profile_fills_nothing(hass: HomeAssistant, command: Command) -> None:
    plug = Device(integration="mqtt", name="Plug", manufacturer="IKEA", model_id="E1603", entities=[DeviceEntity("switch", None)])

    assert await charger_profile(command, register(hass, plug)) == {"profile": None, "fields": {}}
    assert await charger_profile(command, "unknown") == {"profile": None, "fields": {}}


async def test_entity_that_is_missing_disabled_or_not_the_only_one_that_fits_is_left_out(hass: HomeAssistant, command: Command) -> None:
    """The user enables the entities a profile needs, and fills in what the profile cannot."""
    entities = [entity for entity in AMINA_S.entities if entity.name not in ("Charge limit", "Charging")]
    entities.append(DeviceEntity("binary_sensor", "Charging", disabled=True))
    entities.append(DeviceEntity("switch", None))
    amina = replace(AMINA_S, entities=entities)

    fields = (await charger_profile(command, register(hass, amina)))["fields"]

    assert fields == {
        "activate": {"mode": "default"},
        "deactivate": {"mode": "default"},
        "car_connected": {"type": "entity", "value": "binary_sensor.amina_ev_connected"},
        "cloud_controlled": False,
        "deactivate_on_fault": True,
        "fault_flag": {"type": "entity", "value": "binary_sensor.amina_alarm_active"},
    }


async def test_entity_the_user_has_renamed_is_found_by_its_new_entity_id(hass: HomeAssistant, command: Command) -> None:
    device_id = register(hass, AMINA_S)
    er.async_get(hass).async_update_entity("binary_sensor.amina_ev_connected", new_entity_id="binary_sensor.garage_car", name="Garage car")

    fields = (await charger_profile(command, device_id))["fields"]

    assert fields["car_connected"] == {"type": "entity", "value": "binary_sensor.garage_car"}


async def test_template_needs_every_entity_it_names(hass: HomeAssistant, command: Command) -> None:
    easee = replace(EASEE, entities=[entity for entity in EASEE.entities if entity.translation_key != "easee_status"])

    fields = (await charger_profile(command, register(hass, easee)))["fields"]

    assert "car_connected" not in fields
    assert fields["entity_id"] == "switch.garage_charger_enabled"


async def test_profile_fills_the_fault_flag_it_finds(hass: HomeAssistant, command: Command, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = replace(
        amina_s_zigbee2mqtt.PROFILE,
        deactivate_on_fault=True,
        fault_flag=template_condition("{{ states('$alarms') not in ['', '[]'] }}", alarms=ProfileEntity("sensor", name="Alarms")),
    )
    monkeypatch.setattr(recognition, "PROFILES", (profile,))

    fields = (await charger_profile(command, register(hass, AMINA_S)))["fields"]

    assert fields["deactivate_on_fault"] is True
    assert fields["fault_flag"] == {"type": "template", "value": "{{ states('sensor.amina_alarms') not in ['', '[]'] }}"}


async def test_profile_whose_fault_flag_is_not_found_leaves_deactivate_on_fault_alone(hass: HomeAssistant, command: Command, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = replace(amina_s_zigbee2mqtt.PROFILE, deactivate_on_fault=True, fault_flag=entity_condition(ProfileEntity("binary_sensor", name="Missing")))
    monkeypatch.setattr(recognition, "PROFILES", (profile,))

    fields = (await charger_profile(command, register(hass, AMINA_S)))["fields"]

    assert "deactivate_on_fault" not in fields
    assert "fault_flag" not in fields
