"""The diagnostics hold the configuration, the status and every piece of state Kraftvakt keeps in memory."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, EVENT_HOMEASSISTANT_STARTED, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import CoreState, HomeAssistant, ServiceCall
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
CHARGER_POWER = "sensor.charger_power"
CAR_CONNECTED = "binary_sensor.car"
WINDOW = timedelta(seconds=60)
DEFAULT = {"mode": "default"}


@pytest.fixture
def config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        "general": {"power_sensor": POWER_SENSOR, "regulation_window_updates": 1, "power_sensor_interval_s": 60, "wait_at_limit_s": 0, "penalty_threshold_w": 0},
        "appliances": [
            {
                "id": "a",
                "entity_id": "light.a",
                "turn_on": DEFAULT,
                "turn_off": DEFAULT,
                "variants": [{"id": "v", "label": "Morning", "condition": {"type": "entity", "value": "input_boolean.morning"}}],
            }
        ],
        "priority": [
            {"type": "appliance", "appliance_id": "a", "variant_id": "v"},
            {"type": "charger_group", "group_id": "g"},
            {"type": "appliance", "appliance_id": "a", "variant_id": None},
        ],
        "charger_groups": [
            {
                "id": "g",
                "name": "Garage",
                "chargers": [
                    {
                        "id": "c",
                        "device_id": "device",
                        "on_off_entity": "input_boolean.charger",
                        "set_current": {"mode": "entity", "entity_id": "input_number.current"},
                        "min_current_a": 6,
                        "max_current_a": 7,
                        "min_current_power_w": 1000,
                        "car_connected": {"type": "entity", "value": CAR_CONNECTED},
                        "charging_power": {"type": "power_sensor", "value": CHARGER_POWER},
                    }
                ],
            }
        ],
    }
    hass_storage[STORAGE_KEY] = {"version": STORAGE_VERSION, "minor_version": 1, "key": STORAGE_KEY, "data": data}
    return data


@pytest.fixture(autouse=True)
def services(hass: HomeAssistant) -> None:
    for domain, service in (("light", "turn_on"), ("light", "turn_off"), ("input_boolean", "turn_on"), ("input_boolean", "turn_off"), ("input_number", "set_value")):
        hass.services.async_register(domain, service, lambda call: None)


def set_power(hass: HomeAssistant, entity_id: str, watt: str) -> None:
    hass.states.async_set(entity_id, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


async def setup(hass: HomeAssistant, power_w: str = "2000") -> MockConfigEntry:
    assert await async_setup_component(hass, "diagnostics", {})
    set_power(hass, POWER_SENSOR, power_w)
    set_power(hass, CHARGER_POWER, "0")
    hass.states.async_set("input_boolean.morning", STATE_ON)
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    return entry


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, windows: int = 1) -> None:
    for _ in range(windows):
        freezer.tick(WINDOW)
        for sensor in (POWER_SENSOR, CHARGER_POWER):
            if state := hass.states.get(sensor):
                hass.states.async_set(sensor, state.state, state.attributes)
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)


def local(moment: datetime) -> str:
    return dt_util.as_local(moment).isoformat()


async def test_the_diagnostics_hold_the_state_of_a_running_regulation(hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, config) -> None:
    started_at = dt_util.utcnow()
    entry = await setup(hass)
    await advance(hass, freezer, 2)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    now = dt_util.utcnow()
    assert diagnostics["runtime"] == {"waiting_for_home_assistant_start": False, "actions_running": False}
    engine = diagnostics["engine"]
    assert engine["running"]
    assert engine["power_limit_w"] == 10000
    assert engine["waiting_curve"]["steepness"] == 6
    assert engine["appliance_growth"] == {"increment": 0, "cap": 0}
    state = engine["state"]
    assert state["started_at"] == local(started_at)
    assert state["appliances_on"] == ["a"]
    assert state["current_variants"] == {"a": "v"}
    assert state["waiting"] is None
    assert state["power_to_free"] is None
    assert state["settling_since"] == {"ApplianceStepKey(appliance_id='a')": local(now - WINDOW), "AmpereStepKey(charger_id='c', index=0)": local(now)}
    assert state["repeats"] == {"last_key": {"charger_id": "c", "index": 0}, "repeats": 0}
    assert state["penalty"] == {"overconsuming": False, "overconsumption_wh": 0, "active": False, "recovery_started": False}
    assert not state["safe_state"]
    assert state["charging_groups"]["g"] | {"last_readings": None} == {
        "priority": ["c"],
        "ampere_steps_on": {"c": 1},
        "activated_at": {"c": local(now)},
        "bypassed": [],
        "charging": [],
        "held_at_min": ["c"],
        "may_charge": ["c"],
        "starting": {},
        "waiting": [],
        "last_readings": None,
        "last_permissions": {"c": "window"},
        "measured_power_per_ampere_w": {},
        "last_decision": local(now),
    }
    assert state["charging_groups"]["g"]["last_readings"]["c"]["car_connected"] is True
    assert state["appliances_commanded_at"] == {"a": local(now - WINDOW)}
    assert state["chargers_commanded_at"] == {"c": local(now)}
    measurement = diagnostics["measurement"]
    assert measurement["started_at"] == local(started_at)
    assert measurement["power_sensor"] == POWER_SENSOR
    assert measurement["following_power_sensor"]
    assert measurement["silence_timer_set"]
    assert not measurement["clock_close_scheduled"]
    assert not measurement["reading_history"]
    assert measurement["latest_averages"] == {
        "start": local(now - WINDOW),
        "end": local(now),
        "regulation_average_w": 2000,
        "tariff_average_w": 2000,
        "sensor_valid": True,
    }
    assert len(measurement["recent_windows"]) == 2
    assert measurement["averager"] == {
        "window_start": local(now),
        "updates_per_window": 1,
        "next_updates_per_window": 1,
        "updates": 0,
        "latest_measurement_at": local(now),
        "sensor_valid": True,
        "consecutive_invalid_closes": 0,
        "last_missed_windows": None,
        "power_steps": [{"start": local(started_at), "power_w": 2000}],
    }
    assert diagnostics["decision_clock"] == {"windows_since_decision": []}
    assert diagnostics["action_runner"]["queued_commands"] == []
    assert {"owner": "a", "kind": "turn_on"} in diagnostics["action_runner"]["scripts"]
    assert diagnostics["settings"] == {
        "appliance_switches": {"a": {"excluded": False}},
        "charger_switches": {"c": {"excluded": False, "window_override": False}},
        "armed_overrides": [],
    }


async def test_a_stopped_regulation_keeps_no_state_but_the_measurement_goes_on(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, config
) -> None:
    entry = await setup(hass)
    await advance(hass, freezer)
    entry.runtime_data.async_stop_regulation()
    await advance(hass, freezer)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    state = diagnostics["engine"]["state"]
    assert not diagnostics["engine"]["running"]
    assert state["started_at"] is None
    assert state["appliances_on"] == []
    assert state["appliances_commanded_at"] == {}
    assert diagnostics["measurement"]["latest_averages"]["end"] == local(dt_util.utcnow())
    assert diagnostics["decision_clock"] == {"windows_since_decision": []}


async def test_the_diagnostics_show_the_safe_state_and_the_lost_power_sensor(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, config
) -> None:
    entry = await setup(hass)
    hass.states.async_set(POWER_SENSOR, STATE_UNAVAILABLE)
    await advance(hass, freezer, 2)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert diagnostics["engine"]["state"]["safe_state"]
    averager = diagnostics["measurement"]["averager"]
    assert not averager["sensor_valid"]
    assert averager["consecutive_invalid_closes"] == 2
    assert diagnostics["measurement"]["latest_averages"]["regulation_average_w"] is None


async def test_the_diagnostics_show_the_penalty(hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, config) -> None:
    entry = await setup(hass, power_w="20000")
    await advance(hass, freezer, 2)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    assert diagnostics["engine"]["state"]["penalty"] == {
        "overconsuming": True,
        "overconsumption_wh": pytest.approx(10000 * 60 / 3600),
        "active": True,
        "recovery_started": False,
    }


async def test_the_diagnostics_show_the_commands_that_wait_for_an_action_that_runs(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, config
) -> None:
    released = asyncio.Event()

    async def turn_on_slowly(call: ServiceCall) -> None:
        await released.wait()

    hass.services.async_register("light", "turn_on", turn_on_slowly)
    config["general"]["action_timeout_s"] = 300
    entry = await setup(hass)
    client = await hass_client()
    for _ in range(2):
        freezer.tick(WINDOW)
        set_power(hass, POWER_SENSOR, "2000")
        async_fire_time_changed(hass)
        for _ in range(20):
            await asyncio.sleep(0)

    # The harness waits for every task before it fetches the diagnostics, so they are fetched here.
    diagnostics = (await (await client.get(f"/api/diagnostics/config_entry/{entry.entry_id}")).json())["data"]

    released.set()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert diagnostics["runtime"]["actions_running"]
    assert diagnostics["action_runner"]["waiting_for_lock"]
    assert diagnostics["action_runner"]["queued_commands"] == [
        {"command": "SetChargingCurrent", "charger_id": "c", "current_a": 6},
        {"command": "ActivateCharger", "charger_id": "c"},
    ]


async def test_the_diagnostics_tell_when_the_regulation_waits_for_home_assistant_to_start(hass: HomeAssistant, hass_client: ClientSessionGenerator, config) -> None:
    hass.set_state(CoreState.starting)
    entry = await setup(hass)

    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)

    hass.set_state(CoreState.running)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert diagnostics["runtime"]["waiting_for_home_assistant_start"]
    assert not diagnostics["engine"]["running"]
