"""Tests for storage of the configuration and the charger switches."""

import json
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kraftvakt.config_model import (
    ApplianceSwitches,
    ChargerGroup,
    ChargerSwitches,
    ConfigValidationError,
    PriorityEntry,
)
from custom_components.kraftvakt.config_reader import (
    read_config,
)
from custom_components.kraftvakt.storage import (
    STORAGE_KEY,
    STORAGE_VERSION,
    KraftvaktStorage,
    StoredData,
)
from tests.config_examples import full_config_data


async def test_load_without_stored_data_gives_defaults(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    stored = await KraftvaktStorage(hass).async_load()

    assert stored == StoredData()
    assert STORAGE_KEY not in hass_storage


async def test_saved_data_survives_restart(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    config = read_config(full_config_data())
    saved = StoredData(
        config,
        appliance_switches={
            "a1": ApplianceSwitches(excluded=True),
            "a2": ApplianceSwitches(),
        },
        charger_switches={"c1": ChargerSwitches(excluded=True, window_override=True)},
    )

    await KraftvaktStorage(hass).async_save(saved)
    stored = await KraftvaktStorage(hass).async_load()

    assert stored == saved


async def test_stored_format_is_versioned_json(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    config = read_config(full_config_data())

    await KraftvaktStorage(hass).async_save(StoredData(config))

    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert stored["data"] == {
        **full_config_data(),
        "appliance_switches": {"a1": {"excluded": False}, "a2": {"excluded": False}},
        "charger_switches": {"c1": {"excluded": False, "window_override": False}},
    }


async def test_load_reads_stored_data(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": {
            **full_config_data(),
            "appliance_switches": {"a2": {"excluded": True}},
            "charger_switches": {"c1": {"excluded": True, "window_override": False}},
        },
    }

    stored = await KraftvaktStorage(hass).async_load()

    assert stored.config == read_config(full_config_data())
    assert stored.appliance_switches == {
        "a1": ApplianceSwitches(),
        "a2": ApplianceSwitches(excluded=True),
    }
    assert stored.charger_switches == {"c1": ChargerSwitches(excluded=True)}


async def test_switches_follow_configured_chargers(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"].append(
        {
            **data["charger_groups"][0]["chargers"][0],
            "id": "c2",
            "entity_id": "switch.charger_2",
        }
    )
    config = read_config(data)
    switches = {"gone": ChargerSwitches(excluded=True)}

    await KraftvaktStorage(hass).async_save(
        StoredData(config, charger_switches=switches)
    )
    stored = await KraftvaktStorage(hass).async_load()

    assert stored.charger_switches == {
        "c1": ChargerSwitches(),
        "c2": ChargerSwitches(),
    }


async def test_load_rejects_unreadable_data(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "key": STORAGE_KEY,
        "data": {"general": {"power_limit_w": "ti"}},
    }

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()


def version_1_data() -> dict[str, Any]:
    """The full configuration as version 1 stored it: without variant actions,
    and with the chargers in the charging settings instead of groups."""
    data = full_config_data()
    for appliance in data["appliances"]:
        appliance.update(appliance.pop("actions")["main"])
    group = data.pop("charger_groups")[0]
    for charger in group["chargers"]:
        del charger["device_id"]
    data["charging"] = {
        "enabled": True,
        "one_at_a_time": group["one_at_a_time"],
        "chargers": group["chargers"],
    }
    data["priority"] = [
        {"type": "ev_charging"} if entry["type"] == "charger_group" else entry
        for entry in data["priority"]
    ]
    return {
        **data,
        "appliance_switches": {"a1": {"excluded": True}},
        "charger_switches": {"c1": {"excluded": True}},
    }


def store_version_1(hass_storage: dict[str, Any], data: dict[str, Any]) -> None:
    hass_storage[STORAGE_KEY] = {"version": 1, "key": STORAGE_KEY, "data": data}


async def test_version_1_is_migrated_to_the_current_format(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The actions of each appliance become those of the appliance itself, and
    its variants use them. The chargers become one group with a new id, in the
    place of «EV charging», and get the device of their entity."""
    store_version_1(hass_storage, version_1_data())
    device_id = register_entity_on_device(hass, "switch.garage_charger")
    expected = full_config_data()
    del expected["appliances"][0]["actions"]["v1"]
    expected["charger_groups"][0]["chargers"][0]["device_id"] = device_id

    stored = await KraftvaktStorage(hass).async_load()

    group_id = stored.config.charger_groups[0].id
    assert group_id != "g1"
    expected = json.loads(json.dumps(expected).replace('"g1"', f'"{group_id}"'))
    assert stored.config == read_config(expected)
    assert stored.appliance_switches["a1"] == ApplianceSwitches(excluded=True)
    assert stored.charger_switches == {"c1": ChargerSwitches(excluded=True)}


async def test_version_1_without_chargers_and_disabled_gets_no_group(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    store_version_1(hass_storage, {"general": {"power_limit_w": 8000}})

    stored = await KraftvaktStorage(hass).async_load()

    assert stored.config.general.power_limit_w == 8000
    assert stored.config.charger_groups == ()
    assert stored.config.priority == ()


async def test_version_1_enabled_without_chargers_keeps_an_empty_group(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    data = version_1_data()
    data["charging"]["chargers"] = []
    store_version_1(hass_storage, data)

    stored = await KraftvaktStorage(hass).async_load()

    group = stored.config.charger_groups[0]
    assert group == ChargerGroup(group.id, "EV chargers", one_at_a_time=False)
    assert stored.config.priority[1] == PriorityEntry.for_charger_group(group.id)


async def test_version_1_disabled_with_chargers_gets_a_regulated_group_last(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The chargers were kept but not regulated, and are regulated now."""
    data = version_1_data()
    data["charging"]["enabled"] = False
    data["priority"].remove({"type": "ev_charging"})
    store_version_1(hass_storage, data)

    stored = await KraftvaktStorage(hass).async_load()

    group = stored.config.charger_groups[0]
    assert [charger.id for charger in group.chargers] == ["c1"]
    assert stored.config.priority[-1] == PriorityEntry.for_charger_group(group.id)
    assert len(stored.config.priority) == 4


async def test_migrated_data_is_saved_as_the_new_version(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    store_version_1(hass_storage, version_1_data())
    storage = KraftvaktStorage(hass)

    await storage.async_save(await storage.async_load())

    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert "turn_on" not in stored["data"]["appliances"][0]
    assert stored["data"]["appliances"][1]["actions"] == {
        "main": {"turn_on": {"mode": "default"}, "turn_off": {"mode": "default"}}
    }
    assert "charging" not in stored["data"]
    assert stored["data"]["charger_groups"][0]["name"] == "EV chargers"


async def test_migration_leaves_unreadable_charging_to_the_reader(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    store_version_1(hass_storage, {"charging": "not a mapping"})

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()


@pytest.mark.parametrize(
    "appliances", ["not a list", ["not an appliance"]], ids=["text", "list of text"]
)
async def test_migration_leaves_unreadable_appliances_to_the_reader(
    hass: HomeAssistant, hass_storage: dict[str, Any], appliances: Any
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": {"appliances": appliances},
    }

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()


def register_entity_on_device(hass: HomeAssistant, entity_id: str) -> str:
    """Register the entity on a new device and return the id of the device."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", entity_id)}
    )
    domain, object_id = entity_id.split(".")
    er.async_get(hass).async_get_or_create(
        domain,
        "test",
        object_id,
        suggested_object_id=object_id,
        device_id=device.id,
    )
    return device.id


async def test_version_2_chargers_get_the_device_of_their_entity(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """A charger whose entity has no device, or no entity, gets none."""
    device_id = register_entity_on_device(hass, "switch.garage_charger")
    data = full_config_data()
    group = data["charger_groups"][0]
    group["chargers"][0].pop("device_id")
    group["chargers"] += [
        {"id": "c2", "entity_id": "switch.cabin_charger"},
        {"id": "c3"},
    ]
    hass_storage[STORAGE_KEY] = {"version": 2, "key": STORAGE_KEY, "data": data}

    stored = await KraftvaktStorage(hass).async_load()

    chargers = stored.config.charger_groups[0].chargers
    assert [charger.device_id for charger in chargers] == [device_id, None, None]


@pytest.mark.parametrize(
    "charger_groups",
    ["not a list", ["not a group"], [{"id": "g1", "chargers": ["not a charger"]}]],
    ids=["text", "list of text", "chargers of text"],
)
async def test_migration_leaves_unreadable_chargers_to_the_reader(
    hass: HomeAssistant, hass_storage: dict[str, Any], charger_groups: Any
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 2,
        "key": STORAGE_KEY,
        "data": {"charger_groups": charger_groups},
    }

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()


async def test_migration_leaves_an_unreadable_entity_to_the_reader(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    data = full_config_data()
    data["charger_groups"][0]["chargers"][0]["entity_id"] = 7
    hass_storage[STORAGE_KEY] = {"version": 2, "key": STORAGE_KEY, "data": data}

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()
