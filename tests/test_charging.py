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
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt.config_model import (
    Charger,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
)
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.entity import item_name
from custom_components.kraftvakt.regulation.charging import ChargerState
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
        "entity_id": entity_id,
        "activate": {"mode": "default"},
        "deactivate": {"mode": "default"},
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
        "actively_charging": {"type": "power_sensor", "value": CHARGER_POWER},
        "power_reserve_w": 4000,
    }


@pytest.fixture
def config(hass_storage: dict[str, Any]) -> dict[str, Any]:
    """Store a complete configuration with one charger; tests may change it."""
    data: dict[str, Any] = {
        "general": {
            "power_sensor": POWER_SENSOR,
            "power_limit_w": 10000,
            "regulation_window_s": 60,
            "regulation_interval": 1,
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
        set_power(hass, POWER_SENSOR, "2000")
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        return entry

    return setup


def set_power(hass: HomeAssistant, entity_id: str, watt: str) -> None:
    hass.states.async_set(entity_id, watt, {ATTR_UNIT_OF_MEASUREMENT: "W"})


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta = WINDOW
) -> None:
    """Move time on, with the power sensors reporting as a HAN reader does."""
    freezer.tick(delta)
    for sensor in (POWER_SENSOR, CHARGER_POWER):
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


def switch_id(hass: HomeAssistant, charger_id: str, setting: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "switch", DOMAIN, f"charger_{charger_id}_{setting}"
    )


def switch_state(hass: HomeAssistant, charger_id: str, setting: str) -> str:
    entity_id = switch_id(hass, charger_id, setting)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


async def use_switch(
    hass: HomeAssistant, charger_id: str, setting: str, service: str
) -> None:
    await hass.services.async_call(
        "switch",
        service,
        {"entity_id": switch_id(hass, charger_id, setting)},
        blocking=True,
    )


def allowed_sensor_id(hass: HomeAssistant, charger_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, f"charger_{charger_id}_allowed_to_charge"
    )


def allowed_sensor_state(hass: HomeAssistant, charger_id: str) -> str:
    entity_id = allowed_sensor_id(hass, charger_id)
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


def steps_switched_on(hass: HomeAssistant) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, "regulation_steps_on"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


def stored_switches(hass_storage: dict[str, Any]) -> dict[str, Any]:
    return hass_storage[STORAGE_KEY]["data"]["charger_switches"]


async def test_charger_current_follows_the_free_power(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, actions, setup_kraftvakt
) -> None:
    """The current is set before (de)activating."""
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
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["current 7", "current 6", "current 6", f"off {CHARGER}"]
    assert steps_switched_on(hass) == "0"


async def test_charger_without_car_is_not_activated(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    config["charger_groups"][0]["chargers"][0]["car_connected"] = {
        "type": "entity",
        "value": CAR_CONNECTED,
    }
    set_power(hass, CHARGER_POWER, "0")
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
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
    ("actively_charging", "entity_id", "idle", "charging", "attributes"),
    [
        (
            {"type": "power_sensor", "value": CHARGER_POWER},
            CHARGER_POWER,
            "0.1",
            "0.2",
            {ATTR_UNIT_OF_MEASUREMENT: "kW"},
        ),
        (
            {"type": "entity", "value": "binary_sensor.charger_charging"},
            "binary_sensor.charger_charging",
            STATE_OFF,
            STATE_ON,
            {},
        ),
        (
            {
                "type": "template",
                "value": "{{ is_state('sensor.charger_status', 'charging') }}",
            },
            "sensor.charger_status",
            "connected",
            "charging",
            {},
        ),
    ],
)
async def test_actively_charging_from_a_sensor_an_entity_or_a_template(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    actively_charging: dict[str, str],
    entity_id: str,
    idle: str,
    charging: str,
    attributes: dict[str, str],
) -> None:
    """A charger that does not charge is bypassed, and gets more once it charges."""
    config["charger_groups"][0]["chargers"][0]["actively_charging"] = actively_charging
    hass.states.async_set(entity_id, idle, attributes)
    entry = await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]
    assert entry.runtime_data.chargers["c1"].bypassed

    hass.states.async_set(entity_id, charging, attributes)
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}", "current 7"]
    assert not entry.runtime_data.chargers["c1"].bypassed


