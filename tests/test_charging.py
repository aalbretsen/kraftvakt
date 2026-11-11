"""End-to-end tests of EV charging and the charger switches in Home Assistant.

They set the power sensors, move the time forward and check the actions that
reach the charger.
"""

from copy import deepcopy
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt.config_model import Charger, KraftvaktConfig
from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.entity import item_name
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
CHARGER = "input_boolean.charger"
CHARGER_POWER = "sensor.charger_power"
CAR_CONNECTED = "binary_sensor.charger_car"
WINDOW = timedelta(seconds=60)


def charger_data(charger_id: str = "c1", entity_id: str = CHARGER) -> dict[str, Any]:
    return {
        "id": charger_id,
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
        "charge_power_sensor": CHARGER_POWER,
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
        "priority": [{"type": "ev_charging"}],
        "charging": {
            "enabled": True,
            "one_at_a_time": False,
            "chargers": [charger_data()],
        },
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
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)


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
    config["charging"]["chargers"][0]["car_connected"] = {
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


async def test_window_override_lets_the_charger_charge_until_the_window(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The switch is set back when it ends."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    config["general"]["regulation_window_s"] = 600
    config["charging"]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "14:00",
    }
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    actions.clear()

    await advance(hass, freezer, timedelta(minutes=10))
    assert actions == []

    await use_switch(hass, "c1", "window_override", "turn_on")
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions == ["current 6", f"on {CHARGER}"]
    assert stored_switches(hass_storage)["c1"]["window_override"] is True

    for _ in range(3):
        await advance(hass, freezer, timedelta(minutes=10))
    assert switch_state(hass, "c1", "window_override") == STATE_ON
    await advance(hass, freezer, timedelta(minutes=10))
    assert switch_state(hass, "c1", "window_override") == STATE_OFF
    assert stored_switches(hass_storage)["c1"]["window_override"] is False
    actions.clear()

    for _ in range(5):
        await advance(hass, freezer, timedelta(minutes=10))
    assert f"off {CHARGER}" not in actions
    await advance(hass, freezer, timedelta(minutes=10))
    assert actions[-2:] == ["current 6", f"off {CHARGER}"]


async def test_window_override_counts_from_the_switch_over_a_stop(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """A window that started while stopped ends the override."""
    await hass.config.async_set_time_zone("Europe/Oslo")
    freezer.move_to("2026-11-07T11:00:00+00:00")
    config["general"]["regulation_window_s"] = 600
    config["charging"]["chargers"][0]["charging_window"] = {
        "start": "13:00",
        "end": "14:00",
    }
    set_power(hass, CHARGER_POWER, "4100")
    await setup_kraftvakt()
    await use_switch(hass, "c1", "window_override", "turn_on")
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.kraftvakt_regulation"},
        blocking=True,
    )

    for _ in range(7):
        await advance(hass, freezer, timedelta(minutes=10))
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.kraftvakt_regulation"},
        blocking=True,
    )
    for _ in range(2):
        await advance(hass, freezer, timedelta(minutes=10))

    assert switch_state(hass, "c1", "window_override") == STATE_OFF


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


async def test_charger_switches_are_unavailable_while_charging_is_disabled(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    actions,
    config,
    setup_kraftvakt,
) -> None:
    """The chargers are left alone and keep their switches."""
    config["charging"]["enabled"] = False
    config["priority"] = []
    config["charger_switches"] = {"c1": {"excluded": True, "window_override": False}}
    await setup_kraftvakt()

    assert switch_state(hass, "c1", "excluded") == STATE_UNAVAILABLE
    assert switch_state(hass, "c1", "window_override") == STATE_UNAVAILABLE
    assert actions == []
    assert hass_storage[STORAGE_KEY]["data"]["charger_switches"] == {
        "c1": {"excluded": True, "window_override": False}
    }


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
    data["charging"]["chargers"] = [charger_data("c2", "input_boolean.carport")]
    board = entry.runtime_data.charger_switches

    await board.async_update_config(KraftvaktConfig.from_dict(data))
    await hass.async_block_till_done()

    assert switch_id(hass, "c1", "excluded") is None
    assert old_switch is not None
    assert hass.states.get(old_switch) is None
    assert switch_state(hass, "c2", "excluded") == STATE_OFF
    assert switch_state(hass, "c2", "window_override") == STATE_OFF
    assert stored_switches(hass_storage) == {
        "c2": {"excluded": False, "window_override": False}
    }
    assert hass_storage[STORAGE_KEY]["data"]["charging"]["chargers"][0]["id"] == "c2"


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


async def test_charger_name_when_the_entity_has_no_state(hass: HomeAssistant) -> None:
    """The registry is used before the entity has a state."""
    registry = er.async_get(hass)
    entry = registry.async_get_or_create(
        "switch", "test", "garage", original_name="Garage charger"
    )

    assert item_name(hass, Charger("c1", entry.entity_id)) == "Garage charger"
    assert item_name(hass, Charger("c1", "switch.unknown")) == "switch.unknown"
    assert item_name(hass, Charger("c1")) == "c1"


async def test_charger_is_named_after_its_device(hass: HomeAssistant) -> None:
    """A name the user gave the device wins, and an entity without a device
    keeps its own name."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "a")}, name="Charger A"
    )
    allowed = er.async_get(hass).async_get_or_create(
        "switch",
        "test",
        "a_allowed",
        device_id=device.id,
        original_name="Charger A Charging allowed",
    )

    assert item_name(hass, Charger("c1", allowed.entity_id)) == "Charger A"

    dr.async_get(hass).async_update_device(device.id, name_by_user="Garage")

    assert item_name(hass, Charger("c1", allowed.entity_id)) == "Garage"
