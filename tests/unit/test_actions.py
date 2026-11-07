"""Tests of the actions for appliances and chargers (GEN-012, GEN-013, LAD-006)."""

import asyncio
from dataclasses import replace

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kraftvakt.actions import (
    ActionKind,
    ActionRunner,
    default_action_issues,
    default_action_steps,
    set_current_variables,
)
from custom_components.kraftvakt.config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    Charger,
    ChargingConfig,
    Issue,
    KraftvaktConfig,
)
from custom_components.kraftvakt.regulation.model import (
    TurnOffAppliance,
    TurnOnAppliance,
)

DEFAULT = ActionConfig(ActionMode.DEFAULT)


def custom(*steps: dict) -> ActionConfig:
    return ActionConfig(ActionMode.CUSTOM, steps)


def appliance(
    appliance_id: str,
    entity_id: str,
    turn_on: ActionConfig = DEFAULT,
    turn_off: ActionConfig = DEFAULT,
) -> Appliance:
    return Appliance(appliance_id, entity_id, turn_on=turn_on, turn_off=turn_off)


def charger(entity_id: str, set_current: ActionConfig = DEFAULT) -> Charger:
    return Charger(
        "c1",
        entity_id,
        activate=DEFAULT,
        deactivate=DEFAULT,
        set_current=set_current,
        min_current_a=6,
        max_current_a=16,
    )


@pytest.mark.parametrize(
    "domain",
    ["switch", "input_boolean", "light", "fan", "climate", "water_heater"],
)
def test_on_off_domains_have_default_actions(domain: str) -> None:
    entity_id = f"{domain}.x"

    assert default_action_steps(ActionKind.TURN_ON, entity_id) == [
        {"action": f"{domain}.turn_on", "target": {"entity_id": entity_id}}
    ]
    assert default_action_steps(ActionKind.TURN_OFF, entity_id) == [
        {"action": f"{domain}.turn_off", "target": {"entity_id": entity_id}}
    ]


@pytest.mark.parametrize("domain", ["number", "input_number"])
def test_number_domains_set_the_current_by_default(domain: str) -> None:
    assert default_action_steps(ActionKind.SET_CURRENT, f"{domain}.x") == [
        {
            "action": f"{domain}.set_value",
            "target": {"entity_id": f"{domain}.x"},
            "data": {"value": "{{ current }}"},
        }
    ]


@pytest.mark.parametrize(
    ("kind", "entity_id"),
    [
        (ActionKind.TURN_ON, "sensor.x"),
        (ActionKind.TURN_OFF, "number.x"),
        (ActionKind.SET_CURRENT, "switch.x"),
    ],
)
def test_domains_without_default_action(kind: ActionKind, entity_id: str) -> None:
    with pytest.raises(ValueError, match="no default action"):
        default_action_steps(kind, entity_id)


def test_default_actions_must_exist_for_the_domain() -> None:
    """A default action can only be chosen where the domain has one (GEN-013, T18)."""
    config = KraftvaktConfig(
        appliances=(
            appliance("a1", "switch.ok"),
            appliance("a2", "sensor.x", turn_off=custom({"action": "x.y"})),
            appliance("a3", "number.x"),
            Appliance("a4"),
        ),
        charging=ChargingConfig(
            chargers=(
                charger("switch.lader"),
                replace(charger("number.lader"), id="c2"),
            )
        ),
    )

    assert default_action_issues(config) == [
        Issue("default_action_unavailable", "appliances", "a2", "turn_on"),
        Issue("default_action_unavailable", "appliances", "a3", "turn_on"),
        Issue("default_action_unavailable", "appliances", "a3", "turn_off"),
        Issue("default_action_unavailable", "chargers", "c1", "set_current"),
        Issue("default_action_unavailable", "chargers", "c2", "activate"),
        Issue("default_action_unavailable", "chargers", "c2", "deactivate"),
    ]


@pytest.mark.parametrize(("current", "expected"), [(3, 6), (6, 6), (9, 9), (40, 16)])
def test_current_is_kept_between_min_and_max(current: int, expected: int) -> None:
    """The current to set always lies between the minimum and maximum (LAD-006)."""
    assert set_current_variables(charger("switch.lader"), current) == {
        "current": expected,
        "min_current": 6,
        "max_current": 16,
    }


