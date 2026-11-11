"""Helpers for the black box tests of the Kraftvakt simulator."""

from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.kraftvakt_simulator.const import DOMAIN, DeviceKind

type AddDevice = Callable[..., Awaitable[MockConfigEntry]]

HAN = {"background_w": 3500}
HEATER = {
    "heater_type": "heating_cable",
    "power_w": 750,
    "duty_cycle_pct": 25,
    "period_min": 60,
}
THERMOSTAT = {"power_w": 750, "duty_cycle_pct": 25, "period_min": 60}
CHARGER = {"min_current_a": 6, "max_current_a": 16}
SETTINGS = {
    DeviceKind.HAN: HAN,
    DeviceKind.HEATER: HEATER,
    DeviceKind.THERMOSTAT: THERMOSTAT,
    DeviceKind.CHARGER: CHARGER,
}


@pytest.fixture
def add_device(hass: HomeAssistant) -> AddDevice:
    """Return a function that sets up a simulated device with default settings."""

    async def add(kind: DeviceKind, title: str, **settings: Any) -> MockConfigEntry:
        entry = MockConfigEntry(
            domain=DOMAIN,
            title=title,
            data={"kind": kind, **SETTINGS[kind], **settings},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry

    return add


async def advance(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, delta: timedelta
) -> None:
    """Move the time forward and run what is due."""
    freezer.tick(delta)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


def state(hass: HomeAssistant, entity_id: str) -> str:
    """Return the state of an entity that must exist."""
    found = hass.states.get(entity_id)
    assert found is not None, entity_id
    return found.state


def power(hass: HomeAssistant, entity_id: str) -> float:
    """Return the state of a power sensor as a number."""
    return float(state(hass, entity_id))


async def call(
    hass: HomeAssistant, domain: str, service: str, entity_id: str, **data: Any
) -> None:
    """Call a service for one entity and wait for it."""
    await hass.services.async_call(
        domain, service, {"entity_id": entity_id, **data}, blocking=True
    )
    await hass.async_block_till_done()
