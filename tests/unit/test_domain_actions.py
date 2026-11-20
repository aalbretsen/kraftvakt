"""Tests of the actions that belong to the domain of an entity."""

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kraftvakt.actions import (
    ActionRunner,
    action_issues,
    domain_actions_by_field,
)
from custom_components.kraftvakt.config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    ConfigValidationError,
    Issue,
    KraftvaktConfig,
)
from custom_components.kraftvakt.config_validation import missing_items, parse_config
from custom_components.kraftvakt.domain_actions import domain_action_templates
from custom_components.kraftvakt.regulation.model import (
    TurnOffAppliance,
    TurnOnAppliance,
)

THERMOSTAT_ATTRIBUTES = {
    "hvac_modes": ["off", "heat", "auto"],
    "min_temp": 5,
    "max_temp": 30,
}


def domain(key: str, **data: Any) -> ActionConfig:
    return ActionConfig(ActionMode.DOMAIN, domain_action=key, data=data)


def thermostat(turn_on: ActionConfig, turn_off: ActionConfig, entity_id: str = "climate.hall") -> KraftvaktConfig:
    return KraftvaktConfig(
        appliances=(
            Appliance(
                "a1",
                entity_id,
                turn_on=turn_on,
                turn_off=turn_off,
            ),
        )
    )


def test_hvac_mode_defaults_depend_on_the_action_kind() -> None:
    """Heat or auto turns on, off or auto turns off."""
    actions = domain_actions_by_field()

    turn_on = actions["appliances"]["turn_on"]["climate_hvac_mode"]
    turn_off = actions["appliances"]["turn_off"]["climate_hvac_mode"]
    assert turn_on["service"] == "set_hvac_mode"
    assert turn_on["parameters"][0]["preferred_options"] == ["heat", "auto"]
    assert turn_off["parameters"][0]["preferred_options"] == ["off", "auto"]
    assert actions.keys() == {"appliances"}


def test_hvac_mode_is_the_suggested_action_and_no_domain_has_two() -> None:
    """The panel chooses the suggested domain action for a new entity, so there must be at most one per domain in each field."""
    for section in domain_actions_by_field().values():
        for actions in section.values():
            suggested = [action["domain"] for action in actions.values() if action["suggested"]]
            assert len(suggested) == len(set(suggested))
    turn_on = domain_actions_by_field()["appliances"]["turn_on"]
    assert [key for key, action in turn_on.items() if action["suggested"]] == ["climate_hvac_mode"]


def test_temperature_starts_outside_every_range() -> None:
    action = domain_actions_by_field()["appliances"]["turn_on"]["climate_temperature"]

    assert action["parameters"] == [
        {
            "name": "temperature",
            "type": "temperature",
            "options_attribute": None,
            "preferred_options": [],
            "min_attribute": "min_temp",
            "max_attribute": "max_temp",
            "step_attribute": "target_temp_step",
            "default": 0,
        }
    ]


async def test_domain_actions_call_the_service_with_the_chosen_data(
    hass: HomeAssistant,
) -> None:
    modes = async_mock_service(hass, "climate", "set_hvac_mode")
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", hvac_mode="heat", temperature=22),
        domain("climate_hvac_mode", hvac_mode="off"),
    )
    runner = ActionRunner(hass, config)

    await runner.async_execute([TurnOnAppliance("a1"), TurnOffAppliance("a1")])

    assert [call.data for call in temperatures] == [{"entity_id": ["climate.hall"], "hvac_mode": "heat", "temperature": 22}]
    assert [call.data for call in modes] == [{"entity_id": ["climate.hall"], "hvac_mode": "off"}]


async def test_temperature_action_leaves_the_hvac_mode(hass: HomeAssistant) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    config = thermostat(
        domain("climate_temperature", temperature=21.5),
        domain("climate_temperature", temperature=8),
    )

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1"), TurnOffAppliance("a1")])

    assert [call.data for call in temperatures] == [
        {"entity_id": ["climate.hall"], "temperature": 21.5},
        {"entity_id": ["climate.hall"], "temperature": 8},
    ]


@pytest.mark.parametrize(
    ("config", "message"),
    [
        (
            thermostat(domain("climate_hvac_mode", hvac_mode=None), domain("x")),
            "a value of climate_hvac_mode is not chosen",
        ),
        (
            thermostat(domain("climate_hvac_mode"), domain("x")),
            "a value of climate_hvac_mode is not chosen",
        ),
        (
            thermostat(domain("climate_hvac_mode", hvac_mode="heat"), domain("x"), "switch.a"),
            "climate_hvac_mode is not available for switch.a",
        ),
        (
            thermostat(domain("unknown", temperature={"type": "temperature_sensor", "value": "sensor.wanted"}), domain("x")),
            "unknown is not available for climate.hall",
        ),
    ],
)
async def test_domain_action_that_cannot_run_is_logged(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    config: KraftvaktConfig,
    message: str,
) -> None:
    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert message in caplog.text


