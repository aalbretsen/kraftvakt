"""Black box tests of the simulated HAN."""

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt_simulator.const import DeviceKind
from custom_components.kraftvakt_simulator.model import three_phase_power_w

from .conftest import AddDevice, advance, call, power, reported_house_power, state

HOUSE_POWER = "sensor.han_power"
BACKGROUND = "number.han_background_power"


async def test_han_reports_the_background_power(hass: HomeAssistant, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HAN, "HAN")

    assert power(hass, HOUSE_POWER) == 3500
    assert float(state(hass, BACKGROUND)) == 3500
    sensor = hass.states.get(HOUSE_POWER)
    assert sensor is not None
    assert sensor.attributes["device_class"] == "power"
    assert sensor.attributes["state_class"] == "measurement"
    assert sensor.attributes["unit_of_measurement"] == "W"


async def test_han_sums_the_background_and_every_device(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HAN, "HAN")
    await add_device(DeviceKind.HEATER, "Heating cable", duty_cycle_pct=100)
    await add_device(DeviceKind.CHARGER, "Charger")

    await call(hass, "switch", "turn_on", "switch.heating_cable")
    assert await reported_house_power(hass, freezer) == 3500 + 750

    await call(hass, "switch", "turn_on", "switch.charger_car_connected")
    await call(hass, "switch", "turn_on", "switch.charger_charging_allowed")
    assert await reported_house_power(hass, freezer) == pytest.approx(3500 + 750 + three_phase_power_w(6))


async def test_han_set_up_after_the_devices_counts_them(hass: HomeAssistant, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HEATER, "Heating cable", duty_cycle_pct=100)
    await call(hass, "switch", "turn_on", "switch.heating_cable")

    await add_device(DeviceKind.HAN, "HAN")

    assert power(hass, HOUSE_POWER) == 3500 + 750


async def test_background_power_can_be_changed_and_is_kept(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    entry = await add_device(DeviceKind.HAN, "HAN")

    await call(hass, "number", "set_value", BACKGROUND, value=9200)

    assert await reported_house_power(hass, freezer) == 9200
    assert entry.data["background_w"] == 9200
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert power(hass, HOUSE_POWER) == 9200


async def test_unloaded_device_no_longer_counts(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    await add_device(DeviceKind.HAN, "HAN")
    heater = await add_device(DeviceKind.HEATER, "Heating cable")
    await call(hass, "switch", "turn_on", "switch.heating_cable")
    assert await reported_house_power(hass, freezer) == 3500 + 750

    assert await hass.config_entries.async_unload(heater.entry_id)
    await hass.async_block_till_done()
    assert await reported_house_power(hass, freezer) == 3500
    await advance(hass, freezer, timedelta(minutes=60))
    assert power(hass, HOUSE_POWER) == 3500


async def test_han_reports_every_10_seconds_also_without_change(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice) -> None:
    """As a HAN reader does, so Kraftvakt's power sensor timeout does not run out."""
    await add_device(DeviceKind.HAN, "HAN")
    first = hass.states.get(HOUSE_POWER)
    assert first is not None
    reported_at, changed_at = first.last_reported, first.last_changed

    await advance(hass, freezer, timedelta(seconds=10))

    again = hass.states.get(HOUSE_POWER)
    assert again is not None
    assert again.last_reported > reported_at
    assert again.last_changed == changed_at


@pytest.mark.parametrize("interval_s", [2, 10])
async def test_han_reports_a_change_only_at_its_interval(hass: HomeAssistant, freezer: FrozenDateTimeFactory, add_device: AddDevice, interval_s: int) -> None:
    """A real HAN reader reports what the meter measured at a fixed interval, not when a device changes."""
    await add_device(DeviceKind.HAN, "HAN", report_interval_s=str(interval_s))

    await call(hass, "number", "set_value", BACKGROUND, value=6000)
    await advance(hass, freezer, timedelta(seconds=interval_s - 1))
    assert power(hass, HOUSE_POWER) == 3500

    await advance(hass, freezer, timedelta(seconds=1))
    assert power(hass, HOUSE_POWER) == 6000
