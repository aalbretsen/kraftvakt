"""Drafting a charger profile from a charger filled in by hand, and the notes on what a profile cannot carry over."""

from typing import Any

import pytest

from custom_components.kraftvakt.charger_profiles.profile import (
    DEFAULT_ACTION,
    DeviceMatch,
    ProfileCondition,
    ProfileEntity,
    custom_action,
    entity_action,
    entity_condition,
    state_condition,
    template_condition,
)
from custom_components.kraftvakt.config_model import ConditionType
from diagnostics.charger_profile.draft import Drafts, ProfileDraft, draft_profiles
from diagnostics.diagnostics_file import DiagnosticsFile, NotADiagnosticsFileError

DEVICE_ID = "0123456789abcdef0123456789abcdef"
OTHER_DEVICE_ID = "fedcba9876543210fedcba9876543210"


def entity(entity_id: str, translation_key: str | None = None, name: str | None = None, **fields: Any) -> dict[str, Any]:
    return {"entity_id": entity_id, "translation_key": translation_key, "original_name": name, "has_entity_name": True, "disabled_by": None, **fields}


ENTITIES = [
    entity("switch.box_allowed", "allowed", "Allowed"),
    entity("number.box_current", None, "Current"),
    entity("binary_sensor.box_car", "car", "Car"),
    entity("sensor.box", None, None),
]


def device(**fields: Any) -> dict[str, Any]:
    return {"profile": None, "integration": "acme", "manufacturer": "Acme", "model": "Box", "model_id": "B-1", "entities": ENTITIES, **fields}


def charger(charger_id: str = "c1", **fields: Any) -> dict[str, Any]:
    return {
        "id": charger_id,
        "device_id": DEVICE_ID,
        "entity_id": "switch.box_allowed",
        "activate": {"mode": "default"},
        "deactivate": {"mode": "default"},
        "set_current": {"mode": "entity", "entity_id": "number.box_current"},
        "car_connected": {"type": "entity", "value": "binary_sensor.box_car"},
        "charging_power": {"type": "power_sensor", "value": "sensor.box"},
        **fields,
    }


def drafts(chargers: list[dict[str, Any]], devices: dict[str, Any]) -> Drafts:
    config = {"charger_groups": [{"id": "g1", "name": "Garage", "chargers": chargers}]}
    return draft_profiles(DiagnosticsFile({"data": {"config": config, "charger_devices": devices}}))


def draft(device_fields: dict[str, Any] | None = None, **charger_fields: Any) -> ProfileDraft:
    (only,) = drafts([charger(**charger_fields)], {"c1": device(**(device_fields or {}))}).profiles
    return only


def test_a_charger_with_entities_of_its_device_gives_a_profile_without_notes() -> None:
    result = draft(cloud_controlled=True)

    assert result.module == "acme_b_1"
    assert result.profile.name == "Acme B-1"
    assert result.profile.device == DeviceMatch("acme")
    assert result.profile.entity == ProfileEntity("switch", translation_key="allowed")
    assert result.profile.activate == DEFAULT_ACTION
    assert result.profile.set_current == entity_action(ProfileEntity("number", name="Current"))
    assert result.profile.car_connected == entity_condition(ProfileEntity("binary_sensor", translation_key="car"))
    assert result.profile.actively_charging is None
    assert result.profile.charging_power == ProfileCondition(ConditionType.POWER_SENSOR, entity=ProfileEntity("sensor"))
    assert result.profile.cloud_controlled
    assert result.notes == ()


def test_the_states_of_an_entity_are_drafted_with_whether_they_count_as_true() -> None:
    result = draft(car_connected={"type": "state", "value": "binary_sensor.box_car", "states": ["disconnected"], "states_are_true": False})

    assert result.profile.car_connected == state_condition(ProfileEntity("binary_sensor", translation_key="car"), ("disconnected",), states_are_true=False)


def test_the_done_and_fault_flags_are_drafted_as_the_other_conditions() -> None:
    result = draft(
        done_flag={"type": "template", "value": "{{ is_state('sensor.box', 'completed') }}"},
        deactivate_on_fault=True,
        fault_flag={"type": "template", "value": "{{ is_state('sensor.box', 'error') }}"},
    )

    assert result.profile.done_flag == template_condition("{{ is_state('$sensor', 'completed') }}", sensor=ProfileEntity("sensor"))
    assert result.profile.deactivate_on_fault
    assert result.profile.fault_flag == template_condition("{{ is_state('$sensor', 'error') }}", sensor=ProfileEntity("sensor"))