async def test_values_are_checked_against_the_entity(hass: HomeAssistant) -> None:
    """The HVAC mode must be supported, and the temperature in the entity's range."""
    hass.states.async_set("climate.hall", "heat", THERMOSTAT_ATTRIBUTES)
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", hvac_mode="cool", temperature=0),
        domain("climate_temperature", temperature=31),
    )

    assert action_issues(hass, config) == [
        Issue("unsupported_option", "appliances", "a1", "turn_on.hvac_mode"),
        Issue("outside_entity_range", "appliances", "a1", "turn_on.temperature"),
        Issue("outside_entity_range", "appliances", "a1", "turn_off.temperature"),
    ]


async def test_valid_values_have_no_issues(hass: HomeAssistant) -> None:
    hass.states.async_set("climate.hall", "heat", THERMOSTAT_ATTRIBUTES)
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", hvac_mode="auto", temperature=30),
        domain("climate_hvac_mode", hvac_mode=None),
    )

    assert action_issues(hass, config) == []


async def test_only_types_are_checked_without_the_entity(hass: HomeAssistant) -> None:
    """An entity that is not there has no attributes to check against."""
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", hvac_mode="cool", temperature=0),
        domain("climate_hvac_mode_and_temperature", hvac_mode=1, temperature=True),
    )

    assert action_issues(hass, config) == [
        Issue("invalid_type", "appliances", "a1", "turn_off.hvac_mode"),
        Issue("invalid_type", "appliances", "a1", "turn_off.temperature"),
    ]


async def test_domain_action_must_belong_to_the_entity(hass: HomeAssistant) -> None:
    config = KraftvaktConfig(
        appliances=(
            Appliance(
                "a1",
                "switch.a",
                turn_on=domain("climate_hvac_mode", hvac_mode="heat"),
                turn_off=domain("unknown"),
            ),
            Appliance(
                "a2",
                turn_on=domain("unknown"),
            ),
        ),
    )

    assert action_issues(hass, config) == [
        Issue("domain_action_unavailable", "appliances", "a1", "turn_on"),
        Issue("domain_action_unavailable", "appliances", "a1", "turn_off"),
    ]


async def test_every_value_of_the_action_is_required(hass: HomeAssistant) -> None:
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", temperature=20),
        domain("climate_hvac_mode", hvac_mode="off"),
    )

    assert action_issues(hass, config) == [Issue("required", "appliances", "a1", "turn_on.hvac_mode")]


async def test_temperature_template_is_rendered_with_the_variables_when_the_action_runs(hass: HomeAssistant) -> None:
    """It is not checked against the range of the entity, since its value is known only when it runs."""
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    hass.states.async_set("climate.hall", "heat", THERMOSTAT_ATTRIBUTES | {"current_temperature": 18})
    config = thermostat(domain("climate_temperature", temperature="{{ entity.attributes.current_temperature + 50 }}"), domain("climate_temperature", temperature=8))

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert action_issues(hass, config) == []
    assert [call.data["temperature"] for call in temperatures] == [68]


async def test_temperature_template_must_be_valid_and_given(hass: HomeAssistant) -> None:
    data = thermostat(domain("climate_temperature", temperature="{{ 20 "), domain("climate_temperature", temperature="")).to_dict()

    with pytest.raises(ConfigValidationError) as error:
        parse_config(data)

    assert error.value.issues == [Issue("invalid_template", "appliances", "a1", "turn_on.temperature")]
    data["appliances"][0]["turn_on"]["data"]["temperature"] = "{{ 20 }}"
    assert Issue("missing_action", "appliances", "a1", "turn_off") in missing_items(parse_config(data))


def test_an_unknown_domain_action_has_no_templates() -> None:
    assert domain_action_templates(domain("unknown", temperature="{{ 20 }}")) == {}


async def test_hvac_mode_cannot_be_a_template(hass: HomeAssistant) -> None:
    config = thermostat(domain("climate_hvac_mode", hvac_mode="{{ 'heat' }}"), domain("climate_hvac_mode", hvac_mode="off"))
    hass.states.async_set("climate.hall", "heat", THERMOSTAT_ATTRIBUTES)

    assert action_issues(hass, config) == [Issue("unsupported_option", "appliances", "a1", "turn_on.hvac_mode")]


def source(source_type: str, entity_id: str | None) -> dict[str, Any]:
    return {"type": source_type, "value": entity_id}


