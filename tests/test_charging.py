"""End-to-end tests of EV charging and the charger switches in Home Assistant.

They set the power sensors, move the time forward and check the actions that
reach the charger.
"""

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    EntityCategory,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt.config_model import Charger, SwitchedBy
from custom_components.kraftvakt.config_reader import (
    read_config,
)
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.entity import item_name
from custom_components.kraftvakt.regulation.charging import ChargerState
from custom_components.kraftvakt.status import status_snapshot
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
CHARGER = "input_boolean.charger"
CHARGER_POWER = "sensor.charger_power"
CAR_CONNECTED = "binary_sensor.charger_car"
WINDOW = timedelta(seconds=60)
OSLO = ZoneInfo("Europe/Oslo")


def charger_data(charger_id: str = "c1", entity_id: str = CHARGER) -> dict[str, Any]:
    return {
        "id": charger_id,
        "device_id": f"{charger_id}_device",
        "switched_by": "on_off_entity",
        "on_off_entity": entity_id,
        "set_current": {
            "mode": "custom",
            "action": [
                {
                    "action": "input_number.set_value",
                    "target": {"entity_id": "input_number.charger_current"},
                    "data": {"value": "{{ current }}"},
                }
            ],
        },
        "min_current_a": 6,
        "max_current_a": 8,
        "car_connected": {"type": "entity", "value": CAR_CONNECTED},
        "charging_power": {"type": "power_sensor", "value": CHARGER_POWER},
        "min_current_power_w": 4000,
        "start_delay_s": 0,
    }


@pytest.fixture
def config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a complete configuration with one charger; tests may change it."""
    data: dict[str, Any] = {
        "general": {
            "power_sensor": POWER_SENSOR,
            "power_limit_w": 10000,
            "regulation_window_updates": 1,
            "power_sensor_interval_s": 60,
            "wait_at_limit_s": 0,
            "penalty_threshold_w": 1000,
        },
        "appliances": [],
        "priority": [{"type": "charger_group", "group_id": "g1"}],
        "charger_groups": [
            {
                "id": "g1",
                "name": "EV chargers",
                "one_at_a_time": False,
                "chargers": [charger_data()],
            }
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
    """Record the actions that reach the charger, in order."""
    recorded: list[str] = []

    def record_switch(call: ServiceCall) -> None:
        for entity_id in call.data["entity_id"]:
            recorded.append(f"{call.service.removeprefix('turn_')} {entity_id}")

    def record_current(call: ServiceCall) -> None:
        recorded.append(f"current {call.data['value']}")

    hass.services.async_register("input_boolean", "turn_on", record_switch)
    hass.services.async_register("input_boolean", "turn_off", record_switch)
    hass.services.async_register("input_number", "set_value", record_current)
    return recorded


@pytest.fixture
async def setup_kraftvakt(hass: HomeAssistant, config: dict[str, Any]):
    async def setup() -> MockConfigEntry:
        hass.states.async_set(CHARGER, STATE_OFF, {ATTR_FRIENDLY_NAME: "Garage"})
        if hass.states.get(CAR_CONNECTED) is None:
            hass.states.async_set(CAR_CONNECTED, STATE_ON)
        set_power(hass, POWER_SENSOR, "2000")
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        return entry

    return setup


def set_power(hass: HomeAssistant, entity_id: str, watt: str) -> None:
    hass.states.async_set(entity_id, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


async def advance(hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta = WINDOW) -> None:
    """Move time on, with the power sensors reporting as a HAN reader does."""
    freezer.tick(delta)
    for sensor in (POWER_SENSOR, CHARGER_POWER):
        if state := hass.states.get(sensor):
            hass.states.async_set(sensor, state.state, state.attributes)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


async def advance_windows(hass: HomeAssistant, freezer: FrozenDateTimeFactory, count: int) -> None:
    """Close `count` windows, one at a time, since each schedules the next."""
    for _ in range(count):
        await advance(hass, freezer)


def switch_id(hass: HomeAssistant, charger_id: str, setting: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("switch", DOMAIN, f"charger_{charger_id}_{setting}")


def switch_state(hass: HomeAssistant, charger_id: str, setting: str) -> str:
    entity_id = switch_id(hass, charger_id, setting)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


async def use_switch(hass: HomeAssistant, charger_id: str, setting: str, service: str) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": switch_id(hass, charger_id, setting)},
        blocking=True,
    )


def allowed_sensor_id(hass: HomeAssistant, charger_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("binary_sensor", DOMAIN, f"charger_{charger_id}_allowed_to_charge")


def allowed_sensor_state(hass: HomeAssistant, charger_id: str) -> str:
    entity_id = allowed_sensor_id(hass, charger_id)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


def steps_switched_on(hass: HomeAssistant) -> str:
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, "regulation_steps_on")
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


def stored_switches(hass_storage: dict[str, Any]) -> dict[str, Any]:
    return hass_storage[STORAGE_KEY]["data"]["charger_switches"]


async def test_charger_current_follows_the_free_power(hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt) -> None:
    """The current is set before (de)activating.

    Above the limit, a car that draws 4100 W at 8 A, 512.5 W per ampere, frees the 1000 W with two amperes, at once.
    """
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    assert actions == ["current 6", f"off {CHARGER}"]
    actions.clear()

    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]
    set_power(hass, CHARGER_POWER, "4100")
    await advance(hass, freezer)
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}", "current 7", "current 8"]
    assert steps_switched_on(hass) == "3"
    actions.clear()

    set_power(hass, POWER_SENSOR, "11000")
    await advance(hass, freezer)
    assert actions == ["current 6"]
    assert steps_switched_on(hass) == "1"


async def test_ampere_taken_back_above_the_limit_is_damped_and_shown_as_waiting(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The ampere comes back at the first decision two minutes after it was taken back, though it fits at once."""
    config["general"]["ampere_damping_s"] = 120
    set_power(hass, CHARGER_POWER, "4100")
    entry = await setup_kraftvakt()
    await advance_windows(hass, freezer, 3)
    set_power(hass, POWER_SENSOR, "10500")
    await advance(hass, freezer)
    taken_back_at = dt_util.utcnow()
    assert actions[-1] == "current 7"
    actions.clear()

    set_power(hass, POWER_SENSOR, "9000")
    await advance(hass, freezer)
    row = status_snapshot(hass, entry.runtime_data)["priority"][0]["chargers"][0]
    assert row["waiting_since"] == dt_util.as_local(taken_back_at).isoformat()
    assert row["waiting_until"] == row["waiting_ends_at"] == dt_util.as_local(taken_back_at + timedelta(seconds=120)).isoformat()
    assert hass.states.get("sensor.kraftvakt_waiting_time_remaining").state == "60"
    await advance(hass, freezer)
    assert actions == ["current 8"]
    assert status_snapshot(hass, entry.runtime_data)["priority"][0]["chargers"][0]["waiting_since"] is None


