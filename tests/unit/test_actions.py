"""Tests of the actions for appliances and chargers."""

import asyncio
from dataclasses import replace

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kraftvakt.actions import (
    ActionKind,
    ActionRunner,
    action_issues,
    default_action_steps,
    set_current_variables,
)
from custom_components.kraftvakt.config_model import (
    MAIN_ACTIONS,
    ActionConfig,
    ActionMode,
    Appliance,
    ApplianceActions,
    Charger,
    ChargerGroup,
    Condition,
    ConditionType,
    Issue,
    KraftvaktConfig,
    Variant,
)
from custom_components.kraftvakt.regulation.model import (
    ActivateCharger,
    DeactivateCharger,
    SetChargingCurrent,
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
    return Appliance(
        appliance_id,
        entity_id,
        actions={MAIN_ACTIONS: ApplianceActions(turn_on, turn_off)},
    )


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


async def test_actions_of_a_variant_are_checked_against_the_entity(
    hass: HomeAssistant,
) -> None:
    config = KraftvaktConfig(
        appliances=(
            Appliance(
                "a1",
                "sensor.x",
                actions={
                    MAIN_ACTIONS: ApplianceActions(custom(), custom()),
                    "v1": ApplianceActions(DEFAULT, custom()),
                },
                variants=(Variant("v1", "V", Condition(ConditionType.TEMPLATE, "")),),
            ),
        )
    )

    assert action_issues(hass, config) == [
        Issue("default_action_unavailable", "appliances", "a1", "variants.v1.turn_on")
    ]


async def test_default_actions_must_exist_for_the_domain(hass: HomeAssistant) -> None:
    """A default action can only be chosen where the domain has one."""
    config = KraftvaktConfig(
        appliances=(
            appliance("a1", "switch.ok"),
            appliance("a2", "sensor.x", turn_off=custom({"action": "x.y"})),
            appliance("a3", "number.x"),
            Appliance("a4"),
        ),
        charger_groups=(
            ChargerGroup(
                id="g1",
                chargers=(
                    charger("switch.charger"),
                    replace(charger("number.charger"), id="c2"),
                ),
            ),
        ),
    )

    assert action_issues(hass, config) == [
        Issue("default_action_unavailable", "appliances", "a2", "turn_on"),
        Issue("default_action_unavailable", "appliances", "a3", "turn_on"),
        Issue("default_action_unavailable", "appliances", "a3", "turn_off"),
        Issue("default_action_unavailable", "chargers", "c1", "set_current"),
        Issue("default_action_unavailable", "chargers", "c2", "activate"),
        Issue("default_action_unavailable", "chargers", "c2", "deactivate"),
    ]


@pytest.mark.parametrize(("current", "expected"), [(3, 6), (6, 6), (9, 9), (40, 16)])
def test_current_is_kept_between_min_and_max(current: int, expected: int) -> None:
    """The current to set always lies between the minimum and maximum."""
    assert set_current_variables(charger("switch.charger"), current) == {
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
    """Custom actions get `entity_id` and `entity`."""
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


async def test_variant_with_own_actions_runs_them(hass: HomeAssistant) -> None:
    """A variant without its own actions uses those of the appliance."""
    calls = async_mock_service(hass, "test", "record")

    def record(name: str) -> ActionConfig:
        return custom({"action": "test.record", "data": {"name": name}})

    config = KraftvaktConfig(
        appliances=(
            Appliance(
                "a1",
                "switch.a",
                actions={
                    MAIN_ACTIONS: ApplianceActions(record("on"), record("off")),
                    "cool": ApplianceActions(record("cool on"), record("cool off")),
                },
                variants=(
                    Variant("cool", "Cool", Condition(ConditionType.TEMPLATE, "")),
                    Variant("eco", "Eco", Condition(ConditionType.TEMPLATE, "")),
                ),
            ),
        )
    )

    await ActionRunner(hass, config).async_execute(
        [
            TurnOnAppliance("a1"),
            TurnOnAppliance("a1", "cool"),
            TurnOffAppliance("a1", "cool"),
            TurnOffAppliance("a1", "eco"),
        ]
    )

    assert [call.data["name"] for call in calls] == ["on", "cool on", "cool off", "off"]


async def test_failed_action_is_logged_and_not_retried(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """The next commands still run after a failed action."""
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


async def test_charger_actions_get_the_current_variables(hass: HomeAssistant) -> None:
    """The current is kept between the minimum and max."""
    activated = async_mock_service(hass, "switch", "turn_on")
    deactivated = async_mock_service(hass, "switch", "turn_off")
    currents = async_mock_service(hass, "test", "current")
    set_current = custom(
        {
            "action": "test.current",
            "data": {
                "entity": "{{ entity_id }}",
                "value": "{{ current }}",
                "range": "{{ min_current }}-{{ max_current }}",
            },
        }
    )
    config = KraftvaktConfig(
        charger_groups=(
            ChargerGroup(id="g1", chargers=(charger("switch.charger", set_current),)),
        )
    )

    await ActionRunner(hass, config).async_execute(
        [
            SetChargingCurrent("c1", 6),
            ActivateCharger("c1"),
            SetChargingCurrent("c1", 20),
            DeactivateCharger("c1"),
        ]
    )

    assert [call.data for call in currents] == [
        {"entity": "switch.charger", "value": 6, "range": "6-16"},
        {"entity": "switch.charger", "value": 16, "range": "6-16"},
    ]
    assert [call.data["entity_id"] for call in activated] == [["switch.charger"]]
    assert [call.data["entity_id"] for call in deactivated] == [["switch.charger"]]


async def test_charging_current_can_be_set_on_a_chosen_number_entity(
    hass: HomeAssistant,
) -> None:
    """The default action for the chosen entity, with the current as value."""
    values = async_mock_service(hass, "number", "set_value")
    set_current = ActionConfig(ActionMode.ENTITY, entity_id="number.charger_current")
    config = KraftvaktConfig(
        charger_groups=(
            ChargerGroup(id="g1", chargers=(charger("switch.charger", set_current),)),
        )
    )

    await ActionRunner(hass, config).async_execute(
        [SetChargingCurrent("c1", 9), SetChargingCurrent("c1", 20)]
    )

    assert [call.data for call in values] == [
        {"entity_id": ["number.charger_current"], "value": 9},
        {"entity_id": ["number.charger_current"], "value": 16},
    ]


async def test_entity_action_without_entity_is_logged(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    set_current = ActionConfig(ActionMode.ENTITY)
    config = KraftvaktConfig(
        charger_groups=(
            ChargerGroup(id="g1", chargers=(charger("switch.charger", set_current),)),
        )
    )

    await ActionRunner(hass, config).async_execute([SetChargingCurrent("c1", 6)])

    assert "the entity of the action is not chosen" in caplog.text


async def test_chosen_entity_must_have_a_default_action(hass: HomeAssistant) -> None:
    """Only number entities can be given to set the charging current."""
    config = KraftvaktConfig(
        charger_groups=(
            ChargerGroup(
                id="g1",
                chargers=(
                    charger(
                        "switch.a",
                        ActionConfig(ActionMode.ENTITY, entity_id="number.a"),
                    ),
                    replace(
                        charger(
                            "switch.b",
                            ActionConfig(ActionMode.ENTITY, entity_id="switch.b"),
                        ),
                        id="c2",
                    ),
                    replace(
                        charger("switch.c", ActionConfig(ActionMode.ENTITY)), id="c3"
                    ),
                ),
            ),
        )
    )

    assert action_issues(hass, config) == [
        Issue("unsupported_entity_domain", "chargers", "c2", "set_current")
    ]