@pytest.mark.parametrize(
    ("temperature", "expected"),
    [
        (source("temperature_sensor", "input_number.wanted"), 21.5),
        (source("temperature_sensor", "sensor.cold"), 5),
        (source("temperature_sensor", "number.hot"), 30),
        (source("target_temperature", "climate.living_room"), 23),
        (source("current_temperature", "climate.living_room"), 19.5),
    ],
)
async def test_temperature_source_is_read_and_kept_within_the_range_of_the_thermostat(hass: HomeAssistant, temperature: dict[str, Any], expected: float) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    hass.states.async_set("climate.hall", "heat", THERMOSTAT_ATTRIBUTES)
    hass.states.async_set("input_number.wanted", "21.5")
    hass.states.async_set("sensor.cold", "-3", {"unit_of_measurement": "°C"})
    hass.states.async_set("number.hot", "45")
    hass.states.async_set("climate.living_room", "heat", {"temperature": 23, "current_temperature": 19.5})
    config = thermostat(domain("climate_hvac_mode_and_temperature", hvac_mode="heat", temperature=temperature), domain("climate_hvac_mode", hvac_mode="off"))

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert action_issues(hass, config) == []
    assert [call.data for call in temperatures] == [{"entity_id": ["climate.hall"], "hvac_mode": "heat", "temperature": expected}]


async def test_temperature_source_is_read_again_each_time_the_action_runs(hass: HomeAssistant) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    config = thermostat(domain("climate_temperature", temperature=source("temperature_sensor", "input_number.wanted")), domain("climate_temperature", temperature=8))
    runner = ActionRunner(hass, config)

    for wanted in ("20", "22"):
        hass.states.async_set("input_number.wanted", wanted)
        await runner.async_execute([TurnOnAppliance("a1")])

    assert [call.data["temperature"] for call in temperatures] == [20, 22]


async def test_temperature_source_is_given_in_the_unit_of_home_assistant(hass: HomeAssistant) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    hass.config.units = US_CUSTOMARY_SYSTEM
    hass.states.async_set("sensor.wanted", "20", {"unit_of_measurement": "°C"})
    config = thermostat(domain("climate_temperature", temperature=source("temperature_sensor", "sensor.wanted")), domain("climate_temperature", temperature=46))

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert [call.data["temperature"] for call in temperatures] == [pytest.approx(68)]


@pytest.mark.parametrize("state", ["unavailable", "warm", None])
async def test_temperature_source_without_a_value_fails_the_action(hass: HomeAssistant, state: str | None) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    if state is not None:
        hass.states.async_set("sensor.wanted", state)
    failures: list[tuple[str, str]] = []
    config = thermostat(domain("climate_temperature", temperature=source("temperature_sensor", "sensor.wanted")), domain("climate_temperature", temperature=8))

    await ActionRunner(hass, config, on_failure=lambda action, error: failures.append((action, error))).async_execute([TurnOnAppliance("a1"), TurnOffAppliance("a1")])

    assert failures == [("turn_on climate.hall", "sensor.wanted gives no temperature")]
    assert [call.data["temperature"] for call in temperatures] == [8]


async def test_temperature_source_without_an_entity_is_missing(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    config = thermostat(domain("climate_temperature", temperature=source("temperature_sensor", None)), domain("climate_temperature", temperature=8))

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert action_issues(hass, config) == []
    assert Issue("missing_action", "appliances", "a1", "turn_on") in missing_items(config)
    assert "a value of climate_temperature is not chosen" in caplog.text


@pytest.mark.parametrize(
    ("temperature", "code"),
    [
        (source("temperature_sensor", "switch.heater"), "unsupported_entity_domain"),
        (source("target_temperature", "sensor.wanted"), "not_a_thermostat"),
        (source("current_temperature", "not an entity"), "invalid_type"),
        (source("template", "{{ 20 }}"), "invalid_type"),
        ({"type": "temperature_sensor", "value": 20}, "invalid_type"),
        ({"type": ["temperature_sensor"], "value": "sensor.wanted"}, "invalid_type"),
    ],
)
async def test_temperature_source_must_name_an_entity_that_gives_a_temperature(hass: HomeAssistant, temperature: dict[str, Any], code: str) -> None:
    config = thermostat(domain("climate_temperature", temperature=temperature), domain("climate_temperature", temperature=8))

    assert action_issues(hass, config) == [Issue(code, "appliances", "a1", "turn_on.temperature")]


async def test_hvac_mode_cannot_be_a_temperature_source(hass: HomeAssistant) -> None:
    config = thermostat(domain("climate_hvac_mode", hvac_mode=source("temperature_sensor", "sensor.wanted")), domain("climate_hvac_mode", hvac_mode="off"))

    assert action_issues(hass, config) == [Issue("invalid_type", "appliances", "a1", "turn_on.hvac_mode")]
