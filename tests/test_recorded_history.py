"""Black box tests of the recorded history of the entities the regulation reads and sets, in the diagnostics."""

from datetime import datetime, timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder import Recorder
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

POWER_SENSOR = "sensor.han_power"
THERMOSTAT = "climate.floor"
DEFAULT = {"mode": "default"}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock: Recorder, enable_custom_integrations: None) -> None:
    """Start the recorder before Home Assistant, which the recorder requires."""


@pytest.fixture(autouse=True)
def services(hass: HomeAssistant) -> None:
    for domain, service in (
        ("light", "turn_on"),
        ("light", "turn_off"),
        ("climate", "set_temperature"),
        ("input_boolean", "turn_on"),
        ("input_boolean", "turn_off"),
        ("input_number", "set_value"),
    ):
        hass.services.async_register(domain, service, lambda call: None)


def store(hass_storage: dict[str, Any], data: dict[str, Any]) -> None:
    hass_storage[STORAGE_KEY] = {"version": STORAGE_VERSION, "minor_version": 1, "key": STORAGE_KEY, "data": data}


def thermostat_action(temperature: int) -> dict[str, Any]:
    return {"mode": "custom", "action": [{"action": "climate.set_temperature", "target": {"entity_id": THERMOSTAT}, "data": {"temperature": temperature}}]}


CONFIG: dict[str, Any] = {
    "general": {"power_sensor": POWER_SENSOR, "regulation_window_updates": 1, "power_sensor_interval_s": 60},
    "appliances": [
        {
            "id": "a",
            "entity_id": "light.a",
            "turn_on": DEFAULT,
            "turn_off": DEFAULT,
            "variants": [{"id": "v", "label": "Morning", "condition": {"type": "template", "value": "{{ is_state('input_boolean.morning', 'on') }}"}}],
            "display_power": {"type": "power_sensor", "value": "sensor.a_power"},
        },
        {"id": "t", "entity_id": THERMOSTAT, "turn_on": thermostat_action(22), "turn_off": thermostat_action(8)},
    ],
    "charger_groups": [
        {
            "id": "g",
            "name": "Garage",
            "chargers": [
                {
                    "id": "c",
                    "on_off_entity": "input_boolean.charger",
                    "set_current": {"mode": "entity", "entity_id": "input_number.current"},
                    "car_connected": {"type": "entity", "value": "binary_sensor.car"},
                    "charging_power": {"type": "power_sensor", "value": "sensor.charger_power"},
                    "fault_flag": {"type": "entity", "value": "binary_sensor.fault"},
                }
            ],
        }
    ],
}


async def record(hass: HomeAssistant, freezer: FrozenDateTimeFactory, when: datetime, entity_id: str, state: str, attributes: dict[str, Any] | None = None) -> None:
    freezer.move_to(when)
    hass.states.async_set(entity_id, state, attributes)
    await async_wait_recording_done(hass)


