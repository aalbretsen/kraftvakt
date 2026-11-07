"""Tests of the WebSocket commands for the panel (3.8, GUI-001, REG-010, REG-016)."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
WINDOW = timedelta(seconds=60)
DEFAULT = {"mode": "default"}


def appliance(appliance_id: str, **settings: Any) -> dict[str, Any]:
    return {
        "id": appliance_id,
        "entity_id": f"light.{appliance_id}",
        "turn_on": DEFAULT,
        "turn_off": DEFAULT,
        **settings,
    }


def config_data() -> dict[str, Any]:
    return {
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
    ],
)
async def test_commands_require_an_administrator(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    message: dict[str, Any],
) -> None:
    """GUI-001: only administrators may use the panel."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json_auto_id(message)
    response = await client.receive_json()

    assert not response["success"]
    assert response["error"]["code"] == "unauthorized"


async def test_capabilities_give_default_actions_limits_and_defaults(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    """3.6, 3.8: the panel gets the limits and default actions from one source."""
    client = await hass_ws_client(hass)

    response = await send(client, "kraftvakt/capabilities")

    assert response["success"]
    result = response["result"]
    assert result["default_actions"]["appliances"]["turn_on"] == [
        "switch",
        "input_boolean",
        "light",
        "fan",
        "climate",
        "water_heater",
    ]
    assert result["default_actions"]["chargers"]["set_current"] == [
        "number",
        "input_number",
    ]
    assert result["limits"]["general"]["power_limit_kw"] == {
        "min": 1,
        "max": 50,
        "step": 0.01,
    }
    assert result["limits"]["appliances"]["power_reserve_kw"]["max"] is None
    assert result["limits"]["chargers"]["power_reserve_kw"]["max"] == 5
    assert result["defaults"] == {
        "general": {
            "power_sensor": None,
            "power_limit_kw": 10.0,
            "regulation_window_s": 60,
            "regulation_interval": 1,
            "wait_at_limit_min": 5,
            "penalty_threshold_kw": 1.0,
        },
        "appliances": {"power_reserve_kw": None},
        "charging": {"enabled": False, "one_at_a_time": True},
        "chargers": {"min_current_a": 6, "max_current_a": 16, "power_reserve_kw": 4.0},
    }


async def test_config_get_gives_configuration_names_and_missing(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """GEN-013, GUI-005: the configuration with entity names and what is missing."""
    config["appliances"][1]["turn_off"] = None
    hass.states.async_set("light.a", "off", {"friendly_name": "Varmtvannsbereder"})
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
        "light.a": "Varmtvannsbereder",
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


async def test_commands_need_kraftvakt_to_be_loaded(
    hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator
) -> None:
    """The commands that need the runtime say so when Kraftvakt is not loaded."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    client = await hass_ws_client(hass)

    response = await send(client, "kraftvakt/config/get")

    assert not response["success"]
    assert response["error"]["code"] == "not_loaded"
