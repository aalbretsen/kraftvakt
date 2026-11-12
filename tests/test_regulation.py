"""End-to-end tests of the regulation in Home Assistant.

They set the power sensor, move the time forward and check the actions that
reach the appliances.
"""

import asyncio
import logging
import math
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import CoreState, HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.config_model import Issue
from custom_components.kraftvakt.config_reader import read_config
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.regulation.waiting import WaitingCurve
from custom_components.kraftvakt.status import status_snapshot
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
            "power_limit_w": 10000,
            "regulation_window_s": 60,
            "regulation_interval": 1,
            "wait_at_limit_s": 0,
            "penalty_threshold_w": 1000,
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
    """Move time on, with the power sensors reporting as a HAN reader does."""
    freezer.tick(delta)
    for sensor in (POWER_SENSOR,):
        if state := hass.states.get(sensor):
            hass.states.async_set(sensor, state.state, state.attributes)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def advance_windows(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, count: int
) -> None:
    """Close `count` windows, one at a time, since each schedules the next."""
    for _ in range(count):
        await advance(hass, freezer)


def entity_id(hass: HomeAssistant, platform: str, key: str) -> str:
    found = er.async_get(hass).async_get_entity_id(platform, DOMAIN, key)
    assert found is not None
    return found


def state_of(hass: HomeAssistant, platform: str, key: str) -> str:
    state = hass.states.get(entity_id(hass, platform, key))
    assert state is not None
    return state.state


def regulation_switch(hass: HomeAssistant) -> str:
    state = hass.states.get(entity_id(hass, "switch", "regulation"))
    assert state is not None
    return state.state


def safe_state(hass: HomeAssistant) -> str:
    state = hass.states.get(entity_id(hass, "binary_sensor", "regulation_safe_state"))
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
    """It is a repair issue, and the switch gives an error and stays off."""
    del config["appliances"][1]["turn_on"]
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    assert regulation_switch(hass) == STATE_OFF
    assert entry.runtime_data.missing == [
        Issue("missing_action", "appliances", "b", "turn_on")
    ]
    assert ir.async_get(hass).async_get_issue(DOMAIN, "regulation_not_started")

    with pytest.raises(ServiceValidationError) as error:
        await switch_regulation(hass, "turn_on")
    await advance(hass, freezer)

    assert error.value.translation_key == "config_incomplete"
    assert regulation_switch(hass) == STATE_OFF
    assert actions == []

    config["appliances"][1]["turn_on"] = DEFAULT
    await entry.runtime_data.async_save_config(read_config(config))
    await switch_regulation(hass, "turn_on")

    assert regulation_switch(hass) == STATE_ON
    assert not ir.async_get(hass).async_get_issue(DOMAIN, "regulation_not_started")


async def test_each_decision_is_logged_and_kept_for_the_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """They tell what each decision was based on, not only the commands."""
    caplog.set_level(logging.DEBUG, logger="custom_components.kraftvakt.runtime")
    assert await async_setup_component(hass, "diagnostics", {})
    set_power(hass, "2000")
    entry = await setup_kraftvakt()

    await advance(hass, freezer)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert diagnostics["recent_decisions"] == [
        {
            "time": dt_util.now().isoformat(timespec="seconds"),
            "regulation_average_w": 2000,
            "tariff_average_w": 2000,
            "power_sensor_valid": True,
            "safe_state": False,
            "penalty_active": False,
            "overconsumption_wh": 0.0,
            "waiting": None,
            "commands": ["TurnOnAppliance(appliance_id='a', variant_id=None)"],
        }
    ]
    assert diagnostics["config"]["appliances"][0]["id"] == "a"
    assert diagnostics["status"]["running"]
    assert "Decision: {'time': " in caplog.text


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

    assert state_of(hass, "binary_sensor", "penalty_active") == STATE_OFF
    assert state_of(hass, "sensor", "penalty_overconsumption") == "0.0"

    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b"]
    assert state_of(hass, "binary_sensor", "penalty_active") == STATE_ON
    assert float(state_of(hass, "sensor", "penalty_overconsumption")) == pytest.approx(
        2000 * 60 / 3600
    )

    set_power(hass, "5000")
    await advance(hass, freezer)
    assert actions == ["off light.a", "off light.b"] * 2
    assert state_of(hass, "binary_sensor", "penalty_active") == STATE_OFF
    assert state_of(hass, "sensor", "penalty_overconsumption") == "0.0"

    await advance(hass, freezer)
    assert actions == [*["off light.a", "off light.b"] * 2, "on light.a"]


