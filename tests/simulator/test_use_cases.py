"""Use cases of Kraftvakt regulating a simulated house, end to end in Home Assistant.

Each test is a use case from a household's point of view. The simulated HAN reports the background power plus what every
simulated device draws, so the regulation sees the effect of its own commands as it would in a real house.
"""

from collections.abc import Callable
from datetime import timedelta
from itertools import pairwise
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.kraftvakt.const import DOMAIN as KRAFTVAKT
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION
from custom_components.kraftvakt_simulator.const import DeviceKind

from .conftest import AddDevice, call, power, state

DEFAULT = {"mode": "default"}
WINDOW = timedelta(seconds=60)
LIMIT_W = 10_000


class House:
    """A simulated house with Kraftvakt, driven one regulation window at a time."""

    def __init__(self, hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice) -> None:
        self.hass = hass
        self.freezer = freezer
        self.hass_storage = hass_storage
        self.add_device = add_device
        self.config: dict[str, Any] = {
            "general": {
                "power_sensor": "sensor.han_power",
                "power_limit_w": LIMIT_W,
                "regulation_window_updates": 1,
                "power_sensor_interval_s": WINDOW.total_seconds(),
                "penalty_threshold_w": 500,
            },
            "appliances": [],
            "priority": [],
            "charger_groups": [],
        }
        self.entry: MockConfigEntry | None = None

    async def han(self, background_w: int) -> MockConfigEntry:
        return await self.add_device(DeviceKind.HAN, "HAN", background_w=background_w)

    async def heater(self, name: str, power_w: int) -> str:
        """Add a heating device that draws its power all the time it is on, and return its switch."""
        await self.add_device(DeviceKind.HEATER, name, heater_type="heating_cable", power_w=power_w, duty_cycle_pct=100)
        return f"switch.{name.lower().replace(' ', '_')}"

    async def charger(self, name: str) -> str:
        await self.add_device(DeviceKind.CHARGER, name)
        return name.lower()

    def appliance(self, appliance_id: str, entity_id: str, **settings: Any) -> None:
        self.config["appliances"].append({"id": appliance_id, "entity_id": entity_id, "turn_on": DEFAULT, "turn_off": DEFAULT, **settings})
        self.config["priority"].append({"type": "appliance", "appliance_id": appliance_id, "variant_id": None})

    def variant(self, appliance_id: str, variant_id: str, template: str, place: int) -> None:
        appliance = next(item for item in self.config["appliances"] if item["id"] == appliance_id)
        appliance.setdefault("variants", []).append({"id": variant_id, "label": variant_id, "condition": {"type": "template", "value": template}})
        self.config["priority"].insert(place, {"type": "appliance", "appliance_id": appliance_id, "variant_id": variant_id})

    def charger_group(self, group_id: str, chargers: list[str]) -> None:
        """Add a group of the chargers with one EV charger at a time and the configured charging priority."""
        registry = er.async_get(self.hass)
        self.config["charger_groups"].append(
            {
                "id": group_id,
                "name": group_id,
                "one_at_a_time": True,
                "chargers": [
                    {
                        "id": name,
                        "device_id": registry.async_get(f"switch.{name}_charging_allowed").device_id,
                        "entity_id": f"switch.{name}_charging_allowed",
                        "activate": DEFAULT,
                        "deactivate": DEFAULT,
                        "set_current": {"mode": "entity", "entity_id": f"number.{name}_charging_current"},
                        "charging_power": {"type": "power_sensor", "value": f"sensor.{name}_charging_power"},
                        "car_connected": {"type": "entity", "value": f"switch.{name}_car_connected"},
                    }
                    for name in chargers
                ],
            }
        )
        self.config["priority"].append({"type": "charger_group", "group_id": group_id})

    async def start(self) -> None:
        """Set up Kraftvakt with the configuration, which starts the regulation with everything off."""
        self.hass_storage[STORAGE_KEY] = {"version": STORAGE_VERSION, "minor_version": 1, "key": STORAGE_KEY, "data": self.config}
        self.entry = MockConfigEntry(domain=KRAFTVAKT)
        self.entry.add_to_hass(self.hass)
        assert await self.hass.config_entries.async_setup(self.entry.entry_id)
        await self.hass.async_block_till_done(wait_background_tasks=True)

    async def windows(self, count: int = 1) -> None:
        for _ in range(count):
            self.freezer.tick(WINDOW)
            async_fire_time_changed(self.hass)
            await self.hass.async_block_till_done(wait_background_tasks=True)

    async def until(self, condition: Callable[[], bool], max_windows: int = 60) -> int:
        """Let windows pass until `condition` holds, and return how many it took."""
        for count in range(max_windows):
            if condition():
                return count
            await self.windows()
        assert condition()
        return max_windows

    def house_power(self) -> float:
        return power(self.hass, "sensor.han_power")

    def on(self, entity_id: str) -> bool:
        return state(self.hass, entity_id) == STATE_ON

    def kraftvakt(self, platform: str, key: str) -> str:
        return state(self.hass, f"{platform}.kraftvakt_{key}")

    def decisions(self) -> list[dict[str, Any]]:
        assert self.entry is not None
        return self.entry.runtime_data.recent_decisions

    async def set_background(self, background_w: int) -> None:
        await call(self.hass, "number", "set_value", "number.han_background_power", value=background_w)


