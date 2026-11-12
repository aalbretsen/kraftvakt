"""Tests of the actions that belong to the domain of an entity."""

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
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
    Charger,
    ChargerGroup,
    Issue,
    KraftvaktConfig,
)
from custom_components.kraftvakt.regulation.model import (
    ActivateCharger,
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


def thermostat(
    turn_on: ActionConfig, turn_off: ActionConfig, entity_id: str = "climate.hall"
) -> KraftvaktConfig:
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
    assert actions["chargers"]["activate"].keys() == {
        "climate_hvac_mode",
        "climate_temperature",
        "climate_hvac_mode_and_temperature",
    }
    assert actions["chargers"]["set_current"] == {}


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

    assert [call.data for call in temperatures] == [
        {"entity_id": ["climate.hall"], "hvac_mode": "heat", "temperature": 22}
    ]
    assert [call.data for call in modes] == [
        {"entity_id": ["climate.hall"], "hvac_mode": "off"}
    ]


async def test_temperature_action_leaves_the_hvac_mode(hass: HomeAssistant) -> None:
    temperatures = async_mock_service(hass, "climate", "set_temperature")
    config = thermostat(
        domain("climate_temperature", temperature=21.5),
        domain("climate_temperature", temperature=8),
    )

    await ActionRunner(hass, config).async_execute(
        [TurnOnAppliance("a1"), TurnOffAppliance("a1")]
    )

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
            thermostat(
                domain("climate_hvac_mode", hvac_mode="heat"), domain("x"), "switch.a"
            ),
            "climate_hvac_mode is not available for switch.a",
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
        charger_groups=(
            ChargerGroup(
                "g1",
                chargers=(
                    Charger(
                        "c1",
                        entity_id="climate.charger",
                        activate=domain("climate_hvac_mode", hvac_mode="heat"),
                        set_current=domain("climate_temperature", temperature=20),
                    ),
                ),
            ),
        ),
    )

    assert action_issues(hass, config) == [
        Issue("domain_action_unavailable", "appliances", "a1", "turn_on"),
        Issue("domain_action_unavailable", "appliances", "a1", "turn_off"),
        Issue("domain_action_unavailable", "chargers", "c1", "set_current"),
    ]


async def test_every_value_of_the_action_is_required(hass: HomeAssistant) -> None:
    config = thermostat(
        domain("climate_hvac_mode_and_temperature", temperature=20),
        domain("climate_hvac_mode", hvac_mode="off"),
    )

    assert action_issues(hass, config) == [
        Issue("required", "appliances", "a1", "turn_on.hvac_mode")
    ]


async def test_charger_can_be_activated_with_a_domain_action(
    hass: HomeAssistant,
) -> None:
    modes = async_mock_service(hass, "climate", "set_hvac_mode")
    config = KraftvaktConfig(
        charger_groups=(
            ChargerGroup(
                "g1",
                chargers=(
                    Charger(
                        "c1",
                        entity_id="climate.charger",
                        activate=domain("climate_hvac_mode", hvac_mode="heat"),
                    ),
                ),
            ),
        )
    )

    await ActionRunner(hass, config).async_execute([ActivateCharger("c1")])

    assert [call.data["hvac_mode"] for call in modes] == ["heat"]