async def test_charger_activated_again_waits_the_waiting_time_for_ev_chargers_and_shows_it(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Deactivated above the limit, it waits twice the waiting time at the limit by the curve before it is activated again: 30 s at 5000 W with its own 2000 W."""
    config["general"]["wait_at_limit_s"] = 60
    config["charger_groups"][0]["chargers"][0]["min_current_power_w"] = 2000
    set_power(hass, CHARGER_POWER, "4100")
    entry = await setup_kraftvakt()
    await advance(hass, freezer)
    set_power(hass, POWER_SENSOR, "20000")
    await advance(hass, freezer)
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]
    actions.clear()

    set_power(hass, POWER_SENSOR, "5000")
    await advance(hass, freezer)
    waiting_since = dt_util.utcnow()
    assert actions == []
    row = status_snapshot(hass, entry.runtime_data)["priority"][0]["chargers"][0]
    assert row["waiting_since"] == dt_util.as_local(waiting_since).isoformat()
    assert row["waiting_until"] == dt_util.as_local(waiting_since + timedelta(seconds=30)).isoformat()
    assert row["waiting_reason"] == "waiting_time"
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]


async def test_charger_switched_by_its_current_is_set_to_0_a_instead_of_deactivated(hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, config, setup_kraftvakt) -> None:
    """Its on/off entity is kept but never switched."""
    config["charger_groups"][0]["chargers"][0] |= {"switched_by": "current"}
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    assert actions == ["current 0"]
    actions.clear()

    await advance(hass, freezer)
    set_power(hass, CHARGER_POWER, "4100")
    await advance(hass, freezer)
    set_power(hass, POWER_SENSOR, "11000")
    await advance_windows(hass, freezer, 2)

    assert actions == ["current 6", "current 7", "current 0"]


@pytest.mark.parametrize("car_state", [STATE_OFF, STATE_UNAVAILABLE])
async def test_charger_without_car_is_not_activated(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    car_state: str,
) -> None:
    """Only evidence of a car counts as connected."""
    set_power(hass, CHARGER_POWER, "0")
    hass.states.async_set(CAR_CONNECTED, car_state)
    entry = await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == []
    assert entry.runtime_data.chargers["c1"].bypassed

    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]


@pytest.mark.parametrize(
    ("field", "condition", "entity_id", "idle", "charging", "attributes"),
    [
        ("charging_power", {"type": "power_sensor", "value": CHARGER_POWER}, CHARGER_POWER, "0.1", "0.2", {ATTR_UNIT_OF_MEASUREMENT: "kW"}),
        ("charging_power", {"type": "template", "value": "{{ states('sensor.charger_kw') | float(0) * 1000 }}"}, "sensor.charger_kw", "0.1", "0.2", {}),
        ("actively_charging", {"type": "entity", "value": "binary_sensor.charger_charging"}, "binary_sensor.charger_charging", STATE_OFF, STATE_ON, {}),
        ("actively_charging", {"type": "state", "value": "sensor.charger_status", "states": ["charging"]}, "sensor.charger_status", "connected", "charging", {}),
        (
            "actively_charging",
            {"type": "state", "value": "sensor.charger_status", "states": ["connected", "disconnected"], "states_are_true": False},
            "sensor.charger_status",
            "connected",
            "charging",
            {},
        ),
        ("actively_charging", {"type": "template", "value": "{{ is_state('sensor.charger_status', 'charging') }}"}, "sensor.charger_status", "connected", "charging", {}),
    ],
)
async def test_actively_charging_from_the_charging_power_or_the_charging_on_off(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    field: str,
    condition: dict[str, Any],
    entity_id: str,
    idle: str,
    charging: str,
    attributes: dict[str, str],
) -> None:
    """Above 100 W counts as charging, and a charging power template gives W. A car that draws less than half of the power at minimum current gets no more current."""
    charger = config["charger_groups"][0]["chargers"][0]
    charger[field] = condition
    set_power(hass, CHARGER_POWER, "0")
    hass.states.async_set(entity_id, idle, attributes)
    entry = await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]
    await advance(hass, freezer)
    assert not entry.runtime_data.chargers["c1"].charging

    hass.states.async_set(entity_id, charging, attributes)
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert entry.runtime_data.chargers["c1"].charging
    assert actions == ["current 6", f"on {CHARGER}"]


@pytest.mark.parametrize(
    ("field", "condition"),
    [
        ("charging_power", {"type": "power_sensor", "value": CHARGER_POWER}),
        ("charging_power", {"type": "template", "value": "{{ states('sensor.gone') }}"}),
        ("charging_power", {"type": "template", "value": "{{ true }}"}),
        ("actively_charging", {"type": "entity", "value": "binary_sensor.charger_charging"}),
        ("actively_charging", {"type": "state", "value": "binary_sensor.charger_charging", "states": ["off"], "states_are_true": False}),
        ("actively_charging", {"type": "template", "value": "{{ states('sensor.gone') | float > 0 }}"}),
    ],
)
async def test_charger_without_evidence_counts_as_not_charging(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    field: str,
    condition: dict[str, Any],
) -> None:
    """It stays activated at its minimum current, since Kraftvakt never guesses that a car is done."""
    charger = config["charger_groups"][0]["chargers"][0]
    charger[field] = condition
    hass.states.async_set(CHARGER_POWER, STATE_UNAVAILABLE)
    hass.states.async_set("binary_sensor.charger_charging", STATE_UNAVAILABLE)
    entry = await setup_kraftvakt()
    actions.clear()

    await advance_windows(hass, freezer, 5)
    assert actions == ["current 6", f"on {CHARGER}"]
    assert entry.runtime_data.chargers["c1"].state is ChargerState.ACTIVATED


async def test_car_gets_more_current_only_while_it_draws_half_of_its_power_at_minimum_current(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, config, setup_kraftvakt
) -> None:
    """Car charging may tell that the car charges, but only the charging power tells that it uses the current it has."""
    charger = config["charger_groups"][0]["chargers"][0]
    charger["actively_charging"] = {"type": "entity", "value": "binary_sensor.charger_charging"}
    hass.states.async_set("binary_sensor.charger_charging", STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    actions.clear()
    await advance(hass, freezer)

    hass.states.async_set("binary_sensor.charger_charging", STATE_ON)
    await advance(hass, freezer)
    set_power(hass, CHARGER_POWER, "1900")
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]

    set_power(hass, CHARGER_POWER, "2000")
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}", "current 7"]

    set_power(hass, CHARGER_POWER, "1900")
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}", "current 7", "current 6"]


async def test_one_charger_at_a_time_lets_every_car_wait_at_the_minimum_until_one_draws_power(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, config, setup_kraftvakt
) -> None:
    """The car that draws power gets more current. A car higher up that draws takes over, and the charger below it is deactivated at once."""
    carport = charger_data("c2", "input_boolean.carport") | {
        "car_connected": {"type": "entity", "value": "binary_sensor.carport_car"},
        "charging_power": {"type": "power_sensor", "value": "sensor.carport_power"},
    }
    config["charger_groups"][0] |= {"one_at_a_time": True, "chargers": [charger_data(), carport]}
    hass.states.async_set("input_boolean.carport", STATE_OFF, {ATTR_FRIENDLY_NAME: "Carport"})
    hass.states.async_set("binary_sensor.carport_car", STATE_ON)
    set_power(hass, CHARGER_POWER, "0")
    set_power(hass, "sensor.carport_power", "0")
    runtime = (await setup_kraftvakt()).runtime_data
    actions.clear()

    await advance_windows(hass, freezer, 3)
    assert actions == ["current 6", f"on {CHARGER}", "current 6", "on input_boolean.carport"]
    assert runtime.chargers["c1"].state is ChargerState.ACTIVATED

    set_power(hass, "sensor.carport_power", "4100")
    await advance_windows(hass, freezer, 2)
    assert (runtime.chargers["c1"].current_a, runtime.chargers["c2"].current_a) == (6, 8)

    set_power(hass, CHARGER_POWER, "4100")
    actions.clear()
    await advance(hass, freezer)
    assert actions == ["current 6", "off input_boolean.carport", "current 7"]
    assert runtime.chargers["c2"].state is ChargerState.QUEUED


async def test_excluded_switch_stops_charging_and_is_saved(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    actions,
    setup_kraftvakt,
) -> None:
    """It takes effect at the next decision."""
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await advance(hass, freezer)
    assert switch_state(hass, "c1", "excluded") == STATE_OFF
    actions.clear()

    await use_switch(hass, "c1", "excluded", "turn_on")

    assert switch_state(hass, "c1", "excluded") == STATE_ON
    assert stored_switches(hass_storage)["c1"]["excluded"] is True
    assert actions == []
    await advance(hass, freezer)
    assert actions == ["current 6", f"off {CHARGER}"]
    await advance(hass, freezer)
    assert actions == ["current 6", f"off {CHARGER}"]

    await use_switch(hass, "c1", "excluded", "turn_off")
    await advance(hass, freezer)
    assert actions[2:] == ["current 6", f"on {CHARGER}"]


async def test_charger_current_is_repeated_until_the_charger_is_excluded(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config,
    actions,
    setup_kraftvakt,
) -> None:
    config["general"]["command_repeat_interval_min"] = 10
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await advance_windows(hass, freezer, 3)
    assert actions[-1] == "current 8"
    actions.clear()

    await advance_windows(hass, freezer, 9)
    assert actions == []
    await advance(hass, freezer)
    assert actions == ["current 8"]

    await use_switch(hass, "c1", "excluded", "turn_on")
    await advance_windows(hass, freezer, 20)
    assert actions == ["current 8", "current 6", f"off {CHARGER}"]


async def test_cloud_controlled_charger_gets_no_repeated_commands_until_a_car_is_connected(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config,
    actions,
    setup_kraftvakt,
) -> None:
    config["general"]["command_repeat_interval_min"] = 10
    charger = config["charger_groups"][0]["chargers"][0]
    charger["cloud_controlled"] = True
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    actions.clear()

    await advance_windows(hass, freezer, 20)
    assert actions == []

    hass.states.async_set(CAR_CONNECTED, STATE_UNAVAILABLE)
    await advance(hass, freezer)
    assert actions == ["current 6", f"off {CHARGER}"]


async def test_starting_charger_shows_its_start_delay_while_it_holds_back_the_steps_below(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    config,
    actions,
    setup_kraftvakt,
) -> None:
    """The heater below gets the power only when the start delay has ended, since the car does not draw it."""
    config["charger_groups"][0]["chargers"][0]["start_delay_s"] = 180
    config["appliances"] = [{"id": "a", "entity_id": "input_boolean.heater", "turn_on": {"mode": "default"}, "turn_off": {"mode": "default"}}]
    config["priority"].append({"type": "appliance", "appliance_id": "a", "variant_id": None})
    hass.states.async_set("input_boolean.heater", STATE_OFF)
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "0")
    entry = await setup_kraftvakt()
    actions.clear()
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]
    activated_at = dt_util.utcnow()

    await advance_windows(hass, freezer, 2)
    row = status_snapshot(hass, entry.runtime_data)["priority"][0]["chargers"][0]
    assert row["state"] == "starting"
    assert row["starting_until"] == dt_util.as_local(activated_at + timedelta(seconds=180)).isoformat()
    assert row["waiting_since"] == dt_util.as_local(activated_at).isoformat()
    assert row["waiting_until"] == row["starting_until"]
    assert row["waiting_reason"] == "start_delay"
    await advance(hass, freezer)
    assert entry.runtime_data.chargers["c1"].state is ChargerState.ACTIVATED
    assert actions == ["current 6", f"on {CHARGER}", "on input_boolean.heater"]


async def test_charger_with_a_fault_is_deactivated_until_the_fault_clears(hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, config, setup_kraftvakt) -> None:
    """Only evidence is a fault, so an unavailable flag is not."""
    charger = config["charger_groups"][0]["chargers"][0]
    charger["deactivate_on_fault"] = True
    charger["fault_flag"] = {"type": "entity", "value": "binary_sensor.charger_error"}
    hass.states.async_set("binary_sensor.charger_error", STATE_OFF)
    set_power(hass, CHARGER_POWER, "4100")
    entry = await setup_kraftvakt()
    await advance(hass, freezer)
    actions.clear()

    hass.states.async_set("binary_sensor.charger_error", STATE_ON)
    await advance(hass, freezer)
    assert actions == ["current 6", f"off {CHARGER}"]
    assert status_snapshot(hass, entry.runtime_data)["priority"][0]["chargers"][0]["state"] == "fault"
    assert allowed_sensor_state(hass, "c1") == STATE_OFF

    hass.states.async_set("binary_sensor.charger_error", STATE_UNAVAILABLE)
    await advance(hass, freezer)
    assert actions[2:] == ["current 6", f"on {CHARGER}"]
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    hass.states.async_set("binary_sensor.charger_error", STATE_ON)
    await advance(hass, freezer)
    assert actions[4:] == ["current 6", f"off {CHARGER}"]
    assert entry.runtime_data.chargers["c1"].state is ChargerState.FAULT


async def test_fault_flag_is_not_read_while_deactivate_on_fault_is_off(hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, config, setup_kraftvakt) -> None:
    config["charger_groups"][0]["chargers"][0]["fault_flag"] = {"type": "entity", "value": "binary_sensor.charger_error"}
    hass.states.async_set("binary_sensor.charger_error", STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)

    assert actions == ["current 6", f"on {CHARGER}"]


async def advance_until(hass: HomeAssistant, freezer: FrozenDateTimeFactory, local_time: str) -> None:
    """Close windows of ten minutes until the time of day in Oslo."""
    target = datetime.fromisoformat(local_time).replace(tzinfo=OSLO)
    while dt_util.now() < target:
        await advance(hass, freezer, timedelta(minutes=10))


async def test_override_lasts_until_the_car_has_been_disconnected(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Switched on before the car arrives, it outlasts the window and a full car, which stays activated and may heat in the morning."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T18:55:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    await advance_until(hass, freezer, "2026-11-07T20:00")
    await use_switch(hass, "c1", "window_override", "turn_on")
    assert stored_switches(hass_storage)["c1"]["window_override"] is True

    await advance_until(hass, freezer, "2026-11-07T21:00")
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    actions.clear()
    await advance_until(hass, freezer, "2026-11-07T21:30")
    assert actions == ["current 6", f"on {CHARGER}", "current 7", "current 8"]

    await advance_until(hass, freezer, "2026-11-08T05:00")
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    set_power(hass, CHARGER_POWER, "0")
    await advance_until(hass, freezer, "2026-11-08T05:10")
    assert actions[-1] == "current 6"
    actions.clear()

    await advance_until(hass, freezer, "2026-11-08T07:00")
    set_power(hass, CHARGER_POWER, "2500")
    await advance_until(hass, freezer, "2026-11-08T07:20")
    assert "current 7" in actions
    assert f"on {CHARGER}" not in actions
    assert entry_charger_state(hass) is ChargerState.CHARGING
    assert status_snapshot(hass, hass.config_entries.async_entries(DOMAIN)[0].runtime_data)["priority"][0]["chargers"][0]["charging"]
    assert switch_state(hass, "c1", "window_override") == STATE_ON

    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await advance_until(hass, freezer, "2026-11-08T07:40")
    assert switch_state(hass, "c1", "window_override") == STATE_OFF
    assert stored_switches(hass_storage)["c1"]["window_override"] is False
    assert entry_charger_state(hass) is ChargerState.NO_CAR


async def test_override_ends_on_a_disconnect_while_stopped(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The car seen connected is kept over a stop of the regulation."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    await setup_kraftvakt()
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))
    await set_regulation(hass, "turn_off")

    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    await advance(hass, freezer, timedelta(minutes=10))
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    await set_regulation(hass, "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))

    assert switch_state(hass, "c1", "window_override") == STATE_OFF


async def test_override_outlasts_a_car_sensor_without_a_value(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Only a car known to be disconnected, or known to have stopped, ends it."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await use_switch(hass, "c1", "window_override", "turn_on")
    for _ in range(2):
        await advance(hass, freezer, timedelta(minutes=10))

    hass.states.async_set(CAR_CONNECTED, STATE_UNAVAILABLE)
    set_power(hass, CHARGER_POWER, STATE_UNAVAILABLE)
    await advance(hass, freezer, timedelta(minutes=10))
    assert switch_state(hass, "c1", "window_override") == STATE_ON

    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await advance(hass, freezer, timedelta(minutes=10))
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    assert allowed_sensor_state(hass, "c1") == STATE_ON


async def test_override_ends_when_the_car_no_longer_charges(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """A full car ends it at once, so the car heating in the morning does not charge."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T18:55:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "charging_stopped"
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    await advance_until(hass, freezer, "2026-11-07T20:00")
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance_until(hass, freezer, "2026-11-07T21:00")
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await advance_until(hass, freezer, "2026-11-08T05:00")
    assert switch_state(hass, "c1", "window_override") == STATE_ON

    set_power(hass, CHARGER_POWER, "0")
    await advance_until(hass, freezer, "2026-11-08T05:10")
    assert switch_state(hass, "c1", "window_override") == STATE_OFF
    await advance_until(hass, freezer, "2026-11-08T06:10")
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]
    actions.clear()
    set_power(hass, CHARGER_POWER, "2000")
    await advance_until(hass, freezer, "2026-11-08T07:30")
    assert f"on {CHARGER}" not in actions


