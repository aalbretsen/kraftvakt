"""Black box tests of the simulator's config flow."""

from typing import Any

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kraftvakt_simulator.const import DOMAIN, DeviceKind

from .conftest import CHARGER, HAN, HEATER, AddDevice, power, state


async def start_flow(hass: HomeAssistant, kind: DeviceKind) -> dict[str, Any]:
    """Start adding a device and choose its kind in the menu."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["han", "heater", "charger"]
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": kind}
    )


@pytest.mark.parametrize(
    ("kind", "title", "settings"),
    [
        (DeviceKind.HAN, "HAN", HAN),
        (DeviceKind.HEATER, "Bathroom floor", HEATER),
        (DeviceKind.CHARGER, "Garage", CHARGER),
    ],
)
async def test_adding_a_device_creates_a_config_entry(
    hass: HomeAssistant, kind: DeviceKind, title: str, settings: dict[str, Any]
) -> None:
    result = await start_flow(hass, kind)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == kind

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": title, **settings}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == title
    assert result["data"] == {"kind": kind, **settings}
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.state is config_entries.ConfigEntryState.LOADED


async def test_there_can_only_be_one_han(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    await add_device(DeviceKind.HAN, "HAN")

    result = await start_flow(hass, DeviceKind.HAN)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_han"


async def test_charger_maximum_current_must_be_at_least_the_minimum(
    hass: HomeAssistant,
) -> None:
    result = await start_flow(hass, DeviceKind.CHARGER)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Garage", "min_current_a": 10, "max_current_a": 8}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"max_current_a": "max_below_min"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Garage", "min_current_a": 10, "max_current_a": 10}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfiguring_a_heater_changes_its_settings(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    entry = await add_device(DeviceKind.HEATER, "Heating cable", duty_cycle_pct=100)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "heater"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**HEATER, "name": "Heating cable", "power_w": 1200, "duty_cycle_pct": 100},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["power_w"] == 1200
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.heating_cable"}, blocking=True
    )
    assert power(hass, "sensor.heating_cable_power") == 1200


async def test_reconfiguring_the_han_changes_the_background_power(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    entry = await add_device(DeviceKind.HAN, "HAN")

    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "han"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "HAN", "background_w": 5000}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert float(state(hass, "number.han_background_power")) == 5000
    assert power(hass, "sensor.han_power") == 5000


async def test_reconfiguring_shows_the_errors_of_the_kind(
    hass: HomeAssistant, add_device: AddDevice
) -> None:
    entry = await add_device(DeviceKind.CHARGER, "Garage")

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Garage", "min_current_a": 16, "max_current_a": 6}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "charger"
    assert result["errors"] == {"max_current_a": "max_below_min"}
