"""Tests of true/false values from an entity, a template or a power sensor."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.conditions import evaluate_condition
from custom_components.kraftvakt.config_model import Condition, ConditionType

APPLIANCE = "switch.water_heater"
CHARGER = "switch.charger"


def entity(value: str) -> Condition:
    return Condition(ConditionType.ENTITY, value)


def template(value: str) -> Condition:
    return Condition(ConditionType.TEMPLATE, value)


@pytest.mark.parametrize(
    ("state", "expected"),
    [("on", True), ("off", False), ("unavailable", False), ("unknown", False)],
)
async def test_entity_is_true_only_when_on(
    hass: HomeAssistant, state: str, expected: bool
) -> None:
    hass.states.async_set("binary_sensor.morning", state)

    assert evaluate_condition(hass, entity("binary_sensor.morning"), APPLIANCE) is (
        expected
    )


async def test_missing_entity_is_false(hass: HomeAssistant) -> None:
    """A removed or disabled entity is not in the state machine."""
    assert not evaluate_condition(hass, entity("binary_sensor.borte"), APPLIANCE)


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
async def test_template_is_true_only_for_the_boolean_true(
    hass: HomeAssistant, value: str, expected: bool
) -> None:
    assert evaluate_condition(hass, template(value), APPLIANCE) is expected


@pytest.mark.parametrize(
    "value", ["{{ 1 / 0 }}", "{{ states('x') | float }}", "{% if %}"]
)
async def test_failing_template_is_false(hass: HomeAssistant, value: str) -> None:
    assert not evaluate_condition(hass, template(value), APPLIANCE)


async def test_template_gets_the_entity_of_the_appliance(hass: HomeAssistant) -> None:
    """Templates can use `entity_id` and `entity` without naming it."""
    hass.states.async_set(APPLIANCE, "on", {"temperature": 55})
    condition = template(
        "{{ entity_id == 'switch.water_heater' and entity.state == 'on'"
        " and entity.attributes.temperature < 60 }}"
    )

    assert evaluate_condition(hass, condition, APPLIANCE)


async def test_entity_variable_is_none_when_the_entity_is_missing(
    hass: HomeAssistant,
) -> None:
    assert evaluate_condition(hass, template("{{ entity is none }}"), APPLIANCE)


@pytest.mark.parametrize(
    ("state", "unit", "expected"),
    [
        ("110", "W", True),
        ("100", "W", False),
        ("0.2", "kW", True),
        ("0.1", "kW", False),
        ("110", None, True),
        ("-500", "W", False),
        ("200", "A", False),
        ("unavailable", "W", False),
        ("unknown", "W", False),
    ],
)
async def test_power_sensor_is_true_above_100_watt(
    hass: HomeAssistant, state: str, unit: str | None, expected: bool
) -> None:
    hass.states.async_set("sensor.charger_power", state, {"unit_of_measurement": unit})
    condition = Condition(ConditionType.POWER_SENSOR, "sensor.charger_power")

    assert evaluate_condition(hass, condition, CHARGER) is expected


async def test_missing_power_sensor_is_false(hass: HomeAssistant) -> None:
    condition = Condition(ConditionType.POWER_SENSOR, "sensor.gone")

    assert not evaluate_condition(hass, condition, CHARGER)
