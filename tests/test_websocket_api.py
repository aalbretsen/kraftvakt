"""Tests of the WebSocket commands for the panel."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.kraftvakt.config_model import KraftvaktConfig
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.runtime import RegulationRunningError
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
WINDOW = timedelta(seconds=60)
DEFAULT = {"mode": "default"}


def appliance(appliance_id: str, **settings: Any) -> dict[str, Any]:
    return {
        "id": appliance_id,
        "entity_id": f"light.{appliance_id}",
        "actions": {"main": {"turn_on": DEFAULT, "turn_off": DEFAULT}},
        **settings,
    }


def config_data() -> dict[str, Any]:
    return {
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


@pytest.fixture
def config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a complete configuration with two appliances; tests may change it."""
    data = config_data()
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": data,
    }
    return data


@pytest.fixture
def lights(hass: HomeAssistant) -> list[str]:
    """Record the turn on and turn off actions for the lights, in order."""
    recorded: list[str] = []

    def record(call) -> None:
        for entity_id in call.data["entity_id"]:
            recorded.append(f"{call.service.removeprefix('turn_')} {entity_id}")

    hass.services.async_register("light", "turn_on", record)
    hass.services.async_register("light", "turn_off", record)
    return recorded


@pytest.fixture
async def entry(hass: HomeAssistant, config: dict[str, Any]) -> MockConfigEntry:
    """Set up Kraftvakt from the stored configuration."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return config_entry


async def send(client, message_type: str, **data: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": message_type, **data})
    return await client.receive_json()


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta = WINDOW
) -> None:
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


def set_power(hass: HomeAssistant, watt: str) -> None:
    hass.states.async_set(POWER_SENSOR, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


@pytest.mark.parametrize(
    "message",
    [
        {"type": "kraftvakt/capabilities"},
        {"type": "kraftvakt/config/get"},
        {"type": "kraftvakt/config/save", "config": {}},
        {"type": "kraftvakt/regulation/set_running", "running": False},
        {"type": "kraftvakt/status/subscribe"},
    ],
)
async def test_commands_require_an_administrator(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    message: dict[str, Any],
) -> None:
    """Only administrators may use the panel."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json_auto_id(message)
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"


