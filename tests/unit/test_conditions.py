"""Tests of true/false values from an entity or a template, of the charging power as evidence of charging, and of temperatures."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.conditions import (
    Variables,
    charging_evidence,
    condition_evidence,
    evaluate_condition,
    item_variables,
    power_value_w,
    temperature_value,
)
from custom_components.kraftvakt.config_model import Appliance, Charger, Condition, ConditionType

APPLIANCE = "switch.water_heater"


def appliance(hass: HomeAssistant, entity_id: str = APPLIANCE) -> Variables:
    return item_variables(hass, Appliance("a1", entity_id))


def charger(hass: HomeAssistant) -> Variables:
    return item_variables(hass, Charger("c1", device_id="garage", on_off_entity="switch.charger"))


def entity(value: str) -> Condition:
    return Condition(ConditionType.ENTITY, value)


def template(value: str) -> Condition:
    return Condition(ConditionType.TEMPLATE, value)


@pytest.mark.parametrize(
    ("state", "expected"),
    [("on", True), ("off", False), ("unavailable", False), ("unknown", False)],
)
async def test_entity_is_true_only_when_on(hass: HomeAssistant, state: str, expected: bool) -> None:
    hass.states.async_set("binary_sensor.morning", state)

    assert evaluate_condition(hass, entity("binary_sensor.morning"), appliance(hass)) is (expected)


async def test_missing_entity_is_false(hass: HomeAssistant) -> None:
    """A removed or disabled entity is not in the state machine."""
    assert not evaluate_condition(hass, entity("binary_sensor.borte"), appliance(hass))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("{{ true }}", True),
        ("{{ 1 < 2 }}", True),
        ("{{ false }}", False),
        ("{{ 'on' }}", False),
        ("{{ 1 }}", False),
        ("{{ none }}", False),
        ("", False),
    ],
)
async def test_template_is_true_only_for_the_boolean_true(hass: HomeAssistant, value: str, expected: bool) -> None:
    assert evaluate_condition(hass, template(value), appliance(hass)) is expected


@pytest.mark.parametrize("value", ["{{ 1 / 0 }}", "{{ states('x') | float }}", "{% if %}"])
async def test_failing_template_is_false(hass: HomeAssistant, value: str) -> None:
    assert not evaluate_condition(hass, template(value), appliance(hass))


@pytest.mark.parametrize(
    ("condition", "state", "expected"),
    [
        (entity("binary_sensor.car"), "on", True),
        (entity("binary_sensor.car"), "off", False),
        (entity("binary_sensor.car"), "unavailable", None),
        (template("{{ is_state('binary_sensor.car', 'on') }}"), "off", False),
        (template("{{ states('binary_sensor.car') }}"), "off", None),
        (template("{{ 1 / 0 }}"), "off", None),
    ],
)
async def test_evidence_either_way_or_none(hass: HomeAssistant, condition: Condition, state: str, expected: bool | None) -> None:
    """Only an entity that is on or off, or a boolean, is evidence."""
    hass.states.async_set("binary_sensor.car", state)

    assert condition_evidence(hass, condition, charger(hass)) is expected


async def test_missing_entity_is_no_evidence(hass: HomeAssistant) -> None:
    assert condition_evidence(hass, entity("binary_sensor.borte"), charger(hass)) is None


async def test_condition_that_is_not_set_is_no_evidence(hass: HomeAssistant) -> None:
    assert condition_evidence(hass, None, charger(hass)) is None


async def test_template_gets_the_entity_of_the_appliance(hass: HomeAssistant) -> None:
    """Templates can use `entity_id` and `entity` without naming it."""
    hass.states.async_set(APPLIANCE, "on", {"temperature": 55})
    condition = template("{{ entity_id == 'switch.water_heater' and entity.state == 'on' and entity.attributes.temperature < 60 }}")

    assert evaluate_condition(hass, condition, appliance(hass))


async def test_template_of_a_charger_gets_its_device(hass: HomeAssistant) -> None:
    """A charger has no entity of its own, so its templates get `device_id` instead of `entity_id` and `entity`."""
    assert evaluate_condition(hass, template("{{ device_id == 'garage' and entity_id is not defined }}"), charger(hass))


async def test_entity_variable_is_none_when_the_entity_is_missing(
    hass: HomeAssistant,
) -> None:
    assert evaluate_condition(hass, template("{{ entity is none }}"), appliance(hass))


@pytest.mark.parametrize(
    ("state", "unit", "expected"),
    [
        ("110", "W", True),
        ("100", "W", False),
        ("0.2", "kW", True),
        ("0.1", "kW", False),
        ("110", None, True),
        ("-500", "W", False),
        ("200", "A", None),
        ("unavailable", "W", None),
        ("unknown", "W", None),
    ],
)
async def test_charging_power_shows_charging_above_100_watt(hass: HomeAssistant, state: str, unit: str | None, expected: bool | None) -> None:
    hass.states.async_set("sensor.charger_power", state, {"unit_of_measurement": unit})
    condition = Condition(ConditionType.POWER_SENSOR, "sensor.charger_power")

    assert charging_evidence(power_value_w(hass, condition, charger(hass))) is expected


async def test_missing_power_sensor_is_no_evidence(hass: HomeAssistant) -> None:
    condition = Condition(ConditionType.POWER_SENSOR, "sensor.gone")

    assert charging_evidence(power_value_w(hass, condition, charger(hass))) is None


@pytest.mark.parametrize(
    ("condition", "expected"),
    [
        (Condition(ConditionType.TEMPERATURE_SENSOR, "sensor.tank"), (61.5, "°C")),
        (Condition(ConditionType.TEMPERATURE_SENSOR, "sensor.outdoor"), (-4.0, "°C")),
        (Condition(ConditionType.TEMPERATURE_SENSOR, "sensor.offline"), None),
        (Condition(ConditionType.TEMPERATURE_SENSOR, "sensor.gone"), None),
        (template("{{ state_attr(entity_id, 'temperature') }}"), (22.0, "°C")),
        (Condition(ConditionType.CURRENT_TEMPERATURE, "climate.bathroom"), (19.5, "°C")),
        (Condition(ConditionType.TARGET_TEMPERATURE, "climate.bathroom"), (22.0, "°C")),
        (Condition(ConditionType.CURRENT_TEMPERATURE, "climate.gone"), None),
        (Condition(ConditionType.TARGET_TEMPERATURE, "sensor.tank"), None),
        (template("{{ true }}"), None),
        (template("{{ 'warm' }}"), None),
        (template("{{ 'nan' }}"), None),
        (template("{{ none }}"), None),
        (None, None),
    ],
)
async def test_temperature_is_a_number_with_its_unit(hass: HomeAssistant, condition: Condition | None, expected: tuple[float, str] | None) -> None:
    hass.states.async_set("sensor.tank", "61.5", {"unit_of_measurement": "°C"})
    hass.states.async_set("sensor.outdoor", "-4")
    hass.states.async_set("sensor.offline", "unavailable")
    hass.states.async_set("climate.bathroom", "heat", {"temperature": 22, "current_temperature": 19.5})

    assert temperature_value(hass, condition, appliance(hass, "climate.bathroom")) == expected
