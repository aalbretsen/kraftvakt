"""Tests for storage of the configuration and the charger switches."""

from typing import Any

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.config_model import (
    ChargerSwitches,
    ConfigValidationError,
    KraftvaktConfig,
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
    config = KraftvaktConfig.from_dict(full_config_data())
    switches = {"c1": ChargerSwitches(excluded=True, window_override=True)}

    await KraftvaktStorage(hass).async_save(StoredData(config, switches))
    stored = await KraftvaktStorage(hass).async_load()

    assert stored == StoredData(config, switches)


async def test_stored_format_is_versioned_json(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    config = KraftvaktConfig.from_dict(full_config_data())

    await KraftvaktStorage(hass).async_save(StoredData(config))

    stored = hass_storage[STORAGE_KEY]
    assert stored["version"] == STORAGE_VERSION
    assert stored["data"] == {
        **full_config_data(),
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
            "charger_switches": {"c1": {"excluded": True, "window_override": False}},
        },
    }

    stored = await KraftvaktStorage(hass).async_load()

    assert stored.config == KraftvaktConfig.from_dict(full_config_data())
    assert stored.charger_switches == {"c1": ChargerSwitches(excluded=True)}


async def test_switches_follow_configured_chargers(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    data = full_config_data()
    data["charging"]["chargers"].append(
        {**data["charging"]["chargers"][0], "id": "c2", "entity_id": "switch.charger_2"}
    )
    config = KraftvaktConfig.from_dict(data)
    switches = {"gone": ChargerSwitches(excluded=True)}

    await KraftvaktStorage(hass).async_save(StoredData(config, switches))
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