async def test_override_end_changed_waits_for_its_own_start(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Armed by a connected car, it is not armed for a car that stops charging."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "0")
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))
    assert runtime.settings.override_armed("c1")

    await set_regulation(hass, "turn_off")
    data = deepcopy(config)
    data["charger_groups"][0]["chargers"][0]["override_ends"] = "charging_stopped"
    await runtime.async_save_config(read_config(data))
    await set_regulation(hass, "turn_on")
    for _ in range(5):
        await advance(hass, freezer, timedelta(minutes=10))

    assert switch_state(hass, "c1", "window_override") == STATE_ON


async def test_manual_override_stays_until_switched_off(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Neither a window that starts nor a car that leaves ends it."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "13:00", "end": "14:00"}
    charger["override_ends"] = "manual"
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)

    await advance_until(hass, freezer, "2026-11-08T12:10")
    assert switch_state(hass, "c1", "window_override") == STATE_ON

    actions.clear()
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    await use_switch(hass, "c1", "window_override", "turn_off")
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions == ["current 6", f"off {CHARGER}"]


def entry_charger_state(hass: HomeAssistant) -> ChargerState:
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    return entry.runtime_data.chargers["c1"].state


async def set_regulation(hass: HomeAssistant, service: str) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": "switch.kraftvakt_regulation"},
        blocking=True,
    )