async def test_default_actions_call_the_domain_service(hass: HomeAssistant) -> None:
    turned_on = async_mock_service(hass, "switch", "turn_on")
    turned_off = async_mock_service(hass, "light", "turn_off")
    config = KraftvaktConfig(
        appliances=(appliance("a1", "switch.a"), appliance("a2", "light.b"))
    )

    await ActionRunner(hass, config).async_execute(
        [TurnOnAppliance("a1"), TurnOffAppliance("a2")]
    )

    assert [call.data["entity_id"] for call in turned_on] == [["switch.a"]]
    assert [call.data["entity_id"] for call in turned_off] == [["light.b"]]


async def test_custom_actions_get_the_entity_variables(hass: HomeAssistant) -> None:
    """Custom actions get `entity_id` and `entity` (GEN-013, T14)."""
    calls = async_mock_service(hass, "test", "record")
    hass.states.async_set("switch.a", "off", {"mode": "eco"})
    action = custom(
        {
            "action": "test.record",
            "data": {
                "entity": "{{ entity_id }}",
                "mode": "{{ entity.attributes.mode }}",
            },
        }
    )
    config = KraftvaktConfig(appliances=(appliance("a1", "switch.a", turn_on=action),))
    runner = ActionRunner(hass, config)

    await runner.async_execute([TurnOnAppliance("a1")])
    hass.states.async_set("switch.a", "off", {"mode": "comfort"})
    await runner.async_execute([TurnOnAppliance("a1")])

    assert [call.data for call in calls] == [
        {"entity": "switch.a", "mode": "eco"},
        {"entity": "switch.a", "mode": "comfort"},
    ]


async def test_failed_action_is_logged_and_not_retried(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """The next commands still run after a failed action (GEN-012)."""
    failures: list[ServiceCall] = []

    def fail(call: ServiceCall) -> None:
        failures.append(call)
        raise HomeAssistantError("device offline")

    hass.services.async_register("test", "fail", fail)
    turned_off = async_mock_service(hass, "switch", "turn_off")
    config = KraftvaktConfig(
        appliances=(
            appliance("a1", "switch.a", turn_on=custom({"action": "test.fail"})),
            appliance("a2", "switch.b"),
        )
    )

    await ActionRunner(hass, config).async_execute(
        [TurnOnAppliance("a1"), TurnOffAppliance("a2")]
    )

    assert len(failures) == 1
    assert len(turned_off) == 1
    assert "Could not turn_on switch.a: device offline" in caplog.text


@pytest.mark.parametrize(
    "action",
    [
        custom({"action": "test.not_registered"}),
        custom({"not": "an action"}),
        DEFAULT,
    ],
)
async def test_action_that_cannot_run_is_logged(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, action: ActionConfig
) -> None:
    config = KraftvaktConfig(appliances=(appliance("a1", "sensor.a", turn_on=action),))

    await ActionRunner(hass, config).async_execute([TurnOnAppliance("a1")])

    assert "Could not turn_on sensor.a" in caplog.text


async def test_missing_action_is_logged(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    config = KraftvaktConfig(appliances=(Appliance("a1", "switch.a"),))

    await ActionRunner(hass, config).async_execute([TurnOffAppliance("a1")])

    assert "Could not turn_off switch.a: the action is not configured" in caplog.text


async def test_commands_run_one_at_a_time_in_order(hass: HomeAssistant) -> None:
    """Commands from a later decision wait for the earlier ones to finish."""
    order: list[str] = []
    release = asyncio.Event()

    async def slow(call: ServiceCall) -> None:
        order.append(f"start {call.data['entity_id'][0]}")
        await release.wait()
        order.append(f"end {call.data['entity_id'][0]}")

    async def fast(call: ServiceCall) -> None:
        order.append(f"off {call.data['entity_id'][0]}")

    hass.services.async_register("switch", "turn_on", slow)
    hass.services.async_register("switch", "turn_off", fast)
    config = KraftvaktConfig(
        appliances=(appliance("a1", "switch.a"), appliance("a2", "switch.b"))
    )
    runner = ActionRunner(hass, config)

    first = hass.async_create_task(runner.async_execute([TurnOnAppliance("a1")]))
    second = hass.async_create_task(runner.async_execute([TurnOffAppliance("a2")]))
    await asyncio.sleep(0)
    release.set()
    await asyncio.gather(first, second)

    assert order == ["start switch.a", "end switch.a", "off switch.b"]