async def download(hass: HomeAssistant, hass_client: ClientSessionGenerator) -> dict[str, Any]:
    assert await async_setup_component(hass, "diagnostics", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    await async_wait_recording_done(hass)
    diagnostics: dict[str, Any] = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    return diagnostics


def local(moment: datetime) -> str:
    return dt_util.as_local(moment).isoformat()


async def test_the_history_holds_a_day_of_the_entities_the_regulation_reads_and_sets(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any]
) -> None:
    """The state at the start of the day and every change after it; the entities that are set come with their attributes."""
    now = dt_util.utcnow()
    store(hass_storage, CONFIG)
    watt = {ATTR_UNIT_OF_MEASUREMENT: "W"}
    await record(hass, freezer, now - timedelta(hours=26), POWER_SENSOR, "1000", watt)
    await record(hass, freezer, now - timedelta(hours=25), POWER_SENSOR, "1500", watt)
    await record(hass, freezer, now - timedelta(hours=2), POWER_SENSOR, "2000", watt)
    await record(hass, freezer, now - timedelta(hours=2), "input_number.current", "6")
    await record(hass, freezer, now - timedelta(hours=2), "input_boolean.morning", STATE_ON)
    await record(hass, freezer, now - timedelta(hours=2), "binary_sensor.car", STATE_ON)
    await record(hass, freezer, now - timedelta(hours=2), "binary_sensor.fault", STATE_OFF)
    await record(hass, freezer, now - timedelta(hours=2), "sensor.a_power", "0", watt)
    await record(hass, freezer, now - timedelta(hours=2), THERMOSTAT, "heat", {"temperature": 22, "current_temperature": 20})
    await record(hass, freezer, now - timedelta(hours=1), "input_number.current", "7")
    await record(hass, freezer, now - timedelta(hours=1), THERMOSTAT, "heat", {"temperature": 8, "current_temperature": 20})
    freezer.move_to(now)

    history = (await download(hass, hass_client))["history"]

    assert history["start"] == local(now - timedelta(hours=24))
    assert history["end"] == local(now)
    entities = history["entities"]
    assert entities[POWER_SENSOR]["uses"] == [{"item": None, "field": "power_sensor"}]
    assert entities[POWER_SENSOR]["states"] == [
        {"time": local(now - timedelta(hours=24)), "state": "1500"},
        {"time": local(now - timedelta(hours=2)), "state": "2000"},
    ]
    assert entities["input_boolean.morning"]["uses"] == [{"item": "a", "field": "variants.v.condition"}]
    assert entities["light.a"]["uses"] == [{"item": "a", "field": "controlled_entity"}, {"item": "a", "field": "turn_on"}, {"item": "a", "field": "turn_off"}]
    assert entities[THERMOSTAT]["uses"] == [{"item": "t", "field": "controlled_entity"}, {"item": "t", "field": "turn_on"}, {"item": "t", "field": "turn_off"}]
    assert entities[THERMOSTAT]["states"] == [
        {"time": local(now - timedelta(hours=2)), "state": "heat", "attributes": {"temperature": 22, "current_temperature": 20}},
        {"time": local(now - timedelta(hours=1)), "state": "heat", "attributes": {"temperature": 8, "current_temperature": 20}},
    ]
    assert entities["input_number.current"] == {
        "uses": [{"item": "c", "field": "set_current"}],
        "states": [
            {"time": local(now - timedelta(hours=2)), "state": "6", "attributes": {}},
            {"time": local(now - timedelta(hours=1)), "state": "7", "attributes": {}},
        ],
    }
    assert entities["input_boolean.charger"]["uses"] == [{"item": "c", "field": "controlled_entity"}]
    assert entities["binary_sensor.car"]["uses"] == [{"item": "c", "field": "car_connected"}]
    assert entities["sensor.charger_power"]["uses"] == [{"item": "c", "field": "charging_power"}]
    assert entities["switch.kraftvakt_regulation"]["uses"] == [{"item": None, "field": "regulation"}]
    assert entities["switch.kraftvakt_charger_input_boolean_charger_excluded"]["uses"] == [{"item": "c", "field": "charger_excluded"}]
    assert entities["switch.kraftvakt_appliance_light_a_excluded"]["uses"] == [{"item": "a", "field": "appliance_excluded"}]
    assert entities["sensor.kraftvakt_charger_input_boolean_charger_state"]["uses"] == [{"item": "c", "field": "charger_state"}]
    assert "sensor.a_power" not in entities
    assert "binary_sensor.fault" not in entities
    assert "sensor.kraftvakt_power_free" not in entities


async def test_the_history_of_a_custom_action_holds_the_entities_it_names(hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_storage: dict[str, Any]) -> None:
    """Entities named in a template of a custom action are not found. A fault flag is read with deactivate on fault."""
    charger = {
        "id": "c",
        "switched_by": "actions",
        "activate": {"mode": "custom", "action": [{"action": "input_boolean.turn_on", "target": {"entity_id": ["input_boolean.resume", "{{ 'input_boolean.x' }}"]}}]},
        "deactivate": {"mode": "custom", "action": []},
        "deactivate_on_fault": True,
        "fault_flag": {"type": "template", "value": "{{ is_state('binary_sensor.fault', 'on') }}"},
    }
    store(hass_storage, {"charger_groups": [{"id": "g", "name": "Garage", "chargers": [charger]}]})

    entities = (await download(hass, hass_client))["history"]["entities"]

    assert entities["input_boolean.resume"] == {"uses": [{"item": "c", "field": "activate"}], "states": []}
    assert entities["binary_sensor.fault"] == {"uses": [{"item": "c", "field": "fault_flag"}], "states": []}
    assert "input_boolean.x" not in entities


async def test_the_history_holds_the_entities_of_one_at_a_time_given_as_an_expression(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_storage: dict[str, Any]
) -> None:
    """The template gets the power limit, so the branch that reads the entity is rendered."""
    expression = {"type": "template", "value": "{{ power_limit < 15000 and is_state('input_boolean.share', 'off') }}"}
    store(hass_storage, {"general": {"power_limit_w": 10000}, "charger_groups": [{"id": "g", "name": "Garage", "one_at_a_time": expression}]})

    entities = (await download(hass, hass_client))["history"]["entities"]

    assert entities["input_boolean.share"] == {"uses": [{"item": "g", "field": "one_at_a_time"}], "states": []}


async def test_the_history_without_a_configuration_holds_kraftvakts_own_entities(hass: HomeAssistant, hass_client: ClientSessionGenerator) -> None:
    entities = (await download(hass, hass_client))["history"]["entities"]

    assert entities["number.kraftvakt_power_limit"]["uses"] == [{"item": None, "field": "power_limit"}]
    assert all(use["item"] is None for entity in entities.values() for use in entity["uses"])