def test_chargers_without_a_device_of_their_own_kind_are_skipped() -> None:
    result = drafts(
        [charger("c1"), charger("c2", device_id=None), charger("c3"), charger("c4"), charger("c5")],
        {"c1": device(), "c3": None, "c4": device(profile="Easee"), "c5": device()},
    )

    assert [profile.charger_id for profile in result.profiles] == ["c1"]
    assert result.skipped == (
        "Charger c2 has no device.",
        "Charger c3: its device is no longer in Home Assistant.",
        "Charger c4 has the profile Easee.",
        "Charger c5 has the same kind of device as charger c1.",
    )


@pytest.mark.parametrize("data", [{}, {"config": {"charger_groups": "none"}}, {"config": {}}])
def test_diagnostics_without_a_configuration_that_can_be_read_are_refused(data: dict[str, Any]) -> None:
    with pytest.raises(NotADiagnosticsFileError):
        draft_profiles(DiagnosticsFile({"data": data}))


def test_a_device_of_an_integration_for_many_makers_is_matched_by_its_manufacturer_and_model() -> None:
    assert draft({"integration": "mqtt"}).profile.device == DeviceMatch("mqtt", manufacturer="Acme", model_id="B-1")

    without_model = draft({"integration": "mqtt", "model_id": None})

    assert without_model.profile.name == "Acme Box (mqtt)"
    assert without_model.profile.device == DeviceMatch("mqtt", manufacturer="Acme")
    assert without_model.notes == ("device: mqtt serves devices of many makers, and the device has no model ID, so the profile fits every model of its manufacturer.",)


def test_a_device_without_an_integration_is_noted() -> None:
    without_integration = draft({"integration": None, "manufacturer": None, "model": None, "model_id": None})
    assert without_integration.profile.device == DeviceMatch("")
    assert without_integration.module == "charger"
    assert without_integration.notes == ("device: it has no integration. Fill in the integration of the profile.",)


def test_entities_a_profile_cannot_find_are_noted() -> None:
    entities = [
        entity("switch.box_allowed", "allowed", "Allowed", disabled_by="user"),
        entity("number.box_current", None, "Box Current", has_entity_name=False),
        entity("binary_sensor.box_car", "car", "Car"),
        entity("binary_sensor.box_car_2", "car", "Car"),
    ]

    result = draft({"entities": entities}, actively_charging={"type": "entity", "value": "binary_sensor.elsewhere"}, charging_power=None)

    assert result.profile.car_connected == entity_condition(ProfileEntity("binary_sensor", translation_key="car"))
    assert result.profile.actively_charging == ProfileCondition(ConditionType.ENTITY)
    assert result.notes == (
        "entity_id: switch.box_allowed is disabled on this device, and a profile only uses enabled entities.",
        "set_current: number.box_current has no name of its own apart from the device, so its name 'Box Current' may hold the device's name.",
        "car_connected: binary_sensor.box_car is not the only entity of the device that fits "
        "ProfileEntity(domain='binary_sensor', translation_key='car', name=None), so the profile leaves the field out.",
        "actively_charging: binary_sensor.elsewhere is not an entity of the charger's device, so a profile cannot find it.",
    )


def test_fields_that_are_not_set_are_noted_and_left_empty() -> None:
    result = draft(entity_id=None, activate=None, set_current={"mode": "entity", "entity_id": "number.elsewhere"}, car_connected=None)

    assert result.profile.entity == ProfileEntity("switch")
    assert result.profile.activate == custom_action()
    assert result.profile.set_current == custom_action()
    assert result.profile.car_connected == ProfileCondition(ConditionType.ENTITY)
    assert result.notes == (
        "entity_id: not set. Fill in the entity that is activated.",
        "activate: not set. Fill in the action.",
        "set_current: number.elsewhere is not an entity of the charger's device, so a profile cannot find it.",
        "car_connected: not set. Fill in the condition, or leave it out if the integration has nothing for it.",
    )