@pytest.mark.parametrize(
    "actively_charging",
    [
        {"type": "power_sensor", "value": CHARGER_POWER},
        {"type": "entity", "value": "binary_sensor.charger_charging"},
        {"type": "template", "value": "{{ states('sensor.gone') | float > 0 }}"},
    ],
)
async def test_charger_without_evidence_counts_as_not_charging(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
    actively_charging: dict[str, str],
) -> None:
    config["charger_groups"][0]["chargers"][0]["actively_charging"] = actively_charging
    hass.states.async_set(CHARGER_POWER, STATE_UNAVAILABLE)
    hass.states.async_set("binary_sensor.charger_charging", STATE_UNAVAILABLE)
    entry = await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer)
    await advance(hass, freezer)
    await advance(hass, freezer)
    assert actions == ["current 6", f"on {CHARGER}"]
    assert entry.runtime_data.chargers["c1"].bypassed


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


async def advance_until(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, local_time: str
) -> None:
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
    """Switched on before the car arrives, it outlasts the window and full car."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T18:55:00+00:00")
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    charger["car_connected"] = {"type": "entity", "value": CAR_CONNECTED}
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

    await advance_until(hass, freezer, "2026-11-08T07:00")
    set_power(hass, CHARGER_POWER, "2000")
    actions.clear()
    await advance_until(hass, freezer, "2026-11-08T07:20")
    assert actions == ["current 7", "current 8"]
    assert entry_charger_state(hass) is ChargerState.OVERRIDE

    hass.states.async_set(CAR_CONNECTED, STATE_OFF)
    set_power(hass, CHARGER_POWER, "0")
    await advance_until(hass, freezer, "2026-11-08T07:40")
    assert switch_state(hass, "c1", "window_override") == STATE_OFF
    assert stored_switches(hass_storage)["c1"]["window_override"] is False
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]
    assert entry_charger_state(hass) is ChargerState.OUTSIDE_WINDOW


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
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    charger["car_connected"] = {"type": "entity", "value": CAR_CONNECTED}
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
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    charger["car_connected"] = {"type": "entity", "value": CAR_CONNECTED}
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
    """A full car ends it, so the car heating in the morning does not charge."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T18:55:00+00:00")
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "charging_stopped"
    set_power(hass, CHARGER_POWER, "0")
    await setup_kraftvakt()
    await advance_until(hass, freezer, "2026-11-07T20:00")
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance_until(hass, freezer, "2026-11-07T21:00")
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
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "22:00", "end": "06:00"}
    charger["override_ends"] = "car_disconnected"
    charger["car_connected"] = {"type": "entity", "value": CAR_CONNECTED}
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
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "13:00", "end": "14:00"}
    charger["override_ends"] = "manual"
    charger["car_connected"] = {"type": "entity", "value": CAR_CONNECTED}
    hass.states.async_set(CAR_CONNECTED, STATE_ON)
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))
    hass.states.async_set(CAR_CONNECTED, STATE_OFF)

    await advance(hass, freezer, timedelta(days=1))
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


def stored_finish_after_window(hass_storage: dict[str, Any]) -> bool:
    data = hass_storage[STORAGE_KEY]["data"]
    return data["charger_groups"][0]["chargers"][0]["finish_after_window"]


async def test_charger_finishes_charging_after_the_window_when_switched_on(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The switch is saved while the regulation runs and applies at once."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:50:00+00:00")
    config["general"]["regulation_window_s"] = 600
    config["charger_groups"][0]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "13:20",
    }
    set_power(hass, CHARGER_POWER, "4100")
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    version = runtime.config_version
    actions.clear()

    await use_switch(hass, "c1", "finish_after_window", "turn_on")
    assert runtime.running
    assert switch_state(hass, "c1", "finish_after_window") == STATE_ON
    assert stored_finish_after_window(hass_storage) is True
    assert runtime.config_version == version + 1
    for _ in range(4):
        await advance(hass, freezer, timedelta(minutes=10))
    assert actions == ["current 6", f"on {CHARGER}", "current 7", "current 8"]
    assert runtime.chargers["c1"].state is ChargerState.FINISHING

    set_power(hass, CHARGER_POWER, "0")
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]
    actions.clear()
    set_power(hass, CHARGER_POWER, "4100")
    for _ in range(3):
        await advance(hass, freezer, timedelta(minutes=10))
    assert f"on {CHARGER}" not in actions


