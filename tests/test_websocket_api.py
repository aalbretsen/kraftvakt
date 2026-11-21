"""Tests of the WebSocket commands for the panel."""

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
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
        "turn_on": DEFAULT,
        "turn_off": DEFAULT,
        **settings,
    }


def config_data() -> dict[str, Any]:
    return {
        "general": {
            "power_sensor": POWER_SENSOR,
            "power_limit_w": 10000,
            "regulation_window_updates": 1,
            "power_sensor_interval_s": 60,
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


async def run_pending_tasks() -> None:
    """Let started tasks run without waiting for a command that waits for reports."""
    for _ in range(20):
        await asyncio.sleep(0)


async def send(client, message_type: str, **data: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": message_type, **data})
    return await client.receive_json()


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta = WINDOW) -> None:
    """Move time on, with the power sensor reporting as a HAN reader does."""
    freezer.tick(delta)
    if state := hass.states.get(POWER_SENSOR):
        hass.states.async_set(POWER_SENSOR, state.state, state.attributes)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


def set_power(hass: HomeAssistant, watt: str) -> None:
    hass.states.async_set(POWER_SENSOR, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


@pytest.mark.parametrize(
    "message",
    [
        {"type": "kraftvakt/capabilities"},
        {"type": "kraftvakt/charger_profile/get", "device_id": "device"},
        {"type": "kraftvakt/power_sensor/interval", "entity_id": "sensor.han_power"},
        {"type": "kraftvakt/config/get"},
        {"type": "kraftvakt/config/save", "config": {}},
        {"type": "kraftvakt/regulation/set_running", "running": False},
        {"type": "kraftvakt/status/subscribe"},
        {"type": "kraftvakt/diagnostics/subscribe"},
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


async def test_capabilities_give_default_actions_limits_and_defaults(hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator) -> None:
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
    assert result["domain_actions"]["appliances"]["turn_off"]["climate_hvac_mode"]["service"] == "set_hvac_mode"
    assert "chargers" not in result["domain_actions"]
    assert result["limits"]["general"]["power_limit_w"] == {
        "min": 1000,
        "max": 50_000,
        "resolution": 1,
    }
    assert result["limits"]["general"]["turn_on_margin_w"] == {
        "min": 1,
        "max": 1000,
        "resolution": 1,
    }
    assert result["limits"]["general"]["wait_curve_steepness"] == {
        "min": 1.5,
        "max": 9,
        "resolution": 0.5,
    }
    assert result["limits"]["general"]["appliance_repeat_increment_factor"] == {
        "min": 0.25,
        "max": 1,
        "resolution": 0.25,
    }
    assert result["regulation_window"] == {"seconds": {"min": 10, "max": 120, "resolution": 1}, "choices": 12}
    assert result["limits"]["appliances"]["power_reserve_w"]["max"] is None
    assert result["limits"]["chargers"]["min_current_power_w"]["max"] == 5000
    assert result["defaults"] == {
        "general": {
            "power_sensor": None,
            "power_limit_w": 10000,
            "turn_on_margin_w": 100,
            "regulation_window_updates": None,
            "power_sensor_interval_s": None,
            "wait_at_limit_s": 300,
            "wait_curve_steepness": 6.0,
            "wait_curve_pivot": 80,
            "appliance_repeat_increment_factor": 0.5,
            "appliance_repeat_increments": 4,
            "ampere_damping_s": 300,
            "charger_waiting_factor": 2,
            "penalty_threshold_w": 100,
            "command_repeat_interval_min": 30,
            "action_timeout_s": 60,
            "power_sensor_timeout_s": 300,
        },
        "appliances": {"power_reserve_w": None},
        "charger_groups": {"one_at_a_time": True, "dynamic_order": False},
        "chargers": {
            "switched_by": "on_off_entity",
            "min_current_a": 6,
            "max_current_a": 16,
            "min_current_power_w": 4157,
            "override_ends": "manual",
            "start_delay_s": 300,
        },
    }


async def test_config_get_gives_configuration_names_and_missing(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    config["appliances"][1]["turn_off"] = None
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
        {"type": "kraftvakt/diagnostics/subscribe"},
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


async def test_runtime_refuses_a_new_configuration_while_running(hass: HomeAssistant, entry: MockConfigEntry) -> None:
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
                charger_groups=[
                    {
                        "id": "g1",
                        "name": "EV chargers",
                        "chargers": [
                            {
                                "id": "c1",
                                "on_off_entity": "switch.charger",
                                "set_current": {
                                    "mode": "entity",
                                    "entity_id": "switch.charger_current",
                                },
                            }
                        ],
                    }
                ]
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
    changed["appliances"][1]["turn_on"] = {
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
    changed["appliances"][1]["turn_on"]["data"]["hvac_mode"] = "heat"
    response = await send(client, "kraftvakt/config/save", config=changed)
    assert response["result"]["saved"]
    assert stored_config(hass_storage)["appliances"][1]["turn_on"]["data"] == {"hvac_mode": "heat"}


async def test_temperature_source_is_checked_and_stored(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """A temperature read from a thermostat must name a climate entity."""
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["appliances"][1]["entity_id"] = "climate.hall"
    changed["appliances"][1]["turn_on"] = {
        "mode": "domain",
        "domain_action": "climate_temperature",
        "data": {"temperature": {"type": "target_temperature", "value": "input_number.wanted"}},
    }

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert response["result"]["errors"] == [{"code": "not_a_thermostat", "section": "appliances", "target": "b", "field": "turn_on.temperature"}]
    source = {"type": "temperature_sensor", "value": "input_number.wanted"}
    changed["appliances"][1]["turn_on"]["data"]["temperature"] = source
    response = await send(client, "kraftvakt/config/save", config=changed)
    assert response["result"]["saved"]
    assert stored_config(hass_storage)["appliances"][1]["turn_on"]["data"] == {"temperature": source}


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
    assert result["missing"] == [{"code": "missing_power_sensor", "section": "general", "field": "power_sensor"}]
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


async def test_update_interval_is_listened_for_without_recorded_history(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Reports of an unchanged value count, and the last report before the command is the first time."""
    set_power(hass, "2000")
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kraftvakt/power_sensor/interval", "entity_id": POWER_SENSOR})
    await run_pending_tasks()
    for _ in range(4):
        freezer.tick(timedelta(seconds=2))
        set_power(hass, "2000")
        await run_pending_tasks()

    assert (await client.receive_json())["result"] == {"interval_s": 2.0}


async def test_update_interval_is_unknown_when_the_sensor_does_not_report(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Listening ends after 30 seconds, and a sensor that does not exist gives nothing either."""
    set_power(hass, "2000")
    client = await hass_ws_client(hass)

    for entity_id in (POWER_SENSOR, "sensor.missing"):
        await client.send_json_auto_id({"type": "kraftvakt/power_sensor/interval", "entity_id": entity_id})
        await run_pending_tasks()
        freezer.tick(timedelta(seconds=30))
        async_fire_time_changed(hass)
        assert (await client.receive_json())["result"] == {"interval_s": None}


async def test_saved_power_sensor_and_window_are_measured(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The new sensor from now, the new number of updates from the next window."""
    set_power(hass, "1000")
    await switch_regulation(hass, "turn_off")
    hass.states.async_set("sensor.other", "4", {ATTR_UNIT_OF_MEASUREMENT: "kW"})
    client = await hass_ws_client(hass)
    changed = config_data()
    changed["general"].update(power_sensor="sensor.other", regulation_window_updates=2)
    await send(client, "kraftvakt/config/save", config=changed)

    async def report_other() -> None:
        freezer.tick(WINDOW)
        set_power(hass, "9000")
        hass.states.async_set("sensor.other", "4", {ATTR_UNIT_OF_MEASUREMENT: "kW"})
        await hass.async_block_till_done(wait_background_tasks=True)

    await report_other()
    closed_at_first_report = entry.runtime_data.latest_averages
    await report_other()
    assert entry.runtime_data.latest_averages == closed_at_first_report
    await report_other()

    averages = entry.runtime_data.latest_averages
    assert averages.end - averages.start == 2 * WINDOW
    assert averages.regulation_average_w == pytest.approx(4000)


async def test_saved_chargers_get_their_switches(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    changed = config_with_charger(register_device(hass, "switch.charger", "binary_sensor.charger_car", "sensor.charger_power"))

    response = await send(client, "kraftvakt/config/save", config=changed)
    await hass.async_block_till_done()

    assert response["result"]["missing"] == []
    assert entity_id(hass, "switch", "charger_c1_excluded") is not None
    assert entity_id(hass, "switch", "charger_c1_window_override") is not None


def register_device(hass: HomeAssistant, *entity_ids: str) -> str:
    """Register the entities on a new device and return the id of the device."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={("test", entity_ids[0])})
    for entity_id in entity_ids:
        domain, object_id = entity_id.split(".")
        er.async_get(hass).async_get_or_create(
            domain,
            "test",
            object_id,
            suggested_object_id=object_id,
            device_id=device.id,
        )
    return device.id


def config_with_charger(device_id: str, **settings: Any) -> dict[str, Any]:
    data = config_data()
    data["charger_groups"] = [
        {
            "id": "g1",
            "name": "EV chargers",
            "one_at_a_time": False,
            "chargers": [
                {
                    "id": "c1",
                    "device_id": device_id,
                    "on_off_entity": "switch.charger",
                    "set_current": {
                        "mode": "custom",
                        "action": [{"action": "number.set_value"}],
                    },
                    "car_connected": {"type": "entity", "value": "binary_sensor.charger_car"},
                    "charging_power": {
                        "type": "power_sensor",
                        "value": "sensor.charger_power",
                    },
                    **settings,
                }
            ],
        }
    ]
    return data


async def test_charger_entities_must_belong_to_its_device(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Every entity the charger is given must be on the device; templates and
    custom actions are not checked."""
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    register_device(hass, "switch.charger", "binary_sensor.charger_car", "sensor.charger_power")
    other_device = register_device(hass, "number.other_current", "binary_sensor.other_car")
    changed = config_with_charger(
        other_device,
        set_current={"mode": "entity", "entity_id": "number.other_current"},
        car_connected={"type": "entity", "value": "binary_sensor.other_car"},
    )

    response = await send(client, "kraftvakt/config/save", config=changed)

    assert response["result"] == {
        "saved": False,
        "errors": [
            {
                "code": "entity_not_on_device",
                "section": "chargers",
                "target": "c1",
                "field": field,
            }
            for field in ("on_off_entity", "charging_power")
        ],
    }


async def test_display_sensors_must_belong_to_the_device_of_the_appliance(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Templates are not checked, and an appliance whose entity has no device may show any sensor."""
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)
    data = config_data()
    register_device(hass, data["appliances"][0]["entity_id"], "sensor.a_power")
    register_device(hass, "sensor.other_power", "sensor.other_temperature")
    data["appliances"][0]["display_power"] = {"type": "power_sensor", "value": "sensor.a_power"}
    data["appliances"][0]["display_temperature"] = {"type": "temperature_sensor", "value": "sensor.other_temperature"}
    data["appliances"][1]["display_power"] = {"type": "power_sensor", "value": "sensor.other_power"}
    data["appliances"][1]["display_temperature"] = {"type": "template", "value": "{{ 20 }}"}

    response = await send(client, "kraftvakt/config/save", config=data)

    assert response["result"] == {
        "saved": False,
        "errors": [{"code": "entity_not_on_device", "section": "appliances", "target": "a", "field": "display_temperature"}],
    }


async def test_charger_device_must_exist(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    await switch_regulation(hass, "turn_off")
    client = await hass_ws_client(hass)

    response = await send(client, "kraftvakt/config/save", config=config_with_charger("removed"))

    assert response["result"] == {
        "saved": False,
        "errors": [
            {
                "code": "unknown_device",
                "section": "chargers",
                "target": "c1",
                "field": "device_id",
            }
        ],
    }


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
    started = dt_util.utcnow()
    hass.states.async_set("light.a", "off", {"friendly_name": "Water heater"})
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    status = await subscribe_status(client)

    assert status == {
        "running": True,
        "config_version": 0,
        "missing": [],
        "safe_state": False,
        "penalty": {
            "active": False,
            "overconsumption_wh": 0,
            "recovery_started": False,
        },
        "regulation_average_w": None,
        "tariff_average_w": None,
        "power_limit_w": 10000,
        "regulation_window_s": 60,
        "next_decision_at": local(started + WINDOW),
        "priority": [
            {
                "type": "appliance",
                "id": "a",
                "name": "Water heater",
                "essential": False,
                "on": False,
                "excluded": False,
                "variant": None,
                "power_w": None,
                "temperature": None,
                "waiting_since": None,
                "waiting_until": None,
                "waiting_ends_at": None,
                "power_to_free_w": None,
            },
            {
                "type": "appliance",
                "id": "b",
                "name": "light.b",
                "essential": False,
                "on": False,
                "excluded": False,
                "variant": None,
                "power_w": None,
                "temperature": None,
                "waiting_since": None,
                "waiting_until": None,
                "waiting_ends_at": None,
                "power_to_free_w": None,
            },
        ],
    }

    set_power(hass, "2000")
    await advance(hass, freezer)
    status = await next_status(client)

    assert status["regulation_average_w"] == pytest.approx(2000)
    assert status["tariff_average_w"] == pytest.approx(2000)
    assert status["next_decision_at"] == local(started + 2 * WINDOW)
    assert [item["on"] for item in appliance_rows(status)] == [True, False]


async def test_status_shows_the_variant_and_the_waiting_time(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    started = dt_util.utcnow()
    config["general"]["wait_at_limit_s"] = 300
    config["appliances"][1]["variants"] = [
        {
            "id": "v1",
            "label": "Morning",
            "condition": {"type": "template", "value": "{{ true }}"},
        }
    ]
    config["priority"].insert(0, {"type": "appliance", "appliance_id": "b", "variant_id": "v1"})
    set_power(hass, "7000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    status = await subscribe_status(client)
    assert [item["id"] for item in appliance_rows(status)] == ["a", "b"]

    await advance(hass, freezer)
    status = await next_status(client)

    assert [item["id"] for item in appliance_rows(status)] == ["b", "a"]
    assert appliance_rows(status)[0]["variant"] == "Morning"
    assert appliance_rows(status)[0]["waiting_since"] == local(started + WINDOW)
    waiting_until = dt_util.parse_datetime(appliance_rows(status)[0]["waiting_until"])
    assert (waiting_until - started - WINDOW).total_seconds() == 75
    assert appliance_rows(status)[0]["waiting_ends_at"] == local(started + 3 * WINDOW)
    assert appliance_rows(status)[1]["waiting_until"] is None


async def test_status_follows_start_and_stop_from_the_panel_and_the_switch(hass: HomeAssistant, entry: MockConfigEntry, hass_ws_client: WebSocketGenerator) -> None:
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
    """Whether each charger is activated, with its details, and deactivated while the configuration is incomplete and the regulation stopped."""
    config["charger_groups"] = [
        {
            "id": "g1",
            "name": "EV chargers",
            "chargers": [
                {
                    "id": "c1",
                    "on_off_entity": "input_boolean.charger",
                    "set_current": {
                        "mode": "custom",
                        "action": [{"action": "number.set_value"}],
                    },
                    "charging_power": {
                        "type": "power_sensor",
                        "value": "sensor.charger_power",
                    },
                }
            ],
        }
    ]
    config["priority"].append({"type": "charger_group", "group_id": "g1"})
    hass.states.async_set("sensor.charger_power", "3.7", {"unit_of_measurement": "kW"})
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    status = await subscribe_status(client)

    group = status["priority"][2]
    assert (group["type"], group["id"], group["name"]) == (
        "charger_group",
        "g1",
        "EV chargers",
    )
    assert group["chargers"] == [
        {
            "id": "c1",
            "name": "input_boolean.charger",
            "state": "stopped",
            "activated": False,
            "current_a": None,
            "power_w": 3700.0,
            "bypassed": False,
            "starting_until": None,
            "charging": False,
            "waiting_since": None,
            "waiting_until": None,
            "waiting_ends_at": None,
            "power_to_free_w": None,
        }
    ]


async def test_status_shows_the_display_values_of_an_appliance(
    hass: HomeAssistant,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """A sensor gives its own unit, a template the unit of Home Assistant, and no valid value gives nothing."""
    config["appliances"][0]["display_power"] = {"type": "power_sensor", "value": "sensor.heater_power"}
    config["appliances"][0]["display_temperature"] = {"type": "temperature_sensor", "value": "sensor.heater_temperature"}
    config["appliances"][1]["display_power"] = {"type": "template", "value": "{{ 'off' }}"}
    config["appliances"][1]["display_temperature"] = {"type": "template", "value": "{{ 21.5 }}"}
    hass.states.async_set("sensor.heater_power", "1950")
    hass.states.async_set("sensor.heater_temperature", "140", {"unit_of_measurement": "°F"})
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    status = await subscribe_status(client)

    rows = [(row["power_w"], row["temperature"]) for row in status["priority"]]
    assert rows == [(1950.0, {"value": 140.0, "unit": "°F"}), (None, {"value": 21.5, "unit": "°C"})]


def charger(charger_id: str, **settings: Any) -> dict[str, Any]:
    return {
        "id": charger_id,
        "device_id": f"{charger_id}_device",
        "on_off_entity": f"input_boolean.{charger_id}",
        "set_current": {"mode": "custom", "action": [{"action": "number.set_value"}]},
        "car_connected": {"type": "entity", "value": f"binary_sensor.{charger_id}_car"},
        "charging_power": {
            "type": "power_sensor",
            "value": f"sensor.{charger_id}_power",
        },
        **settings,
    }


async def test_status_shows_the_power_to_free_on_the_row_of_the_next_step(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """The first ampere step of c1 needs its power at minimum current, 4157 W, free; the appliances below wait for it."""
    config["charger_groups"] = [{"id": "g1", "name": "EV chargers", "chargers": [charger("c1")]}]
    config["priority"].insert(0, {"type": "charger_group", "group_id": "g1"})
    hass.states.async_set("binary_sensor.c1_car", "on")
    hass.states.async_set("sensor.c1_power", "0")
    set_power(hass, "9000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    await subscribe_status(client)

    await advance(hass, freezer)
    status = await next_status(client)

    assert status["priority"][0]["chargers"][0]["power_to_free_w"] == pytest.approx(3157)
    assert [row["power_to_free_w"] for row in appliance_rows(status)] == [None, None]


async def test_status_shows_the_power_to_free_of_an_appliance_within_the_turn_on_margin(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    set_power(hass, "9950")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    await subscribe_status(client)

    await advance(hass, freezer)
    status = await next_status(client)

    assert [row["power_to_free_w"] for row in appliance_rows(status)] == [pytest.approx(50), None]


async def test_status_shows_the_chargers_in_the_current_priority(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """With dynamic charging order a bypassed charger is shown last."""
    config["charger_groups"] = [
        {
            "id": "g1",
            "name": "EV chargers",
            "dynamic_order": True,
            "chargers": [charger("c1"), charger("c2")],
        }
    ]
    config["priority"].append({"type": "charger_group", "group_id": "g1"})
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

    assert [(item["id"], item["state"], item["bypassed"]) for item in status["priority"][-1]["chargers"]] == [("c2", "excluded", False), ("c1", "no_car", True)]


async def test_status_places_charger_groups_among_the_current_variants(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """A group moves when a variant moves an appliance above it."""
    config["charger_groups"] = [
        {
            "id": "g1",
            "name": "EV chargers",
            "one_at_a_time": False,
            "chargers": [charger("c1")],
        }
    ]
    config["charger_groups"] += [
        {
            "id": "g2",
            "name": "Cabin",
            "one_at_a_time": False,
            "chargers": [charger("c2")],
        },
    ]
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
        {"type": "charger_group", "group_id": "g1"},
        {"type": "appliance", "appliance_id": "b", "variant_id": None},
        {"type": "charger_group", "group_id": "g2"},
    ]
    for charger_id in ("c1", "c2"):
        hass.states.async_set(f"binary_sensor.{charger_id}_car", "on")
        hass.states.async_set(f"sensor.{charger_id}_power", "0")
    set_power(hass, "1000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)
    status = await subscribe_status(client)
    assert row_ids(status) == ["a", "g1", "b", "g2"]

    await advance(hass, freezer)
    status = await next_status(client)

    assert row_ids(status) == ["b", "a", "g1", "g2"]


def row_ids(status: dict[str, Any]) -> list[str]:
    return [row["id"] for row in status["priority"]]


def appliance_rows(status: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in status["priority"] if row["type"] == "appliance"]


SHORT_WINDOW = timedelta(seconds=10)


def with_short_window(config: dict[str, Any]) -> None:
    """Report every 10 seconds, since the heartbeat of the WebSocket closes a connection when time moves on by a minute twice."""
    config["general"]["power_sensor_interval_s"] = 10


async def subscribe_diagnostics(client) -> dict[str, Any]:
    """Subscribe to what the diagnostics page shows and return the first event."""
    response = await send(client, "kraftvakt/diagnostics/subscribe")
    assert response["success"]
    return await next_status(client)


async def test_diagnostics_are_sent_at_once_and_then_only_what_is_new(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    lights: list[str],
    hass_ws_client: WebSocketGenerator,
) -> None:
    started = dt_util.utcnow()
    with_short_window(config)
    set_power(hass, "2000")
    await setup_entry(hass)
    client = await hass_ws_client(hass)

    diagnostics = await subscribe_diagnostics(client)

    assert diagnostics == {
        "started_at": local(started),
        "power_sensor": {
            "valid": True,
            "update_interval_s": 10,
            "reported_interval_s": None,
            "last_missed_windows": None,
        },
        "queued_commands": 0,
        "repeats_due_at": {
            "appliances": {"a": local(started + timedelta(minutes=30)), "b": local(started + timedelta(minutes=30))},
            "chargers": {},
        },
        "measurements": {"replace": True, "kept_from": local(started), "items": [{"start": local(started), "power_w": 2000}]},
        "decisions": {"replace": True, "kept_from": None, "items": []},
        "failed_actions": [],
    }

    await advance(hass, freezer, SHORT_WINDOW)
    diagnostics = await next_status(client)

    decision = {
        "time": local(started + SHORT_WINDOW),
        "regulation_average_w": 2000,
        "tariff_average_w": 2000,
        "power_sensor_valid": True,
        "safe_state": False,
        "penalty_active": False,
        "overconsumption_wh": 0,
        "waiting": None,
        "commands": [{"command": "TurnOnAppliance", "appliance_id": "a", "variant_id": None}],
    }
    assert diagnostics["decisions"] == {"replace": False, "kept_from": local(started + SHORT_WINDOW), "items": [decision]}
    assert diagnostics["measurements"] == {"replace": False, "kept_from": local(started), "items": [{"start": local(started), "power_w": 2000}]}
    assert diagnostics["repeats_due_at"]["appliances"]["a"] == local(started + SHORT_WINDOW + timedelta(minutes=30))

    set_power(hass, "3000")
    await advance(hass, freezer, SHORT_WINDOW)
    await next_status(client)
    set_power(hass, "4000")
    await advance(hass, freezer, SHORT_WINDOW)
    diagnostics = await next_status(client)

    assert [item["time"] for item in diagnostics["decisions"]["items"]] == [local(started + 3 * SHORT_WINDOW)]
    assert diagnostics["decisions"]["kept_from"] == local(started + SHORT_WINDOW)
    assert diagnostics["measurements"]["items"] == [
        {"start": local(started), "power_w": 2000},
        {"start": local(started + SHORT_WINDOW), "power_w": 3000},
        {"start": local(started + 2 * SHORT_WINDOW), "power_w": 4000},
    ]


async def test_diagnostics_show_failed_actions_and_the_stopped_regulation(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config: dict[str, Any],
    lights: list[str],
    hass_ws_client: WebSocketGenerator,
) -> None:
    def fail(call) -> None:
        raise HomeAssistantError("Light is gone")

    hass.services.async_register("light", "turn_on", fail)
    with_short_window(config)
    set_power(hass, "2000")
    entry = await setup_entry(hass)
    subscriber = await hass_ws_client(hass)
    commander = await hass_ws_client(hass)
    await subscribe_diagnostics(subscriber)

    await advance(hass, freezer, SHORT_WINDOW)
    diagnostics = await next_status(subscriber)
    while not diagnostics["failed_actions"]:
        diagnostics = await next_status(subscriber)

    assert diagnostics["failed_actions"] == [{"time": local(dt_util.utcnow()), "action": "turn_on light.a", "error": "Light is gone"}]

    await set_running(commander, False)
    diagnostics = await next_status(subscriber)
    assert diagnostics["started_at"] is None
    assert diagnostics["repeats_due_at"] == {"appliances": {}, "chargers": {}}
    assert len(diagnostics["decisions"]["items"]) == 0
    assert diagnostics["decisions"]["kept_from"] is not None

    assert await hass.config_entries.async_reload(entry.entry_id)
    diagnostics = await next_status(subscriber)
    assert diagnostics["decisions"] == {"replace": True, "kept_from": None, "items": []}
    assert diagnostics["measurements"]["replace"]
