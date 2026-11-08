"""End-to-end tests of the regulation in Home Assistant.

They set the power sensor, move the time forward and check the actions that
reach the appliances.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import CoreState, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.kraftvakt.config_model import Issue
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
WINDOW = timedelta(seconds=60)
DEFAULT = {"mode": "default"}


def appliance(
    appliance_id: str, turn_on: dict[str, Any] = DEFAULT, **settings: Any
) -> dict[str, Any]:
    return {
        "id": appliance_id,
        "entity_id": f"light.{appliance_id}",
        "turn_on": turn_on,
        "turn_off": DEFAULT,
        **settings,
    }


@pytest.fixture
def config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a complete configuration with two appliances; tests may change it."""
    data = {
        "general": {
            "power_sensor": POWER_SENSOR,
            "power_limit_kw": 10.0,
            "regulation_window_s": 60,
            "regulation_interval": 1,
            "wait_at_limit_min": 0,
            "penalty_threshold_kw": 1.0,
        },
        "appliances": [appliance("a"), appliance("b")],
        "priority": [
            {"type": "appliance", "appliance_id": "a", "variant_id": None},
            {"type": "appliance", "appliance_id": "b", "variant_id": None},
        ],
    }
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": data,
    }
    return data


@pytest.fixture
def actions(hass: HomeAssistant) -> list[str]:
    """Record the turn on and turn off actions for the lights, in order."""
    recorded: list[str] = []

    def record(call: ServiceCall) -> None:
        for entity_id in call.data["entity_id"]:
            recorded.append(f"{call.service.removeprefix('turn_')} {entity_id}")

    hass.services.async_register("light", "turn_on", record)
    hass.services.async_register("light", "turn_off", record)
    return recorded


@pytest.fixture
async def setup_kraftvakt(hass: HomeAssistant, config: dict[str, Any]):
    async def setup() -> MockConfigEntry:
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        return entry

    return setup


async def run_pending_tasks() -> None:
    """Let started tasks run without waiting for blocked ones to finish."""
    for _ in range(20):
        await asyncio.sleep(0)


def set_power(hass: HomeAssistant, watt: str) -> None:
    hass.states.async_set(POWER_SENSOR, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta = WINDOW
) -> None:
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


def entity_id(hass: HomeAssistant, platform: str, key: str) -> str:
    found = er.async_get(hass).async_get_entity_id(platform, DOMAIN, key)
    assert found is not None
    return found


def regulation_switch(hass: HomeAssistant) -> str:
    state = hass.states.get(entity_id(hass, "switch", "regulation"))
    assert state is not None
    return state.state


def safe_state(hass: HomeAssistant) -> str:
    state = hass.states.get(entity_id(hass, "binary_sensor", "safe_state"))
    assert state is not None
    return state.state


async def switch_regulation(hass: HomeAssistant, service: str) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": entity_id(hass, "switch", "regulation")},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_everything_is_turned_off_at_startup(
    hass: HomeAssistant, actions: list[str], setup_kraftvakt
) -> None:
    """The regulation starts by itself with everything off."""
    set_power(hass, "2000")
    await setup_kraftvakt()

    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_ON
    assert safe_state(hass) == STATE_OFF


async def test_regulation_starts_when_home_assistant_has_started(
    hass: HomeAssistant, actions: list[str], setup_kraftvakt
) -> None:
    """The integrations of the appliances are loaded by then."""
    hass.set_state(CoreState.starting)
    set_power(hass, "2000")
    await setup_kraftvakt()
    assert actions == []
    assert regulation_switch(hass) == STATE_OFF

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_ON


async def test_user_start_before_home_assistant_has_started(
    hass: HomeAssistant, actions: list[str], setup_kraftvakt
) -> None:
    """The regulation is not started a second time when HA has started."""
    hass.set_state(CoreState.starting)
    set_power(hass, "2000")
    await setup_kraftvakt()
    await switch_regulation(hass, "turn_on")

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_ON


