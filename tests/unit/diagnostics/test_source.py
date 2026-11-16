"""The source of a drafted profile and its test: written as the repository's profiles are, and read back as the same profile."""

from pathlib import Path

from custom_components.kraftvakt.charger_profiles.profile import (
    DEFAULT_ACTION,
    ChargerProfile,
    DeviceMatch,
    ProfileCondition,
    ProfileEntity,
    custom_action,
    entity_action,
    entity_condition,
    power_sensor_condition,
    template_condition,
)
from custom_components.kraftvakt.config_model import ConditionType
from diagnostics.charger_profile.draft import DescribedEntity, ProfileDraft
from diagnostics.charger_profile.source import harness_entities, profile_source, profile_test_source

from ...diagnostics.drafted import PROFILE_TESTS_PACKAGE, PROFILES_PACKAGE, load

ENTITIES = (
    DescribedEntity("switch", None, None),
    DescribedEntity("switch.box", None, None),
    DescribedEntity("sensor.box_power", "power", "Power"),
    DescribedEntity("sensor.box_power_2", "power_l1", "Power"),
    DescribedEntity("sensor.box_voltage", "voltage", "Voltage", disabled=True),
)

PROFILE = ChargerProfile(
    name="Acme Box (mqtt)",
    device=DeviceMatch("mqtt", manufacturer="Acme", model_id="B-1"),
    entity=ProfileEntity("switch"),
    activate=DEFAULT_ACTION,
    deactivate=custom_action({"action": "acme.pause", "data": {"device_id": "{{ device_id(entity_id) }}", "now": True}}),
    set_current=entity_action(ProfileEntity("number", name="Current")),
    car_connected=template_condition("{{ states('$power') != '$$' }}", power=ProfileEntity("sensor", translation_key="power")),
    actively_charging=ProfileCondition(ConditionType.ENTITY),
    cloud_controlled=True,
    deactivate_on_fault=True,
    fault_flags=(
        entity_condition(ProfileEntity("binary_sensor", name="Error")),
        template_condition("{{ is_state('$power', 'error') }}", power=ProfileEntity("sensor", translation_key="power")),
    ),
)

DRAFT = ProfileDraft(module="acme_box_mqtt", profile=PROFILE, manufacturer="Acme", model_id="B-1", entities=ENTITIES[1:], charger_id="c1", notes=())


def written(tmp_path: Path, source: str, name: str) -> Path:
    path = tmp_path / f"{name}.py"
    path.write_text(source)
    return path


def test_the_written_profile_is_the_drafted_profile(tmp_path: Path) -> None:
    source = profile_source(DRAFT)

    assert "from ...config_model import ConditionType\nfrom ..profile import DEFAULT_ACTION, ChargerProfile, DeviceMatch, ProfileCondition," in source
    assert load(written(tmp_path, source, "acme_box_mqtt"), PROFILES_PACKAGE).PROFILE == PROFILE


def test_a_profile_without_cloud_controlled_leaves_the_setting_out(tmp_path: Path) -> None:
    profile = ChargerProfile(
        name="Acme",
        device=DeviceMatch("acme"),
        entity=ProfileEntity("switch", translation_key="allowed"),
        activate=DEFAULT_ACTION,
        deactivate=DEFAULT_ACTION,
        set_current=DEFAULT_ACTION,
        car_connected=ProfileCondition(ConditionType.ENTITY, entity=ProfileEntity("binary_sensor", translation_key="car")),
        actively_charging=power_sensor_condition(ProfileEntity("sensor", translation_key="power")),
    )
    draft = ProfileDraft(module="acme", profile=profile, manufacturer=None, model_id=None, entities=(), charger_id="c1", notes=())

    source = profile_source(draft)

    assert "cloud_controlled" not in source
    assert "fault" not in source
    assert "ConditionType" not in source
    assert draft.profile == load(written(tmp_path, source, "acme"), PROFILES_PACKAGE).PROFILE


def test_the_written_test_registers_the_device_with_every_entity(tmp_path: Path) -> None:
    drafted_test = load(written(tmp_path, profile_test_source(DRAFT), "test_acme_box_mqtt"), PROFILE_TESTS_PACKAGE)

    assert drafted_test.DEVICE.integration == "mqtt"
    assert (drafted_test.DEVICE.manufacturer, drafted_test.DEVICE.model_id) == ("Acme", "B-1")
    assert [(entity.domain, entity.name, entity.translation_key, entity.disabled) for entity in drafted_test.DEVICE.entities] == [
        ("switch", None, None, False),
        ("sensor", "Power", "power", False),
        ("sensor", "Power", "power_l1", False),
        ("sensor", "Voltage", "voltage", True),
    ]
    assert callable(drafted_test.test_acme_box_mqtt_fills_the_fields_of_a_charger)


def test_entities_in_the_test_harness_get_their_ids_from_the_device_and_entity_names() -> None:
    assert [entity.entity_id for entity in harness_entities(ENTITIES[1:])] == ["switch.garage", "sensor.garage_power", "sensor.garage_power_2", "sensor.garage_voltage"]