def test_a_main_entity_from_another_device_keeps_its_domain() -> None:
    result = draft(entity_id="light.elsewhere")

    assert result.profile.entity == ProfileEntity("light")
    assert result.notes == ("entity_id: light.elsewhere is not an entity of the charger's device, so a profile cannot find it.",)


def test_script_steps_name_the_charger_by_the_variable_entity_id() -> None:
    steps = [
        {"action": "acme.pause", "data": {"device_id": DEVICE_ID, "level": 1}},
        {"action": "switch.turn_off", "target": {"entity_id": ["switch.box_allowed", "{{ entity_id }}"]}},
    ]

    result = draft(deactivate={"mode": "custom", "action": steps})

    assert result.profile.deactivate == custom_action(
        {"action": "acme.pause", "data": {"device_id": "{{ device_id(entity_id) }}", "level": 1}},
        {"action": "switch.turn_off", "target": {"entity_id": ["{{ entity_id }}", "{{ entity_id }}"]}},
    )
    assert result.notes == ()


def test_script_steps_that_name_other_devices_and_entities_are_noted() -> None:
    steps = [
        {"action": "acme.pause", "data": {"device_id": OTHER_DEVICE_ID, "message": "{{ states('sensor.box') }}"}},
        {"action": "number.set_value", "target": {"entity_id": "number.box_current"}},
        {"action": "light.turn_on", "target": {"entity_id": "light.porch"}},
    ]

    result = draft(activate={"mode": "custom", "action": steps})

    assert result.profile.activate == custom_action(*steps)
    assert result.notes == (
        f"activate: the action names the device {OTHER_DEVICE_ID}, which is not the charger's device.",
        "activate: the action names sensor.box in \"{{ states('sensor.box') }}\". Give it by the variable entity_id, or leave it out.",
        "activate: the action names number.box_current, but script steps in a profile can only name the charger's own entity, by the variable entity_id.",
        "activate: the action names light.porch, which is not on the charger's device.",
    )


def test_a_domain_action_is_written_as_its_script_steps() -> None:
    entities = [entity("climate.box", None, None), *ENTITIES[1:]]
    domain_action = {"mode": "domain", "domain_action": "climate_hvac_mode", "data": {"hvac_mode": "heat"}}

    result = draft({"entities": entities}, entity_id="climate.box", activate=domain_action, deactivate=domain_action | {"domain_action": "unknown"})

    assert result.profile.activate == custom_action({"action": "climate.set_hvac_mode", "target": {"entity_id": "{{ entity_id }}"}, "data": {"hvac_mode": "heat"}})
    assert result.profile.deactivate == custom_action()
    assert result.notes == (
        "activate: the domain action climate_hvac_mode is written as the script steps it runs.",
        "deactivate: the domain action unknown does not fit the entity climate.box. Fill in the action.",
    )


def test_a_template_names_the_entities_of_the_device_by_placeholders() -> None:
    template = "{{ is_state('binary_sensor.box_car', 'on') and states.sensor.box.state != '$' and is_state('sun.sun', 'above_horizon') }}"

    result = draft(car_connected={"type": "template", "value": template})

    assert result.profile.car_connected == template_condition(
        "{{ is_state('$car', 'on') and states.$sensor.state != '$$' and is_state('sun.sun', 'above_horizon') }}",
        car=ProfileEntity("binary_sensor", translation_key="car"),
        sensor=ProfileEntity("sensor"),
    )
    assert result.notes == ("car_connected: the template names sun.sun, which is not on the charger's device.",)


def test_placeholders_are_unique_names_that_python_accepts_as_keyword_arguments() -> None:
    entities = [
        entity("sensor.box_status", "status"),
        entity("binary_sensor.box_status", "status"),
        entity("sensor.box_class", "class"),
        entity("sensor.box_phase", None, "1 phase"),
    ]
    template = "{{ [states('sensor.box_status'), states('binary_sensor.box_status'), states('sensor.box_class'), states('sensor.box_phase')] }}"

    result = draft({"entities": [*ENTITIES, *entities]}, car_connected={"type": "template", "value": template})

    assert result.profile.car_connected.template == "{{ [states('$status_2'), states('$status'), states('$sensor_class'), states('$sensor_1_phase')] }}"
    assert set(result.profile.car_connected.entities) == {"status", "status_2", "sensor_class", "sensor_1_phase"}
