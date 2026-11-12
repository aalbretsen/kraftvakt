"""Tests for storage of the configuration and the charger switches."""

import json
from typing import Any

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.config_model import (
    ApplianceSwitches,
    ChargerGroup,
    ChargerSwitches,
    ConfigValidationError,
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


def version_2_data() -> dict[str, Any]:
    """The full configuration as version 2 stored it, without charger groups."""
    data = full_config_data()
    group = data.pop("charger_groups")[0]
    data["charging"] = {
        key: group[key] for key in ("enabled", "one_at_a_time", "chargers")
    }
    data["priority"] = [
        {"type": "ev_charging"} if entry["type"] == "charger_group" else entry
        for entry in data["priority"]
    ]
    return {**data, "charger_switches": {"c1": {"excluded": True}}}


def with_group_id(data: dict[str, Any], group_id: str) -> dict[str, Any]:
    """Return the full configuration with another id for its group."""
    return json.loads(json.dumps(data).replace('"g1"', f'"{group_id}"'))


async def test_version_2_puts_the_chargers_in_one_group(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The group gets a new id and takes the place of «EV charging»."""
    hass_storage[STORAGE_KEY] = {
        "version": 2,
        "key": STORAGE_KEY,
        "data": version_2_data(),
    }

    stored = await KraftvaktStorage(hass).async_load()

    group_id = stored.config.charger_groups[0].id
    assert group_id != "g1"
    assert stored.config == read_config(with_group_id(full_config_data(), group_id))
    assert stored.charger_switches == {"c1": ChargerSwitches(excluded=True)}


async def test_version_2_without_chargers_gets_an_empty_group(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 2,
        "key": STORAGE_KEY,
        "data": {"general": {"power_limit_w": 8000}},
    }

    stored = await KraftvaktStorage(hass).async_load()

    group_id = stored.config.charger_groups[0].id
    assert stored.config.charger_groups == (ChargerGroup(group_id, "EV chargers"),)
    assert stored.config.priority == ()


async def test_migration_leaves_unreadable_charging_to_the_reader(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 2,
        "key": STORAGE_KEY,
        "data": {"charging": "not a mapping"},
    }

    with pytest.raises(ConfigValidationError):
        await KraftvaktStorage(hass).async_load()


def version_1_data() -> dict[str, Any]:
    """The full configuration as version 1 stored it, without variant actions."""
    data = version_2_data()
    for appliance in data["appliances"]:
        appliance.update(appliance.pop("actions")["main"])
    return {**data, "appliance_switches": {"a1": {"excluded": True}}}


async def test_version_1_gets_the_actions_of_the_appliance_in_a_map(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The actions of each appliance become those of the appliance itself, and
    its variants use them."""
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": version_1_data(),
    }
    expected = full_config_data()
    del expected["appliances"][0]["actions"]["v1"]

    stored = await KraftvaktStorage(hass).async_load()

    group_id = stored.config.charger_groups[0].id
    assert stored.config == read_config(with_group_id(expected, group_id))
    assert stored.appliance_switches["a1"] == ApplianceSwitches(excluded=True)


async def test_migrated_data_is_saved_as_the_new_version(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": version_1_data(),
    }
    storage = KraftvaktStorage(hass)

    await storage.async_save(await storage.async_load())

    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert "turn_on" not in stored["data"]["appliances"][0]
    assert stored["data"]["appliances"][1]["actions"] == {
        "main": {"turn_on": {"mode": "default"}, "turn_off": {"mode": "default"}}
    }


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


async def test_version_1_without_appliances_is_read(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": {"general": {"power_limit_w": 8000}},
    }

    stored = await KraftvaktStorage(hass).async_load()

    assert stored.config.general.power_limit_w == 8000