def stored_charge_until_disconnected(hass_storage: dict[str, Any]) -> bool:
    data = hass_storage[STORAGE_KEY]["data"]
    return data["charger_groups"][0]["chargers"][0]["charge_until_disconnected"]


async def test_charger_charges_until_the_car_is_disconnected_when_switched_on(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The switch is saved while the regulation runs and applies at once.

    A car that stops charging after the window keeps its minimum current.
    """
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:50:00+00:00")
    config["charger_groups"][0]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "13:20",
    }
    set_power(hass, CHARGER_POWER, "4100")
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    version = runtime.config_version
    actions.clear()

    await use_switch(hass, "c1", "charge_until_disconnected", "turn_on")
    assert runtime.running
    assert switch_state(hass, "c1", "charge_until_disconnected") == STATE_ON
    assert stored_charge_until_disconnected(hass_storage) is True
    assert runtime.config_version == version + 1
    for _ in range(4):
        await advance(hass, freezer, timedelta(minutes=10))
    assert actions == ["current 6", f"on {CHARGER}", "current 7", "current 8"]
    assert runtime.chargers["c1"].state is ChargerState.CHARGING

    set_power(hass, CHARGER_POWER, "0")
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-1] == "current 6"
    assert runtime.chargers["c1"].state is ChargerState.ACTIVATED

    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]
    actions.clear()
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    for _ in range(3):
        await advance(hass, freezer, timedelta(minutes=10))
    assert f"on {CHARGER}" not in actions
    assert runtime.chargers["c1"].state is ChargerState.OUTSIDE_WINDOW


async def test_charge_until_disconnected_switch_saves_the_configuration_while_stopped(hass: HomeAssistant, hass_storage: dict[str, Any], actions, setup_kraftvakt) -> None:
    """Setting it to what it is already saves nothing."""
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    runtime.async_stop_regulation()
    await use_switch(hass, "c1", "charge_until_disconnected", "turn_on")
    version = runtime.config_version

    await use_switch(hass, "c1", "charge_until_disconnected", "turn_on")
    assert runtime.config_version == version
    await use_switch(hass, "c1", "charge_until_disconnected", "turn_off")

    assert switch_state(hass, "c1", "charge_until_disconnected") == STATE_OFF
    assert stored_charge_until_disconnected(hass_storage) is False
    assert runtime.config.chargers[0].charge_until_disconnected is False
    assert runtime.config_version == version + 1


async def test_allowed_sensor_follows_the_clock_and_the_override(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """It changes at the whole minute, also while the regulation is stopped."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:59:00+00:00")
    config["charger_groups"][0]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "14:00",
    }
    entry = await setup_kraftvakt()
    assert entry.runtime_data.running
    await set_regulation(hass, "turn_off")
    assert allowed_sensor_state(hass, "c1") == STATE_OFF

    await use_switch(hass, "c1", "window_override", "turn_on")
    assert allowed_sensor_state(hass, "c1") == STATE_ON
    await use_switch(hass, "c1", "window_override", "turn_off")
    assert allowed_sensor_state(hass, "c1") == STATE_OFF

    await advance(hass, freezer, timedelta(seconds=59))
    assert allowed_sensor_state(hass, "c1") == STATE_OFF
    await advance(hass, freezer, timedelta(seconds=1))
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    await advance(hass, freezer, timedelta(minutes=60))
    assert allowed_sensor_state(hass, "c1") == STATE_OFF