async def test_finish_after_window_switch_saves_the_configuration_while_stopped(
    hass: HomeAssistant, hass_storage: dict[str, Any], actions, setup_kraftvakt
) -> None:
    """Setting it to what it is already saves nothing."""
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data
    runtime.async_stop_regulation()
    await use_switch(hass, "c1", "finish_after_window", "turn_on")
    version = runtime.config_version

    await use_switch(hass, "c1", "finish_after_window", "turn_on")
    assert runtime.config_version == version
    await use_switch(hass, "c1", "finish_after_window", "turn_off")

    assert switch_state(hass, "c1", "finish_after_window") == STATE_OFF
    assert stored_finish_after_window(hass_storage) is False
    assert runtime.config.chargers[0].finish_after_window is False
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
    config["general"]["regulation_window_s"] = 600
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


async def test_allowed_sensor_follows_finishing_and_the_excluded_switch(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """It stays on from the end of the window until a decision ends finishing."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:50:00+00:00")
    config["general"]["regulation_window_s"] = 600
    charger = config["charger_groups"][0]["chargers"][0]
    charger["charging_window"] = {"start": "13:00", "end": "13:15"}
    charger["finish_after_window"] = True
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    actions.clear()
    for _ in range(3):
        await advance(hass, freezer, timedelta(minutes=10))
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    await advance(hass, freezer, timedelta(minutes=5))
    assert allowed_sensor_state(hass, "c1") == STATE_ON
    await advance(hass, freezer, timedelta(minutes=5))
    assert allowed_sensor_state(hass, "c1") == STATE_ON
    assert f"off {CHARGER}" not in actions

    await use_switch(hass, "c1", "excluded", "turn_on")
    assert allowed_sensor_state(hass, "c1") == STATE_OFF
    await use_switch(hass, "c1", "excluded", "turn_off")
    assert allowed_sensor_state(hass, "c1") == STATE_ON

    set_power(hass, CHARGER_POWER, "0")
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-1] == f"off {CHARGER}"
    assert allowed_sensor_state(hass, "c1") == STATE_OFF
    set_power(hass, CHARGER_POWER, "4100")
    await advance(hass, freezer, timedelta(minutes=10))
    assert allowed_sensor_state(hass, "c1") == STATE_OFF


async def test_allowed_sensor_is_on_without_a_window(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    """A diagnostic named after the charger."""
    await setup_kraftvakt()

    entity_id = allowed_sensor_id(hass, "c1")
    assert entity_id == "binary_sensor.kraftvakt_charger_garage_allowed_to_charge"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.name == "Kraftvakt Garage allowed to charge"
    registry_entry = er.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.entity_category is EntityCategory.DIAGNOSTIC


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
    settings = entry.runtime_data.settings
    data = deepcopy(config)
    data["charger_groups"][0]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "14:00",
    }

    await settings.async_update_config(read_config(data))
    await hass.async_block_till_done()
    assert allowed_sensor_state(hass, "c1") == STATE_OFF

    hass.states.async_set("input_boolean.carport", STATE_OFF)
    data["charger_groups"][0]["chargers"] = [
        charger_data("c2", "input_boolean.carport")
    ]
    await settings.async_update_config(read_config(data))
    await hass.async_block_till_done()

    assert allowed_sensor_id(hass, "c1") is None
    assert allowed_sensor_state(hass, "c2") == STATE_ON


async def test_allowed_sensor_of_removed_charger_is_removed_at_setup(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    """No orphaned binary sensors remain in the entity registry."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    orphan = registry.async_get_or_create(
        "binary_sensor", DOMAIN, "charger_old_allowed_to_charge", config_entry=entry
    )
    hass.states.async_set(CHARGER, STATE_OFF, {ATTR_FRIENDLY_NAME: "Garage"})
    set_power(hass, POWER_SENSOR, "2000")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert registry.async_get(orphan.entity_id) is None
    assert allowed_sensor_id(hass, "c1") is not None