async def test_use_case_1_heating_in_priority_order(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice) -> None:
    """Three heaters are turned on in priority order, and the lowest give way when the background rises.

    The heating cable is turned on again and again while it does not fit, each time after a longer waiting time,
    and the panel heater below it is never turned on, although it would fit, since the order is fixed.
    """
    house = House(hass, freezer, hass_storage, add_device)
    await house.han(background_w=3000)
    water_heater = await house.heater("Water heater", 2000)
    cable = await house.heater("Heating cable", 3000)
    panel = await house.heater("Panel heater", 1500)
    house.appliance("water_heater", water_heater)
    house.appliance("cable", cable)
    house.appliance("panel", panel)
    await house.start()

    await house.until(lambda: house.on(water_heater) and house.on(cable) and house.on(panel), max_windows=10)
    assert house.house_power() == 9500
    assert house.kraftvakt("sensor", "regulation_steps_on") == "3"

    await house.set_background(5500)
    await house.windows(2)
    assert house.on(water_heater)
    assert not house.on(cable)
    assert not house.on(panel)

    turned_on_at = []
    for minute in range(60):
        was_on = house.on(cable)
        await house.windows()
        if house.on(cable) and not was_on:
            turned_on_at.append(minute)
        assert not house.on(panel)
    gaps = [later - earlier for earlier, later in pairwise(turned_on_at)]
    assert gaps == [7, 10, 12, 15]
    assert float(house.kraftvakt("sensor", "power_tariff_average")) <= LIMIT_W


async def test_use_case_2_water_heater_first_in_the_morning(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice) -> None:
    """The variant Morning moves the water heater from the bottom to the top, and the lowest heater gives it room at once."""
    house = House(hass, freezer, hass_storage, add_device)
    await house.han(background_w=3000)
    cable = await house.heater("Heating cable", 3000)
    panel = await house.heater("Panel heater", 1500)
    water_heater = await house.heater("Water heater", 2000)
    house.appliance("cable", cable)
    house.appliance("panel", panel)
    house.appliance("water_heater", water_heater)
    house.variant("water_heater", "morning", "{{ is_state('input_boolean.morning', 'on') }}", place=0)
    hass.states.async_set("input_boolean.morning", STATE_OFF)
    await house.start()
    await house.until(lambda: house.on(cable) and house.on(panel) and house.on(water_heater), max_windows=10)

    await house.set_background(4500)
    await house.windows()
    assert not house.on(water_heater)
    assert house.on(panel)

    hass.states.async_set("input_boolean.morning", STATE_ON)
    await house.windows()
    assert not house.on(panel)
    assert house.on(cable)
    assert house.decisions()[-1]["commands"] == [
        {"command": "TurnOffAppliance", "appliance_id": "water_heater", "variant_id": "morning"},
        {"command": "TurnOffAppliance", "appliance_id": "panel", "variant_id": None},
    ]

    await house.until(lambda: house.on(water_heater), max_windows=10)
    assert not house.on(panel)
    assert house.house_power() == 9500


async def test_use_case_3_full_car_waits_at_the_minimum_current(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice) -> None:
    """A car charges with what is free, is set back to its minimum when full, and is cut back at once when the background jumps."""
    house = House(hass, freezer, hass_storage, add_device)
    await house.han(background_w=3000)
    garage = await house.charger("Garage")
    house.charger_group("home", [garage])
    await call(hass, "switch", "turn_on", "switch.garage_car_connected")
    await house.start()

    def current() -> float:
        return float(state(hass, "number.garage_charging_current"))

    await house.until(lambda: current() == 10, max_windows=60)
    await house.windows(10)
    assert current() == 10
    assert LIMIT_W - 100 <= house.house_power() <= LIMIT_W

    await call(hass, "switch", "turn_on", "switch.garage_car_fully_charged")
    await house.windows()
    assert current() == 6
    assert house.on("switch.garage_charging_allowed")
    await house.windows(5)
    assert current() == 6

    await call(hass, "switch", "turn_off", "switch.garage_car_fully_charged")
    await house.until(lambda: current() == 10, max_windows=60)

    await house.set_background(5000)
    await house.windows()
    assert current() == 7
    assert house.house_power() <= LIMIT_W