async def test_allowed_sensor_follows_charging_until_disconnected_and_the_excluded_switch(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """It stays on from the end of the window until a decision finds the car disconnected."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:50:00+00:00")
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "13:00", "end": "13:15"}
    charger["charge_until_disconnected"] = True
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    actions.clear()
    for _ in range(3):
        await advance(hass, freezer, timedelta(minutes=10))
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    await advance(hass, freezer, timedelta(minutes=5))
    assert allowed_sensor_state(hass, "c1") == STATE_ON
    set_power(hass, CHARGER_POWER, "0")
    await advance(hass, freezer, timedelta(minutes=5))
    assert allowed_sensor_state(hass, "c1") == STATE_ON
    assert f"off {CHARGER}" not in actions

    await use_switch(hass, "c1", "excluded", "turn_on")
    assert allowed_sensor_state(hass, "c1") == STATE_OFF
    await use_switch(hass, "c1", "excluded", "turn_off")
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-1] == f"off {CHARGER}"
    assert allowed_sensor_state(hass, "c1") == STATE_OFF
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    await advance(hass, freezer, timedelta(minutes=10))
    assert allowed_sensor_state(hass, "c1") == STATE_OFF


async def test_allowed_sensor_is_on_without_a_window(hass: HomeAssistant, actions, setup_kraftvakt) -> None:
    """Named after the charger."""
    await setup_kraftvakt()

    entity_id = allowed_sensor_id(hass, "c1")
    assert entity_id == "binary_sensor.kraftvakt_charger_garage_allowed_to_charge"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.name == "Kraftvakt Garage allowed to charge"


@pytest.mark.parametrize(
    ("language", "name", "labels"),
    [
        ("en", "Garage state", ["First decision", "Activated", "Charging", "Regulation stopped"]),
        ("nb", "Garage tilstand", ["Første avgjørelse", "Aktivert", "Lader", "Regulering stoppet"]),
    ],
)
async def test_state_sensor_gives_templates_the_label_icon_and_colours_of_the_state(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    setup_kraftvakt,
    language: str,
    name: str,
    labels: list[str],
) -> None:
    """Named after the charger, in the language of Home Assistant, and stopped while the regulation is stopped."""
    await hass.config.async_update(language=language)
    set_power(hass, CHARGER_POWER, "0")
    entry = await setup_kraftvakt()
    entity_id = "sensor.kraftvakt_charger_garage_state"
    template = Template("{{ states(e) }}|{{ state_translated(e) }}|{{ state_attr(e, 'icon') }}|{{ state_attr(e, 'color') }}|{{ state_attr(e, 'badge_color') }}", hass)

    def shown() -> list[str]:
        return template.async_render({"e": entity_id}, parse_result=False).split("|")

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == f"Kraftvakt {name}"
    assert "stopped" in state.attributes["options"]
    assert shown() == ["first_decision", labels[0], "mdi:timer-sand", "grey", "dark-grey"]

    await advance(hass, freezer)
    assert shown() == ["activated", labels[1], "mdi:power-plug", "green", "green"]

    set_power(hass, CHARGER_POWER, "4100")
    await advance(hass, freezer)
    assert shown() == ["charging", labels[2], "mdi:lightning-bolt", "green", "green"]

    entry.runtime_data.async_stop_regulation()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert shown() == ["stopped", labels[3], "mdi:stop-circle-outline", "red", "red"]


async def test_entities_are_grouped_by_entity_category(hass: HomeAssistant, actions, config, setup_kraftvakt) -> None:
    """The switches of appliances and chargers configure them, and the rest are controls, sensors or diagnostics."""
    config["appliances"] = [{"id": "a", "entity_id": "light.heater", "turn_on": {"mode": "default"}, "turn_off": {"mode": "default"}}]
    config["priority"].append({"type": "appliance", "appliance_id": "a", "variant_id": None})
    entry = await setup_kraftvakt()

    categories = {registry_entry.unique_id: registry_entry.entity_category for registry_entry in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
    assert categories == {
        "regulation": None,
        "power_limit": None,
        "regulation_safe_state": None,
        "power_regulation_average": None,
        "power_tariff_average": None,
        "power_free": None,
        "penalty_active": None,
        "penalty_overconsumption": None,
        "regulation_steps_on": EntityCategory.DIAGNOSTIC,
        "waiting_time_remaining": EntityCategory.DIAGNOSTIC,
        "waiting_time_next_turn_on": EntityCategory.DIAGNOSTIC,
        "appliance_a_excluded": EntityCategory.CONFIG,
        "charger_c1_excluded": EntityCategory.CONFIG,
        "charger_c1_window_override": EntityCategory.CONFIG,
        "charger_c1_charge_until_disconnected": EntityCategory.CONFIG,
        "charger_c1_allowed_to_charge": EntityCategory.DIAGNOSTIC,
        "charger_c1_state": EntityCategory.DIAGNOSTIC,
    }


async def test_allowed_sensor_follows_the_configuration_without_reload(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """A new window applies at once, and the sensor goes with its charger."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    runtime.async_stop_regulation()
    data = deepcopy(config)
    data["charger_groups"][0]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "14:00",
    }

    await runtime.async_save_config(read_config(data))
    await hass.async_block_till_done()
    assert allowed_sensor_state(hass, "c1") == STATE_OFF

    hass.states.async_set("input_boolean.carport", STATE_OFF)
    data["charger_groups"][0]["chargers"] = [charger_data("c2", "input_boolean.carport")]
    await runtime.async_save_config(read_config(data))
    await hass.async_block_till_done()

    assert allowed_sensor_id(hass, "c1") is None
    assert allowed_sensor_state(hass, "c2") == STATE_ON