async def test_charger_switches_are_kept_over_a_reload(
    hass: HomeAssistant, hass_storage: dict[str, Any], actions, setup_kraftvakt
) -> None:
    """The positions are configuration."""
    entry = await setup_kraftvakt()
    await use_switch(hass, "c1", "excluded", "turn_on")
    await use_switch(hass, "c1", "window_override", "turn_on")

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert switch_state(hass, "c1", "excluded") == STATE_ON
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    assert stored_switches(hass_storage) == {
        "c1": {"excluded": True, "window_override": True}
    }


async def test_charger_switches_are_named_after_the_charger(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    """The name of the charger's entity identifies the switches."""
    await setup_kraftvakt()

    assert (
        switch_id(hass, "c1", "excluded") == "switch.kraftvakt_charger_garage_excluded"
    )
    assert (
        switch_id(hass, "c1", "window_override")
        == "switch.kraftvakt_charger_garage_window_override"
    )
    excluded = hass.states.get(switch_id(hass, "c1", "excluded") or "")
    override = hass.states.get(switch_id(hass, "c1", "window_override") or "")

    assert excluded is not None
    assert excluded.name == "Kraftvakt Garage excluded from regulation"
    assert override is not None
    assert override.name == "Kraftvakt Garage override charging window"
    finish = hass.states.get(switch_id(hass, "c1", "finish_after_window") or "")
    assert finish is not None
    assert finish.entity_id == "switch.kraftvakt_charger_garage_finish_after_window"
    assert finish.name == "Kraftvakt Garage finish charging after charging window"


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
    data["charger_groups"][0]["chargers"] = [
        charger_data("c2", "input_boolean.carport")
    ]
    settings = entry.runtime_data.settings

    await settings.async_update_config(read_config(data))
    await hass.async_block_till_done()

    assert switch_id(hass, "c1", "excluded") is None
    assert old_switch is not None
    assert hass.states.get(old_switch) is None
    assert switch_state(hass, "c2", "excluded") == STATE_OFF
    assert switch_state(hass, "c2", "window_override") == STATE_OFF
    assert stored_switches(hass_storage) == {
        "c2": {"excluded": False, "window_override": False}
    }
    assert (
        hass_storage[STORAGE_KEY]["data"]["charger_groups"][0]["chargers"][0]["id"]
        == "c2"
    )


async def test_switches_of_removed_chargers_are_removed_at_setup(
    hass: HomeAssistant, actions, setup_kraftvakt
) -> None:
    """No orphaned switches remain in the entity registry."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    orphan = registry.async_get_or_create(
        "switch", DOMAIN, "charger_old_excluded", config_entry=entry
    )
    hass.states.async_set(CHARGER, STATE_OFF, {ATTR_FRIENDLY_NAME: "Garage"})
    set_power(hass, POWER_SENSOR, "2000")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert registry.async_get(orphan.entity_id) is None
    assert switch_id(hass, "c1", "excluded") is not None


async def test_charger_name_without_a_device(hass: HomeAssistant) -> None:
    """The entity's name is used, from the registry before it has a state."""
    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        "switch", "test", "garage", original_name="Garage charger"
    )

    assert item_name(hass, Charger("c1", entity_id=entry.entity_id)) == (
        "Garage charger"
    )
    assert item_name(hass, Charger("c1", entity_id="switch.unknown")) == (
        "switch.unknown"
    )
    assert item_name(hass, Charger("c1", device_id="unknown")) == "c1"
    assert item_name(hass, Charger("c1")) == "c1"


async def test_charger_is_named_after_its_device(hass: HomeAssistant) -> None:
    """A name the user gave the device wins."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "a")}, name="Charger A"
    )
    charger = Charger("c1", device_id=device.id, entity_id="switch.a_allowed")

    assert item_name(hass, charger) == "Charger A"

    dr.async_get(hass).async_update_device(device.id, name_by_user="Garage")

    assert item_name(hass, charger) == "Garage"


async def test_finish_after_window_of_a_removed_charger_changes_nothing(
    hass: HomeAssistant, setup_kraftvakt
) -> None:
    """The switch can be used for a moment after its charger was removed."""
    entry = await setup_kraftvakt()
    runtime = entry.runtime_data

    await runtime.async_set_finish_after_window("gone", True)

    assert runtime.config_version == 0