async def test_capabilities_give_default_actions_limits_and_defaults(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    """The panel gets the limits and default actions from one source."""
    client = await hass_ws_client(hass)

    response = await send(client, "kraftvakt/capabilities")

    assert response["success"]
    result = response["result"]
    assert result["default_actions"]["appliances"]["turn_on"] == {
        "domains": [
            "switch",
            "input_boolean",
            "light",
            "fan",
            "climate",
            "water_heater",
        ],
        "service": "turn_on",
        "data": {},
    }
    assert result["default_actions"]["chargers"]["set_current"] == {
        "domains": ["number", "input_number"],
        "service": "set_value",
        "data": {"value": "{{ current }}"},
    }
    assert (
        result["domain_actions"]["appliances"]["turn_off"]["climate_hvac_mode"][
            "service"
        ]
        == "set_hvac_mode"
    )
    assert result["limits"]["general"]["power_limit_w"] == {
        "min": 1000,
        "max": 50_000,
        "step": 1,
    }
    assert result["limits"]["general"]["turn_on_margin_w"] == {
        "min": 1,
        "max": 1000,
        "step": 1,
    }
    assert result["limits"]["general"]["wait_curve_steepness"] == {
        "min": 1.5,
        "max": 9,
        "step": 0.5,
    }
    assert result["limits"]["general"]["charger_cycling_step_factor"] == {
        "min": 0.25,
        "max": 1,
        "step": 0.25,
    }
    assert result["limits"]["appliances"]["power_reserve_w"]["max"] is None
    assert result["limits"]["chargers"]["power_reserve_w"]["max"] == 5000
    assert result["defaults"] == {
        "general": {
            "power_sensor": None,
            "power_limit_w": 10000,
            "turn_on_margin_w": 100,
            "regulation_window_s": 10,
            "regulation_interval": 1,
            "wait_at_limit_s": 300,
            "wait_curve_steepness": 6.0,
            "wait_curve_pivot": 80,
            "appliance_cycling_step_factor": 0.5,
            "appliance_cycling_steps": 4,
            "charger_cycling_step_factor": 1.0,
            "charger_cycling_steps": 5,
            "penalty_threshold_w": 100,
        },
        "appliances": {"power_reserve_w": None},
        "charging": {"enabled": False, "one_at_a_time": True},
        "chargers": {"min_current_a": 6, "max_current_a": 16, "power_reserve_w": 4000},
    }


async def test_config_get_gives_configuration_names_and_missing(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The configuration with entity names and what is missing."""
    config["appliances"][1]["actions"]["main"]["turn_off"] = None
    hass.states.async_set("light.a", "off", {"friendly_name": "Water heater"})
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    client = await hass_ws_client(hass)

    response = await send(client, "kraftvakt/config/get")

    assert response["success"]
    result = response["result"]
    assert result["config"]["general"]["power_sensor"] == POWER_SENSOR
    assert [item["id"] for item in result["config"]["appliances"]] == ["a", "b"]
    assert result["entity_names"] == {
        "light.a": "Water heater",
        "light.b": "light.b",
    }
    assert result["missing"] == [
        {
            "code": "missing_action",
            "section": "appliances",
            "target": "b",
            "field": "turn_off",
        }
    ]


@pytest.mark.parametrize(
    "message",
    [
        {"type": "kraftvakt/config/get"},
        {"type": "kraftvakt/config/save", "config": {}},
        {"type": "kraftvakt/regulation/set_running", "running": True},
        {"type": "kraftvakt/status/subscribe"},
    ],
)
async def test_commands_need_kraftvakt_to_be_loaded(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    message: dict[str, Any],
) -> None:
    """The commands that need the runtime say so when Kraftvakt is not loaded."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(message)
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "not_loaded"


def entity_id(hass: HomeAssistant, platform: str, key: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(platform, DOMAIN, key)


async def switch_regulation(hass: HomeAssistant, service: str) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": entity_id(hass, "switch", "regulation")},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)


def stored_config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    return hass_storage[STORAGE_KEY]["data"]


async def test_save_is_refused_while_the_regulation_runs(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """The configuration cannot change while the regulation runs."""
    before = stored_config(hass_storage)
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["general"]["power_limit_w"] = 8.0

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert not response["success"]
    assert response["error"]["code"] == "regulation_running"
    assert stored_config(hass_storage) == before


async def test_runtime_refuses_a_new_configuration_while_running(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """The runtime itself guards the configuration."""
    runtime = entry.runtime_data

    with pytest.raises(RegulationRunningError):
        await runtime.async_save_config(KraftvaktConfig())

    assert runtime.config.general.power_sensor == POWER_SENSOR


@pytest.mark.parametrize(
    ("change", "errors"),
    [
        (
            lambda data: data["general"].update(power_limit_w=100000),
            [
                {
                    "code": "out_of_range",
                    "section": "general",
                    "field": "power_limit_w",
                }
            ],
        ),
        (
            lambda data: data["appliances"][1].update(entity_id="sensor.b"),
            [
                {
                    "code": "default_action_unavailable",
                    "section": "appliances",
                    "target": "b",
                    "field": field,
                }
                for field in ("turn_on", "turn_off")
            ],
        ),
        (
            lambda data: data.update(
                charging={
                    "chargers": [
                        {
                            "id": "c1",
                            "entity_id": "switch.charger",
                            "set_current": {
                                "mode": "entity",
                                "entity_id": "switch.charger_current",
                            },
                        }
                    ]
                }
            ),
            [
                {
                    "code": "unsupported_entity_domain",
                    "section": "chargers",
                    "target": "c1",
                    "field": "set_current",
                }
            ],
        ),
    ],
)
async def test_invalid_configuration_is_not_saved(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    change,
    errors: list[dict[str, str]],
) -> None:
    """Every issue is given per field, and nothing is saved."""
    await switch_regulation(hass, "turn_off")
    before = stored_config(hass_storage)
    client = await hass_ws_client(hass)
    changed = config_data()
    change(changed)

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert response["success"]
    assert response["result"] == {"saved": False, "errors": errors}
    assert stored_config(hass_storage) == before


async def test_domain_action_values_are_checked_against_the_entity(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """A thermostat's HVAC mode must be one it supports."""
    await switch_regulation(hass, "turn_off")
    hass.states.async_set("climate.hall", "off", {"hvac_modes": ["off", "heat"]})
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["appliances"][1]["entity_id"] = "climate.hall"
    changed["appliances"][1]["actions"]["main"]["turn_on"] = {
        "mode": "domain",
        "domain_action": "climate_hvac_mode",
        "data": {"hvac_mode": "auto"},
    }

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert response["result"] == {
        "saved": False,
        "errors": [
            {
                "code": "unsupported_option",
                "section": "appliances",
                "target": "b",
                "field": "turn_on.hvac_mode",
            }
        ],
    }
    changed["appliances"][1]["actions"]["main"]["turn_on"]["data"]["hvac_mode"] = "heat"
    response = await send(client, "kraftvakt/config/save", config=changed)
    assert response["result"]["saved"]
    assert stored_config(hass_storage)["appliances"][1]["actions"]["main"]["turn_on"][
        "data"
    ] == {"hvac_mode": "heat"}


async def test_incomplete_configuration_is_saved(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Saved with what is missing and the priority completed."""
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["general"]["power_sensor"] = None
    changed["appliances"].append(appliance("c"))

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert response["success"]
    result = response["result"]
    assert result["saved"]
    assert result["missing"] == [
        {"code": "missing_power_sensor", "section": "general", "field": "power_sensor"}
    ]
    assert result["config"]["priority"][-1] == {
        "type": "appliance",
        "appliance_id": "c",
        "variant_id": None,
    }
    assert stored_config(hass_storage)["general"]["power_sensor"] is None
    response = await send(client, "kraftvakt/config/get")
    assert response["result"]["config"] == result["config"]
    assert response["result"]["missing"] == result["missing"]


async def test_new_configuration_is_used_from_the_next_start(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
    lights: list[str],
) -> None:
    """No reload, and removed appliances get no more commands."""
    set_power(hass, "1000")
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["appliances"] = [appliance("c"), appliance("a")]
    changed["priority"] = []
    response = await send(client, "kraftvakt/config/save", config=changed)
    assert response["result"]["saved"]
    lights.clear()

    await switch_regulation(hass, "turn_on")
    await advance(hass, freezer)
    await advance(hass, freezer)
    await advance(hass, freezer)

    assert lights == ["off light.c", "off light.a", "on light.c", "on light.a"]


async def test_saved_power_sensor_and_window_are_measured(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The new sensor from now, the new window from the next."""
    set_power(hass, "1000")
    await switch_regulation(hass, "turn_off")
    hass.states.async_set("sensor.other", "4", {ATTR_UNIT_OF_MEASUREMENT: "kW"})
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["general"].update(power_sensor="sensor.other", regulation_window_s=30)
    await send(client, "kraftvakt/config/save", config=changed)

    await advance(hass, freezer)
    await advance(hass, freezer, timedelta(seconds=30))

    averages = entry.runtime_data.latest_averages
    assert averages.end - averages.start == timedelta(seconds=30)
    assert averages.regulation_average_w == pytest.approx(4000)
    set_power(hass, "9000")
    await advance(hass, freezer, timedelta(seconds=30))
    assert entry.runtime_data.latest_averages.regulation_average_w == pytest.approx(
        4000
    )


async def test_saved_chargers_get_their_switches(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The switches follow the saved chargers."""
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["charging"] = {
        "enabled": True,
        "one_at_a_time": False,
        "chargers": [
            {
                "id": "c1",
                "entity_id": "switch.charger",
                "activate": DEFAULT,
                "deactivate": DEFAULT,
                "set_current": {
                    "mode": "custom",
                    "action": [{"action": "number.set_value"}],
                },
                "actively_charging": {
                    "type": "power_sensor",
                    "value": "sensor.charger_power",
                },
            }
        ],
    }

    response = await send(client, "kraftvakt/config/save", config=changed)
    await hass.async_block_till_done()

    assert response["result"]["missing"] == []
    assert entity_id(hass, "switch", "charger_c1_excluded") is not None
    assert entity_id(hass, "switch", "charger_c1_window_override") is not None


def regulation_switch(hass: HomeAssistant) -> str:
    state = hass.states.get(entity_id(hass, "switch", "regulation"))
    assert state is not None
    return state.state


async def set_running(client, running: bool) -> dict[str, Any]:
    return await send(client, "kraftvakt/regulation/set_running", running=running)


async def test_set_running_stops_and_starts_like_the_switch(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    lights: list[str],
) -> None:
    """The panel and the switch are the same function."""
    client = await hass_ws_client(hass)

    response = await set_running(client, False)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert response["result"] == {"running": False}
    assert regulation_switch(hass) == "off"
    assert lights == ["off light.a", "off light.b"]

    response = await set_running(client, True)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert response["result"] == {"running": True}
    assert regulation_switch(hass) == "on"
    assert lights == ["off light.a", "off light.b"] * 2

    await switch_regulation(hass, "turn_off")
    response = await set_running(client, False)
    assert response["result"] == {"running": False}
    await switch_regulation(hass, "turn_on")
    response = await set_running(client, True)
    assert response["result"] == {"running": True}


async def test_start_is_refused_while_the_configuration_is_incomplete(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The regulation cannot start before the configuration is complete."""
    config["general"]["power_sensor"] = None
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    client = await hass_ws_client(hass)

    response = await set_running(client, True)

    assert not response["success"]
    assert response["error"]["code"] == "config_incomplete"
    assert "missing_power_sensor" in response["error"]["message"]
    assert regulation_switch(hass) == "off"


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return config_entry


async def subscribe_status(client) -> dict[str, Any]:
    """Subscribe to the status and return the first snapshot."""
    response = await send(client, "kraftvakt/status/subscribe")
    assert response["success"]
    return await next_status(client)


async def next_status(client) -> dict[str, Any]:
    message = await client.receive_json()
    assert message["type"] == "event"
    return message["event"]


def local(moment) -> str:
    return dt_util.as_local(moment).isoformat()


async def test_status_is_sent_at_once_and_at_each_window(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The status now, and after each window and decision."""
    started = dt_util.utcnow()
    hass.states.async_set("light.a", "off", {"friendly_name": "Water heater"})
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    status = await subscribe_status(client)

    assert status == {
        "running": True,
        "missing": [],
        "safe_state": False,
        "penalty": {
            "active": False,
            "overconsumption_wh": 0,
            "recovery_started": False,
        },
        "regulation_average_w": None,
        "capacity_average_w": None,
        "power_limit_w": 10000,
        "regulation_window_s": 60,
        "regulation_interval": 1,
        "next_decision_at": local(started + WINDOW),
        "appliances": [
            {
                "id": "a",
                "name": "Water heater",
                "on": False,
                "excluded": False,
                "variant": None,
                "waiting_since": None,
                "waiting_until": None,
                "waiting_ends_at": None,
            },
            {
                "id": "b",
                "name": "light.b",
                "on": False,
                "excluded": False,
                "variant": None,
                "waiting_since": None,
                "waiting_until": None,
                "waiting_ends_at": None,
            },
        ],
        "ev_charging_position": None,
        "chargers": [],
    }

    set_power(hass, "2000")
    await advance(hass, freezer)
    status = await next_status(client)

    assert status["regulation_average_w"] == pytest.approx(2000)
    assert status["capacity_average_w"] == pytest.approx(2000)
    assert status["next_decision_at"] == local(started + 2 * WINDOW)
    assert [item["on"] for item in status["appliances"]] == [True, False]


async def test_status_shows_the_variant_and_the_waiting_time(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The current variant, its place and the waiting."""
    started = dt_util.utcnow()
    config["general"]["wait_at_limit_s"] = 300
    config["appliances"][1]["variants"] = [
        {
            "id": "v1",
            "label": "Morning",
            "condition": {"type": "template", "value": "{{ true }}"},
        }
    ]
    config["priority"].insert(
        0, {"type": "appliance", "appliance_id": "b", "variant_id": "v1"}
    )
    set_power(hass, "7000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    status = await subscribe_status(client)
    assert [item["id"] for item in status["appliances"]] == ["a", "b"]

    await advance(hass, freezer)
    status = await next_status(client)

    assert [item["id"] for item in status["appliances"]] == ["b", "a"]
    assert status["appliances"][0]["variant"] == "Morning"
    assert status["appliances"][0]["waiting_since"] == local(started + WINDOW)
    waiting_until = dt_util.parse_datetime(status["appliances"][0]["waiting_until"])
    assert (waiting_until - started - WINDOW).total_seconds() == pytest.approx(
        75.4758, abs=1e-3
    )
    assert status["appliances"][0]["waiting_ends_at"] == local(started + 3 * WINDOW)
    assert status["appliances"][1]["waiting_until"] is None


async def test_status_follows_start_and_stop_from_the_panel_and_the_switch(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    """The status, the panel and the switch agree."""
    subscriber = await hass_ws_client(hass)
    commander = await hass_ws_client(hass)
    assert (await subscribe_status(subscriber))["running"]

    await set_running(commander, False)
    status = await next_status(subscriber)
    assert not status["running"]
    assert status["next_decision_at"] is None
    assert regulation_switch(hass) == "off"

    await switch_regulation(hass, "turn_on")
    assert (await next_status(subscriber))["running"]

    await switch_regulation(hass, "turn_off")
    assert not (await next_status(subscriber))["running"]
    response = await set_running(commander, True)
    assert response["result"] == {"running": True}
    assert (await next_status(subscriber))["running"]
    assert regulation_switch(hass) == "on"


async def test_status_follows_a_saved_configuration_and_a_reload(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The new configuration shows at once, and the status survives a reload."""
    subscriber = await hass_ws_client(hass)
    commander = await hass_ws_client(hass)
    await subscribe_status(subscriber)
    await set_running(commander, False)
    await next_status(subscriber)
    changed = config_data()
    changed["general"].update(power_sensor=None, power_limit_w=8000)

    await send(commander, "kraftvakt/config/save", config=changed)
    status = await next_status(subscriber)

    assert status["power_limit_w"] == 8000
    assert [issue["code"] for issue in status["missing"]] == ["missing_power_sensor"]

    changed["general"]["power_sensor"] = POWER_SENSOR
    await send(commander, "kraftvakt/config/save", config=changed)
    await next_status(subscriber)
    assert await hass.config_entries.async_reload(entry.entry_id)
    status = await next_status(subscriber)
    while not status["running"]:
        status = await next_status(subscriber)
    assert status["power_limit_w"] == 8000


async def test_status_shows_the_chargers(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Whether each charger is activated, with its details."""
    config["charging"] = {
        "enabled": True,
        "chargers": [
            {
                "id": "c1",
                "entity_id": "input_boolean.charger",
                "activate": DEFAULT,
                "deactivate": DEFAULT,
                "set_current": {
                    "mode": "custom",
                    "action": [{"action": "number.set_value"}],
                },
                "actively_charging": {
                    "type": "power_sensor",
                    "value": "sensor.charger_power",
                },
            }
        ],
    }
    config["priority"].append({"type": "ev_charging"})
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    status = await subscribe_status(client)

    assert status["chargers"] == [
        {
            "id": "c1",
            "name": "input_boolean.charger",
            "activated": False,
            "current_a": None,
            "bypassed": False,
            "waiting": False,
            "allowed": False,
            "excluded": None,
            "charging": False,
            "window_overridden": False,
            "car_connected": None,
            "waiting_since": None,
            "waiting_until": None,
            "waiting_ends_at": None,
        }
    ]
    assert status["ev_charging_position"] == 2


def charger(charger_id: str, **settings: Any) -> dict[str, Any]:
    return {
        "id": charger_id,
        "entity_id": f"input_boolean.{charger_id}",
        "activate": DEFAULT,
        "deactivate": DEFAULT,
        "set_current": {"mode": "custom", "action": [{"action": "number.set_value"}]},
        "actively_charging": {
            "type": "power_sensor",
            "value": f"sensor.{charger_id}_power",
        },
        **settings,
    }


async def test_status_shows_the_chargers_in_the_current_priority(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """A bypassed charger is shown last, with whether its car is connected."""
    config["charging"] = {
        "enabled": True,
        "chargers": [
            charger(
                "c1", car_connected={"type": "entity", "value": "binary_sensor.c1_car"}
            ),
            charger(
                "c2", car_connected={"type": "entity", "value": "binary_sensor.c2_car"}
            ),
        ],
    }
    config["priority"].append({"type": "ev_charging"})
    hass.states.async_set("binary_sensor.c1_car", "off")
    hass.states.async_set("binary_sensor.c2_car", "on")
    for charger_id in ("c1", "c2"):
        hass.states.async_set(f"sensor.{charger_id}_power", "0")
    set_power(hass, "1000")
    await setup_entry(hass)
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_id(hass, "switch", "charger_c2_excluded")},
        blocking=True,
    )
    client = await hass_ws_client(hass)
    await subscribe_status(client)

    await advance(hass, freezer)
    status = await next_status(client)

    assert [
        (
            item["id"],
            item["bypassed"],
            item["allowed"],
            item["excluded"],
            item["car_connected"],
        )
        for item in status["chargers"]
    ] == [("c2", False, False, True, True), ("c1", True, True, False, False)]


async def test_status_places_ev_charging_among_the_current_variants(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """«EV charging» moves when a variant moves an appliance above it."""
    config["charging"] = {
        "enabled": True,
        "one_at_a_time": False,
        "chargers": [charger("c1")],
    }
    config["appliances"][1]["variants"] = [
        {
            "id": "v1",
            "label": "Morning",
            "condition": {"type": "template", "value": "{{ true }}"},
        }
    ]
    config["priority"] = [
        {"type": "appliance", "appliance_id": "b", "variant_id": "v1"},
        {"type": "appliance", "appliance_id": "a", "variant_id": None},
        {"type": "ev_charging"},
        {"type": "appliance", "appliance_id": "b", "variant_id": None},
    ]
    hass.states.async_set("sensor.c1_power", "0")
    set_power(hass, "1000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    status = await subscribe_status(client)
    assert [item["id"] for item in status["appliances"]] == ["a", "b"]
    assert status["ev_charging_position"] == 1

    await advance(hass, freezer)
    status = await next_status(client)

    assert [item["id"] for item in status["appliances"]] == ["b", "a"]
    assert status["ev_charging_position"] == 2