async def test_allowed_sensor_of_removed_charger_is_removed_at_setup(hass: HomeAssistant, actions, setup_kraftvakt) -> None:
    """No orphaned binary sensors remain in the entity registry."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    orphan = registry.async_get_or_create("binary_sensor", DOMAIN, "charger_old_allowed_to_charge", config_entry=entry)
    hass.states.async_set(CHARGER, STATE_OFF, {ATTR_FRIENDLY_NAME: "Garage"})
    set_power(hass, POWER_SENSOR, "2000")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert registry.async_get(orphan.entity_id) is None
    assert allowed_sensor_id(hass, "c1") is not None


async def test_charger_switches_are_kept_over_a_reload(hass: HomeAssistant, hass_storage: dict[str, Any], actions, setup_kraftvakt) -> None:
    """The positions are configuration."""
    entry = await setup_kraftvakt()
    await use_switch(hass, "c1", "excluded", "turn_on")
    await use_switch(hass, "c1", "window_override", "turn_on")

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert switch_state(hass, "c1", "excluded") == STATE_ON
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    assert stored_switches(hass_storage) == {"c1": {"excluded": True, "window_override": True}}


async def test_charger_switches_are_named_after_the_charger(hass: HomeAssistant, actions, setup_kraftvakt) -> None:
    """The name of the charger's entity identifies the switches."""
    await setup_kraftvakt()

    assert switch_id(hass, "c1", "excluded") == "switch.kraftvakt_charger_garage_excluded"
    assert switch_id(hass, "c1", "window_override") == "switch.kraftvakt_charger_garage_window_override"
    excluded = hass.states.get(switch_id(hass, "c1", "excluded") or "")
    override = hass.states.get(switch_id(hass, "c1", "window_override") or "")

    assert excluded is not None
    assert excluded.name == "Kraftvakt Garage excluded from regulation"
    assert override is not None
    assert override.name == "Kraftvakt Garage override charging window"
    until_disconnected = hass.states.get(switch_id(hass, "c1", "charge_until_disconnected") or "")
    assert until_disconnected is not None
    assert until_disconnected.entity_id == "switch.kraftvakt_charger_garage_charge_until_disconnected"
    assert until_disconnected.name == "Kraftvakt Garage charge until car disconnected"