async def test_appliances_are_turned_on_one_per_decision(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """The first decision comes after one interval."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer, WINDOW - timedelta(seconds=1))
    assert actions == []
    await advance(hass, freezer, timedelta(seconds=1))
    assert actions == ["on light.a"]
    await advance(hass, freezer)
    assert actions == ["on light.a", "on light.b"]


async def test_decisions_follow_the_regulation_interval(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """With 2x, a decision is made for every second window."""
    config["general"]["regulation_interval"] = 2
    set_power(hass, "2000")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    assert actions == []
    await advance(hass, freezer)
    assert actions == ["on light.a"]
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["on light.a", "on light.b"]


async def test_lowest_priority_is_turned_off_above_the_limit(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    await advance(hass, freezer)
    actions.clear()

    set_power(hass, "12000")
    await advance(hass, freezer)

    assert actions == ["off light.b"]


async def test_stop_turns_everything_off_and_stops_the_decisions(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """Stopping works at once, and nothing is turned on."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    await switch_regulation(hass, "turn_off")
    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_OFF

    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b"]


async def test_start_waits_for_a_whole_window_after_the_start(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """A window that started before the start does not count."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await switch_regulation(hass, "turn_off")
    await advance(hass, freezer, timedelta(seconds=30))
    actions.clear()

    await switch_regulation(hass, "turn_on")
    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_ON

    await advance(hass, freezer, timedelta(seconds=30))
    assert actions == ["off light.a", "off light.b"]
    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b", "on light.a"]


async def test_turning_on_a_running_regulation_changes_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    await switch_regulation(hass, "turn_on")
    await advance(hass, freezer)

    assert actions == ["on light.b"]


async def test_turning_off_a_stopped_regulation_changes_nothing(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    await switch_regulation(hass, "turn_off")
    actions.clear()

    await switch_regulation(hass, "turn_off")

    assert actions == []
    assert regulation_switch(hass) == STATE_OFF


async def test_incomplete_configuration_does_not_start(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The switch stays off and the attempt is logged."""
    del config["appliances"][1]["turn_on"]
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    assert regulation_switch(hass) == STATE_OFF
    assert entry.runtime_data.missing == [
        Issue("missing_action", "appliances", "b", "turn_on")
    ]

    await switch_regulation(hass, "turn_on")
    await advance(hass, freezer)

    assert regulation_switch(hass) == STATE_OFF
    assert actions == []
    assert "The configuration is not complete: missing_action" in caplog.text


async def test_each_decision_is_logged_for_debugging(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Found in the exploratory test: only the commands were logged, not why."""
    caplog.set_level(logging.DEBUG, logger="custom_components.kraftvakt.runtime")
    set_power(hass, "2000")
    await setup_kraftvakt()

    await advance(hass, freezer)

    assert (
        "regulation average 2.0 kW, average consumption 2.0 kW, sensor valid True, "
        "safe state False, penalty False (0.0000 kWh), waiting None, "
        "commands [TurnOnAppliance(appliance_id='a')]"
    ) in caplog.text


async def test_safe_state_when_the_power_sensor_is_lost(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """One lost window is tolerated, two are not."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    set_power(hass, "unavailable")
    await advance(hass, freezer)
    assert actions == ["on light.b"]
    assert safe_state(hass) == STATE_OFF

    await advance(hass, freezer)
    assert actions == ["on light.b", "off light.a", "off light.b"]
    assert safe_state(hass) == STATE_ON
    assert regulation_switch(hass) == STATE_ON

    await advance(hass, freezer)
    assert actions == ["on light.b", "off light.a", "off light.b"]


async def test_regulation_starts_again_when_the_power_sensor_is_back(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    set_power(hass, "unavailable")
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert safe_state(hass) == STATE_ON
    actions.clear()

    await advance(hass, freezer, timedelta(seconds=30))
    set_power(hass, "3000")
    await advance(hass, freezer, timedelta(seconds=30))
    assert actions == ["off light.a", "off light.b"]
    assert safe_state(hass) == STATE_OFF

    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b", "on light.a"]


async def test_safe_state_before_the_first_measurement(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """A power sensor that never reports leads to the safe state."""
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    assert safe_state(hass) == STATE_OFF
    await advance(hass, freezer)

    assert safe_state(hass) == STATE_ON
    assert actions == ["off light.a", "off light.b"]


async def test_penalty_turns_everything_off_until_paid_back(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """The regulation starts again after it."""
    set_power(hass, "12000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b"]

    set_power(hass, "5000")
    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b"] * 2

    await advance(hass, freezer)
    assert actions == [*["off light.a", "off light.b"] * 2, "on light.a"]


async def test_variant_condition_moves_the_appliance(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """A true condition gives the variant's place in the list."""
    config["appliances"][1]["variants"] = [
        {
            "id": "morning",
            "label": "Morgen",
            "condition": {"type": "entity", "value": "input_boolean.morning"},
        }
    ]
    config["priority"].insert(
        0, {"type": "appliance", "appliance_id": "b", "variant_id": "morning"}
    )
    hass.states.async_set("input_boolean.morning", STATE_ON)
    set_power(hass, "2000")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)

    assert actions == ["on light.b"]


async def test_template_condition_gets_the_appliance_entity(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """`entity` is the state of the appliance's entity."""
    config["appliances"][1]["variants"] = [
        {
            "id": "cold",
            "label": "Kald",
            "condition": {
                "type": "template",
                "value": "{{ entity.attributes.temperature < 40 }}",
            },
        }
    ]
    config["priority"].insert(
        0, {"type": "appliance", "appliance_id": "b", "variant_id": "cold"}
    )
    hass.states.async_set("light.b", STATE_OFF, {"temperature": 35})
    set_power(hass, "2000")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)

    assert actions == ["on light.b"]


async def test_custom_action_gets_the_entity_variables(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config,
    setup_kraftvakt,
) -> None:
    """Custom actions run with `entity_id` and `entity`."""
    calls = async_mock_service(hass, "test", "heat")
    config["appliances"][0]["turn_on"] = {
        "mode": "custom",
        "action": [
            {
                "action": "test.heat",
                "data": {"target": "{{ entity_id }}", "was": "{{ entity.state }}"},
            }
        ],
    }
    hass.states.async_set("light.a", STATE_OFF)
    set_power(hass, "2000")
    await setup_kraftvakt()

    await advance(hass, freezer)

    assert [call.data for call in calls] == [{"target": "light.a", "was": "off"}]


async def test_failed_action_does_not_stop_the_regulation(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The error is logged, and the regulation goes on as if it worked."""
    attempts: list[ServiceCall] = []

    def fail(call: ServiceCall) -> None:
        attempts.append(call)
        raise HomeAssistantError("no answer")

    hass.services.async_register("test", "fail", fail)
    config["appliances"][0]["turn_on"] = {
        "mode": "custom",
        "action": [{"action": "test.fail"}],
    }
    set_power(hass, "2000")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)

    assert len(attempts) == 1
    assert actions == ["on light.b"]
    assert "Could not turn_on light.a: no answer" in caplog.text


async def test_appliance_states_are_not_taken_into_account(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """The regulation counts on what it last decided itself.

    Appliances switched outside Kraftvakt are not noticed, and no appliance is
    assumed to use power just because it was turned on.
    """
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    hass.states.async_set("light.a", STATE_OFF)
    hass.states.async_set("light.b", STATE_ON)
    await advance(hass, freezer)
    assert actions == ["on light.b"]

    set_power(hass, "12000")
    await advance(hass, freezer)
    assert actions == ["on light.b", "off light.b"]


async def test_reload_starts_the_regulation_again(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """A restart forgets the state and turns all off."""
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    await switch_regulation(hass, "turn_off")
    actions.clear()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert actions == ["off light.a", "off light.b"]
    assert regulation_switch(hass) == STATE_ON

    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b", "on light.a"]


async def test_reload_waits_for_the_actions_of_the_old_regulation(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, config, setup_kraftvakt
) -> None:
    """The appliances are turned off after the old actions have run."""
    recorded: list[str] = []
    release = asyncio.Event()

    async def slow_turn_on(call: ServiceCall) -> None:
        await release.wait()
        recorded.append("on")

    def turn_off(call: ServiceCall) -> None:
        recorded.append("off")

    hass.services.async_register("light", "turn_on", slow_turn_on)
    hass.services.async_register("light", "turn_off", turn_off)
    config["appliances"] = [appliance("a")]
    config["priority"] = config["priority"][:1]
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    freezer.tick(WINDOW)
    async_fire_time_changed(hass)
    await run_pending_tasks()
    recorded.clear()

    assert await hass.config_entries.async_reload(entry.entry_id)
    await run_pending_tasks()
    assert recorded == []

    release.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert recorded == ["on", "off"]


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        (
            "en",
            {
                "regulation": "Kraftvakt Regulation",
                "safe_state": "Kraftvakt Safe state",
            },
        ),
        (
            "nb",
            {
                "regulation": "Kraftvakt Regulering",
                "safe_state": "Kraftvakt Sikker tilstand",
            },
        ),
    ],
)
async def test_entity_names_are_translated(
    hass: HomeAssistant, setup_kraftvakt, language: str, expected: dict[str, str]
) -> None:
    """English is the default, and Norwegian is translated."""
    hass.config.language = language
    await setup_kraftvakt()

    names = {
        key: hass.states.get(entity_id(hass, platform, key)).attributes["friendly_name"]
        for platform, key in (("switch", "regulation"), ("binary_sensor", "safe_state"))
    }
    assert names == expected