async def test_use_case_4_a_car_at_the_first_charger_takes_over(hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice) -> None:
    """With one EV charger at a time, a car at the charger first in the charging priority takes over from the one that charges."""
    house = House(hass, freezer, hass_storage, add_device)
    await house.han(background_w=2000)
    garage = await house.charger("Garage")
    carport = await house.charger("Carport")
    house.charger_group("home", [garage, carport])
    await call(hass, "switch", "turn_on", "switch.carport_car_connected")
    await house.start()

    def charger_state(charger_id: str) -> str:
        assert house.entry is not None
        return house.entry.runtime_data.chargers[charger_id].state.value

    await house.until(lambda: float(state(hass, "number.carport_charging_current")) >= 10, max_windows=60)
    assert charger_state("garage") == "no_car"

    await call(hass, "switch", "turn_on", "switch.garage_car_connected")
    await house.until(lambda: charger_state("garage") == "charging", max_windows=20)
    await house.windows()
    assert not house.on("switch.carport_charging_allowed")
    assert charger_state("carport") == "queued"
    assert power(hass, "sensor.carport_charging_power") == 0

    await call(hass, "switch", "turn_off", "switch.garage_car_connected")
    await house.until(lambda: charger_state("carport") == "charging", max_windows=20)
    assert charger_state("garage") == "no_car"


async def test_use_case_5_lost_power_sensor_keeps_only_the_freezer_on(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice
) -> None:
    """Without a valid measurement only the essential appliance is on, and the regulation starts again when the HAN is back."""
    house = House(hass, freezer, hass_storage, add_device)
    han = await house.han(background_w=3000)
    freezer_switch = await house.heater("Freezer", 300)
    water_heater = await house.heater("Water heater", 2000)
    house.appliance("freezer", freezer_switch, essential=True)
    house.appliance("water_heater", water_heater)
    await house.start()
    assert house.on(freezer_switch)
    await house.until(lambda: house.on(water_heater), max_windows=5)

    await hass.config_entries.async_unload(han.entry_id)
    await house.windows()
    assert house.kraftvakt("binary_sensor", "regulation_safe_state") == STATE_OFF
    assert house.on(water_heater)
    await house.windows()
    assert house.kraftvakt("binary_sensor", "regulation_safe_state") == STATE_ON
    assert house.kraftvakt("sensor", "power_regulation_average") == "unavailable"
    assert not house.on(water_heater)
    assert house.on(freezer_switch)

    assert await hass.config_entries.async_setup(han.entry_id)
    await house.windows()
    assert house.kraftvakt("binary_sensor", "regulation_safe_state") == STATE_OFF
    await house.until(lambda: house.on(water_heater), max_windows=5)
    assert house.on(freezer_switch)


async def test_use_case_6_penalty_when_an_unregulated_load_keeps_the_hour_too_high(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, hass_storage: dict[str, Any], add_device: AddDevice
) -> None:
    """A load Kraftvakt does not control keeps the tariff average above the limit plus the penalty threshold.

    Everything is turned off, also the freezer, until the overconsumption is paid back, and then the regulation starts again.
    """
    house = House(hass, freezer, hass_storage, add_device)
    await house.han(background_w=3000)
    freezer_switch = await house.heater("Freezer", 300)
    water_heater = await house.heater("Water heater", 2000)
    house.appliance("freezer", freezer_switch, essential=True)
    house.appliance("water_heater", water_heater)
    await house.start()
    await house.until(lambda: house.on(water_heater), max_windows=5)

    await house.set_background(12_000)
    await house.windows(2)
    assert not house.on(water_heater)
    assert house.on(freezer_switch)

    minutes = await house.until(lambda: house.kraftvakt("binary_sensor", "penalty_active") == STATE_ON, max_windows=90)
    assert float(house.kraftvakt("sensor", "power_tariff_average")) > LIMIT_W + 500
    assert minutes > 30
    assert not house.on(freezer_switch)

    await house.set_background(3000)
    await house.until(lambda: house.kraftvakt("binary_sensor", "penalty_active") == STATE_OFF, max_windows=90)
    assert house.on(freezer_switch)
    assert house.kraftvakt("sensor", "penalty_overconsumption") == "0.0"
    await house.until(lambda: house.on(water_heater), max_windows=5)
