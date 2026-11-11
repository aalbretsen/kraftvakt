"""Kraftvakt regulating the simulated devices, end to end in Home Assistant."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt.const import DOMAIN as KRAFTVAKT
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION
from custom_components.kraftvakt_simulator.const import DeviceKind

from .conftest import AddDevice, call, power, state

DEFAULT = {"mode": "default"}
HOUSE_POWER = "sensor.han_power"
WATER_HEATER = "switch.water_heater"
CHARGING_ALLOWED = "switch.garage_charging_allowed"
CHARGING_POWER = "sensor.garage_charging_power"
THERMOSTAT = "climate.hall"
THERMOSTAT_POWER = "sensor.hall_power"


def kraftvakt_config() -> dict[str, Any]:
    """Return a configuration of Kraftvakt against the simulated devices."""
    return {
        "general": {
            "power_sensor": HOUSE_POWER,
            "power_limit_w": 10000,
            "regulation_window_s": 60,
            "regulation_interval": 1,
            "wait_at_limit_s": 0,
            "penalty_threshold_w": 1000,
        },
        "appliances": [
            {
                "id": "a1",
                "entity_id": WATER_HEATER,
                "turn_on": DEFAULT,
                "turn_off": DEFAULT,
            }
        ],
        "priority": [
            {"type": "appliance", "appliance_id": "a1", "variant_id": None},
            {"type": "ev_charging"},
        ],
        "charging": {
            "enabled": True,
            "one_at_a_time": True,
            "chargers": [
                {
                    "id": "c1",
                    "entity_id": CHARGING_ALLOWED,
                    "activate": DEFAULT,
                    "deactivate": DEFAULT,
                    "set_current": {
                        "mode": "custom",
                        "action": [
                            {
                                "action": "number.set_value",
                                "target": {
                                    "entity_id": "number.garage_charging_current"
                                },
                                "data": {"value": "{{ current }}"},
                            }
                        ],
                    },
                    "min_current_a": 6,
                    "max_current_a": 16,
                    "actively_charging": {
                        "type": "power_sensor",
                        "value": CHARGING_POWER,
                    },
                    "car_connected": {
                        "type": "entity",
                        "value": "switch.garage_car_connected",
                    },
                }
            ],
        },
    }


async def regulate_until(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    condition: Callable[[], bool],
    max_windows: int = 30,
) -> None:
    """Let regulation windows pass until `condition` is true."""
    for _ in range(max_windows):
        if condition():
            return
        freezer.tick(timedelta(seconds=60))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)
    assert condition()


async def setup_kraftvakt(
    hass: HomeAssistant, hass_storage: dict[str, Any], config: dict[str, Any]
) -> None:
    """Set up Kraftvakt with the configuration, which starts the regulation."""
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": config,
    }
    entry = MockConfigEntry(domain=KRAFTVAKT)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_kraftvakt_regulates_the_simulated_devices(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    add_device: AddDevice,
) -> None:
    await add_device(DeviceKind.HAN, "HAN", background_w=3000)
    await add_device(
        DeviceKind.HEATER,
        "Water heater",
        heater_type="water_heater",
        power_w=2000,
        duty_cycle_pct=100,
    )
    await add_device(DeviceKind.CHARGER, "Garage")
    await call(hass, "switch", "turn_on", "switch.garage_car_connected")
    await setup_kraftvakt(hass, hass_storage, kraftvakt_config())

    await regulate_until(
        hass,
        freezer,
        lambda: (
            state(hass, WATER_HEATER) == STATE_ON and power(hass, CHARGING_POWER) > 0
        ),
    )
    assert power(hass, HOUSE_POWER) <= 10_000

    await call(hass, "number", "set_value", "number.han_background_power", value=9000)
    await regulate_until(
        hass,
        freezer,
        lambda: (
            state(hass, WATER_HEATER) == STATE_OFF
            and state(hass, CHARGING_ALLOWED) == STATE_OFF
        ),
    )
    assert power(hass, HOUSE_POWER) == 9000


async def test_kraftvakt_controls_a_thermostat_with_its_domain_actions(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
    add_device: AddDevice,
) -> None:
    """On sets heat and 22 °C, off sets 8 °C, below the room's 10 °C."""
    await add_device(DeviceKind.HAN, "HAN", background_w=3000)
    await add_device(
        DeviceKind.THERMOSTAT,
        "Hall",
        power_w=2000,
        duty_cycle_pct=100,
        room_temperature=10,
    )
    config = kraftvakt_config()
    config["charging"] = {"enabled": False}
    config["priority"] = config["priority"][:1]
    config["appliances"][0].update(
        entity_id=THERMOSTAT,
        turn_on={
            "mode": "domain",
            "domain_action": "climate_hvac_mode_and_temperature",
            "data": {"hvac_mode": "heat", "temperature": 22},
        },
        turn_off={
            "mode": "domain",
            "domain_action": "climate_temperature",
            "data": {"temperature": 8},
        },
    )
    await setup_kraftvakt(hass, hass_storage, config)

    await regulate_until(hass, freezer, lambda: power(hass, THERMOSTAT_POWER) > 0)
    assert state(hass, THERMOSTAT) == "heat"

    await call(hass, "number", "set_value", "number.han_background_power", value=9000)
    await regulate_until(hass, freezer, lambda: power(hass, THERMOSTAT_POWER) == 0)
    assert state(hass, THERMOSTAT) == "heat"