async def test_charger_switches_follow_the_configuration_without_reload(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """Switches are added and removed with the chargers."""
    entry = await setup_kraftvakt()
    await use_switch(hass, "c1", "excluded", "turn_on")
    old_switch = switch_id(hass, "c1", "excluded")
    hass.states.async_set("input_boolean.carport", STATE_OFF)
    data = deepcopy(config)
    data["charger_groups"][0]["chargers"] = [charger_data("c2", "input_boolean.carport")]
    runtime = entry.runtime_data
    runtime.async_stop_regulation()

    await runtime.async_save_config(read_config(data))
    await hass.async_block_till_done()

    assert switch_id(hass, "c1", "excluded") is None
    assert old_switch is not None
    assert hass.states.get(old_switch) is None
    assert switch_state(hass, "c2", "excluded") == STATE_OFF
    assert switch_state(hass, "c2", "window_override") == STATE_OFF
    assert stored_switches(hass_storage) == {"c2": {"excluded": False, "window_override": False}}
    assert hass_storage[STORAGE_KEY]["data"]["charger_groups"][0]["chargers"][0]["id"] == "c2"


async def test_switches_of_removed_chargers_are_removed_at_setup(hass: HomeAssistant, actions, setup_kraftvakt) -> None:
    """No orphaned switches remain in the entity registry."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    orphan = registry.async_get_or_create("switch", DOMAIN, "charger_old_excluded", config_entry=entry)
    hass.states.async_set(CHARGER, STATE_OFF, {ATTR_FRIENDLY_NAME: "Garage"})
    set_power(hass, POWER_SENSOR, "2000")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert registry.async_get(orphan.entity_id) is None
    assert switch_id(hass, "c1", "excluded") is not None


async def test_charger_name_without_a_device(hass: HomeAssistant) -> None:
    """The on/off entity's name is used, from the registry before it has a state, while the charger is switched by it."""
    registry = er.async_get(hass)
    entry = registry.async_get_or_create("switch", "test", "garage", original_name="Garage charger")

    assert item_name(hass, Charger("c1", on_off_entity=entry.entity_id)) == ("Garage charger")
    assert item_name(hass, Charger("c1", on_off_entity="switch.unknown")) == ("switch.unknown")
    assert item_name(hass, Charger("c1", switched_by=SwitchedBy.ACTIONS, on_off_entity="switch.unknown")) == "c1"
    assert item_name(hass, Charger("c1", device_id="unknown")) == "c1"
    assert item_name(hass, Charger("c1")) == "c1"


async def test_charger_is_named_after_its_device(hass: HomeAssistant) -> None:
    """A name the user gave the device wins."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={("test", "a")}, name="Charger A")
    charger = Charger("c1", device_id=device.id, on_off_entity="switch.a_allowed")

    assert item_name(hass, charger) == "Charger A"

    dr.async_get(hass).async_update_device(device.id, name_by_user="Garage")

    assert item_name(hass, charger) == "Garage"


async def test_charge_until_disconnected_of_a_removed_charger_changes_nothing(hass: HomeAssistant, setup_kraftvakt) -> None:
    """The switch can be used for a moment after its charger was removed."""
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data

    await runtime.async_set_charge_until_disconnected("gone", True)

    assert runtime.config_version == 0