async def test_variant_condition_moves_the_appliance(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """A true condition gives the variant's place in the list. The switch from
    the appliance itself at the first decision gives no turn-off action, since
    the appliance is turned on at the same decision."""
    config["appliances"][1]["variants"] = [
        {
            "id": "morning",
            "label": "Morning",
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


async def test_variant_moved_up_gets_room_until_it_is_turned_on(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Within the turn-on margin, the appliances below the variant are switched
    off one per decision until it can be turned on."""
    config["appliances"].append(appliance("c"))
    config["appliances"][1]["variants"] = [
        {
            "id": "swim",
            "label": "Swim",
            "condition": {"type": "entity", "value": "input_boolean.swim"},
        }
    ]
    config["priority"] = [
        {"type": "appliance", "appliance_id": "b", "variant_id": "swim"},
        {"type": "appliance", "appliance_id": "a", "variant_id": None},
        {"type": "appliance", "appliance_id": "c", "variant_id": None},
        {"type": "appliance", "appliance_id": "b", "variant_id": None},
    ]
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance_windows(hass, freezer, 2)
    set_power(hass, "9950")
    await advance(hass, freezer)
    actions.clear()

    hass.states.async_set("input_boolean.swim", STATE_ON)
    await advance_windows(hass, freezer, 3)
    set_power(hass, "5000")
    await advance(hass, freezer)

    assert actions == ["off light.b", "off light.c", "off light.a", "on light.b"]


def light_action(service: str, light: str) -> dict[str, Any]:
    return {
        "mode": "custom",
        "action": [{"action": f"light.{service}", "target": {"entity_id": [light]}}],
    }


async def test_variant_with_own_actions_is_switched_with_them(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Every switch of variant runs an action of the new variant, and stop
    turns the appliance off as its current variant does it."""
    config["appliances"][1]["variants"] = [
        {
            "id": "cool",
            "label": "Cool",
            "condition": {"type": "entity", "value": "input_boolean.cool"},
            "actions": {
                "turn_on": light_action("turn_on", "light.cool"),
                "turn_off": light_action("turn_off", "light.cool"),
            },
        }
    ]
    config["priority"].insert(
        1, {"type": "appliance", "appliance_id": "b", "variant_id": "cool"}
    )
    hass.states.async_set("input_boolean.cool", STATE_ON)
    set_power(hass, "2000")
    await setup_kraftvakt()
    assert actions == ["off light.a", "off light.b"]
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["off light.cool", "on light.a", "on light.cool"]
    actions.clear()

    hass.states.async_set("input_boolean.cool", STATE_OFF)
    await advance(hass, freezer)
    assert actions == ["on light.b"]
    actions.clear()

    hass.states.async_set("input_boolean.cool", STATE_ON)
    await advance(hass, freezer)
    await switch_regulation(hass, "turn_off")
    assert actions == ["on light.cool", "off light.a", "off light.cool"]


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
            "label": "Cold",
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
    entry = await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)

    assert len(attempts) == 1
    assert actions == ["on light.b"]
    assert "Could not turn_on light.a: no answer" in caplog.text
    assert [
        (failure["action"], failure["error"])
        for failure in entry.runtime_data.failed_actions
    ] == [("turn_on light.a", "no answer")]


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


ENTITY_NAMES = {
    "switch.kraftvakt_regulation": ("Regulation", "Regulering"),
    "binary_sensor.kraftvakt_regulation_safe_state": (
        "Regulation safe state",
        "Regulering sikker tilstand",
    ),
    "sensor.kraftvakt_regulation_steps_on": (
        "Regulation steps on",
        "Regulering innkoblede trinn",
    ),
    "number.kraftvakt_power_limit": ("Power limit", "Effektgrense"),
    "sensor.kraftvakt_power_regulation_average": (
        "Power regulation average",
        "Effekt reguleringssnitt",
    ),
    "sensor.kraftvakt_power_tariff_average": (
        "Power tariff average",
        "Effekt tariffsnitt",
    ),
    "sensor.kraftvakt_power_free": ("Power free", "Effekt ledig"),
    "sensor.kraftvakt_waiting_time_remaining": (
        "Waiting time remaining",
        "Ventetid gjenstående",
    ),
    "sensor.kraftvakt_waiting_time_next_turn_on": (
        "Waiting time next turn-on (calculated)",
        "Ventetid neste innkobling (beregnet)",
    ),
    "binary_sensor.kraftvakt_penalty_active": ("Penalty active", "Straff aktiv"),
    "sensor.kraftvakt_penalty_overconsumption": (
        "Penalty overconsumption",
        "Straff overforbruk",
    ),
    "switch.kraftvakt_appliance_light_a_excluded": (
        "light.a excluded from regulation",
        "light.a utenfor regulering",
    ),
    "switch.kraftvakt_appliance_light_b_excluded": (
        "light.b excluded from regulation",
        "light.b utenfor regulering",
    ),
}


@pytest.mark.parametrize(("language", "index"), [("en", 0), ("nb", 1)])
async def test_entity_ids_are_the_same_in_every_language(
    hass: HomeAssistant, setup_kraftvakt, language: str, index: int
) -> None:
    """The entity ids group the entities, and the names are translated."""
    hass.config.language = language
    enable_next_turn_on_sensor(hass)
    await setup_kraftvakt()

    names = {
        entity.entity_id: hass.states.get(entity.entity_id).attributes["friendly_name"]
        for entity in er.async_get(hass).entities.values()
        if entity.platform == DOMAIN
    }
    assert names == {
        entity_id: f"Kraftvakt {translated[index]}"
        for entity_id, translated in ENTITY_NAMES.items()
    }


def enable_next_turn_on_sensor(hass: HomeAssistant) -> None:
    """Register the sensor that is disabled by default as enabled."""
    er.async_get(hass).async_get_or_create(
        "sensor",
        DOMAIN,
        "waiting_time_next_turn_on",
        suggested_object_id="kraftvakt_waiting_time_next_turn_on",
    )


async def set_power_limit(hass: HomeAssistant, watt: float) -> None:
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id(hass, "number", "power_limit"), "value": watt},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)


def stored_power_limit(hass_storage: dict[str, Any]) -> int:
    return hass_storage[STORAGE_KEY]["data"]["general"]["power_limit_w"]


async def test_power_limit_is_the_stored_power_limit_in_w(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    await setup_kraftvakt()

    state = hass.states.get(entity_id(hass, "number", "power_limit"))
    assert state is not None
    assert state.state == "10000"
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "W"
    assert (state.attributes["min"], state.attributes["max"]) == (1000, 50000)
    assert state.attributes["step"] == 1
    assert state.attributes["mode"] == "box"


async def test_power_limit_is_saved_while_the_regulation_is_stopped(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    actions,
    setup_kraftvakt,
) -> None:
    """The new limit is saved and used from the next start."""
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    await switch_regulation(hass, "turn_off")
    actions.clear()

    await set_power_limit(hass, 8000.4)

    assert stored_power_limit(hass_storage) == 8000
    assert state_of(hass, "number", "power_limit") == "8000"
    assert entry.runtime_data.config.general.power_limit_w == 8000
    assert regulation_switch(hass) == STATE_OFF
    assert actions == []


async def test_power_limit_is_used_from_the_next_decision_without_a_restart(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
) -> None:
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions[-2:] == ["on light.a", "on light.b"]
    actions.clear()

    await set_power_limit(hass, 9000)
    await set_power_limit(hass, 7500)
    assert stored_power_limit(hass_storage) == 7500
    assert state_of(hass, "number", "power_limit") == "7500"
    assert entry.runtime_data.config.general.power_limit_w == 7500
    set_power(hass, "7600")
    await advance(hass, freezer)

    assert actions == ["off light.b"]


async def test_power_limit_changed_while_running_is_used_after_a_stop(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    set_power(hass, "7450")
    entry = await setup_kraftvakt()
    await set_power_limit(hass, 7500)
    await switch_regulation(hass, "turn_off")
    assert entry.runtime_data.config.general.power_limit_w == 7500

    await switch_regulation(hass, "turn_on")
    actions.clear()
    await advance(hass, freezer)
    assert actions == []


async def test_power_limit_changed_back_before_the_decision_changes_nothing(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    await set_power_limit(hass, 10000)
    await set_power_limit(hass, 8000)
    await set_power_limit(hass, 10000)
    await advance(hass, freezer)

    assert stored_power_limit(hass_storage) == 10000
    assert actions == ["on light.b"]


async def test_free_power_is_the_limit_minus_the_regulation_average(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, setup_kraftvakt
) -> None:
    set_power(hass, "2000")
    await setup_kraftvakt()
    assert state_of(hass, "sensor", "power_free") == STATE_UNAVAILABLE

    await advance(hass, freezer)
    set_power(hass, "12500")
    await advance(hass, freezer)

    state = hass.states.get(entity_id(hass, "sensor", "power_free"))
    assert state is not None
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "W"
    assert float(state.state) == pytest.approx(-2500)


async def test_waiting_time_sensors_follow_the_waiting_time(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    actions,
    setup_kraftvakt,
) -> None:
    """The time left counts to the decision that turns the appliance on."""
    config["general"]["wait_at_limit_s"] = 300
    set_power(hass, "9000")
    enable_next_turn_on_sensor(hass)
    await setup_kraftvakt()
    curve_waiting_s = 300 * WaitingCurve.from_settings(6, 80).share(0.9)
    windows_to_wait = math.ceil(curve_waiting_s / WINDOW.total_seconds())
    assert windows_to_wait > 1
    assert state_of(hass, "sensor", "waiting_time_remaining") == "0"
    assert state_of(hass, "sensor", "waiting_time_next_turn_on") == STATE_UNAVAILABLE
    actions.clear()

    await advance(hass, freezer)
    assert float(
        state_of(hass, "sensor", "waiting_time_next_turn_on")
    ) == pytest.approx(curve_waiting_s)
    assert int(state_of(hass, "sensor", "waiting_time_remaining")) == (
        windows_to_wait * WINDOW.total_seconds()
    )

    await advance(hass, freezer)
    assert int(state_of(hass, "sensor", "waiting_time_remaining")) == (
        (windows_to_wait - 1) * WINDOW.total_seconds()
    )

    for _ in range(windows_to_wait - 1):
        await advance(hass, freezer)
    assert actions == ["on light.a"]


def excluded_switch(hass: HomeAssistant, appliance_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"appliance_{appliance_id}_excluded"
    )


async def exclude(hass: HomeAssistant, appliance_id: str, service: str) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": excluded_switch(hass, appliance_id)},
        blocking=True,
    )


async def test_excluded_appliance_is_switched_off_at_the_next_decision(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """It is skipped from then on, and no longer counted as on."""
    set_power(hass, "2000")
    entry = await setup_kraftvakt()
    await advance(hass, freezer)
    await advance(hass, freezer)
    actions.clear()

    await exclude(hass, "a", "turn_on")
    assert actions == []
    await advance(hass, freezer)

    assert actions == ["off light.a"]
    assert state_of(hass, "sensor", "regulation_steps_on") == "1"
    assert [
        (item["id"], item["on"], item["excluded"])
        for item in status_snapshot(hass, entry.runtime_data)["priority"]
    ] == [("a", False, True), ("b", True, False)]


async def test_commands_are_repeated_at_any_window(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Decisions come every third window, and the commands of A and B are
    repeated at windows between them. Excluded C is left alone."""
    config["general"]["regulation_interval"] = 3
    config["general"]["command_repeat_interval_min"] = 10
    config["appliances"].append(appliance("c"))
    config["priority"].append(
        {"type": "appliance", "appliance_id": "c", "variant_id": None}
    )
    set_power(hass, "2000")
    await setup_kraftvakt()
    await exclude(hass, "c", "turn_on")
    actions.clear()

    await advance_windows(hass, freezer, 3)
    assert actions == ["on light.a"]
    set_power(hass, "9950")
    await advance_windows(hass, freezer, 6)
    assert actions == ["on light.a"]
    await advance(hass, freezer)
    assert actions == ["on light.a", "off light.b"]
    await advance_windows(hass, freezer, 3)
    assert actions == ["on light.a", "off light.b", "on light.a"]


async def test_appliance_included_again_gets_room(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """The appliance below is switched off, and comes on again after it."""
    set_power(hass, "2000")
    await setup_kraftvakt()
    await exclude(hass, "a", "turn_on")
    actions.clear()
    await advance(hass, freezer)
    assert actions == ["on light.b"]

    await exclude(hass, "a", "turn_off")
    await advance(hass, freezer)
    await advance(hass, freezer)

    assert actions == ["on light.b", "off light.b", "on light.a", "on light.b"]


async def test_excluded_switches_are_named_and_kept_over_a_reload(
    hass: HomeAssistant, hass_storage: dict[str, Any], actions, setup_kraftvakt
) -> None:
    """The positions are configuration, and the appliance names the switch."""
    hass.states.async_set("light.a", STATE_OFF, {"friendly_name": "Water heater"})
    entry = await setup_kraftvakt()
    await exclude(hass, "a", "turn_on")

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    switch = excluded_switch(hass, "a")
    assert switch == "switch.kraftvakt_appliance_water_heater_excluded"
    state = hass.states.get(switch)
    assert state is not None
    assert state.state == STATE_ON
    assert state.name == "Kraftvakt Water heater excluded from regulation"
    assert hass_storage[STORAGE_KEY]["data"]["appliance_switches"] == {
        "a": {"excluded": True},
        "b": {"excluded": False},
    }


async def test_excluded_switches_follow_the_configuration_without_reload(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Switches are added and removed with the appliances."""
    entry = await setup_kraftvakt()
    old_switch = excluded_switch(hass, "b")
    data = {
        **config,
        "appliances": [appliance("a"), appliance("c")],
        "priority": [
            {"type": "appliance", "appliance_id": "a", "variant_id": None},
            {"type": "appliance", "appliance_id": "c", "variant_id": None},
        ],
    }

    await entry.runtime_data.settings.async_update_config(read_config(data))
    await hass.async_block_till_done()

    assert excluded_switch(hass, "b") is None
    assert old_switch is not None
    assert hass.states.get(old_switch) is None
    assert state_of(hass, "switch", "appliance_c_excluded") == STATE_OFF
    assert hass_storage[STORAGE_KEY]["data"]["appliance_switches"] == {
        "a": {"excluded": False},
        "c": {"excluded": False},
    }


async def test_switches_of_removed_appliances_are_removed_at_setup(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    """No orphaned switches remain in the entity registry."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    orphan = registry.async_get_or_create(
        "switch", DOMAIN, "appliance_old_excluded", config_entry=entry
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert registry.async_get(orphan.entity_id) is None
    assert excluded_switch(hass, "a") is not None


async def test_an_entity_that_no_longer_exists_is_a_repair_issue(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
) -> None:
    """It is found when the regulation starts and when an action fails.

    An entity that only is unavailable is not an issue.
    """
    issues = ir.async_get(hass)
    hass.states.async_set("light.b", "unavailable")
    set_power(hass, "2000")
    await setup_kraftvakt()

    assert issues.async_get_issue(DOMAIN, "missing_entity_light.a")
    assert not issues.async_get_issue(DOMAIN, "missing_entity_light.b")

    hass.states.async_set("light.a", "off")
    hass.states.async_remove("light.b")
    hass.services.async_remove("light", "turn_on")
    await advance(hass, freezer)

    assert not issues.async_get_issue(DOMAIN, "missing_entity_light.a")
    assert issues.async_get_issue(DOMAIN, "missing_entity_light.b")


async def test_next_turn_on_sensor_is_disabled_by_default(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    await setup_kraftvakt()

    registry_entry = er.async_get(hass).async_get(
        entity_id(hass, "sensor", "waiting_time_next_turn_on")
    )
    assert registry_entry is not None
    assert registry_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
