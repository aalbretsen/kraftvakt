"""Black box tests of the capacity average filled from the recorder at startup."""

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder import Recorder
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION

from .test_sensor import POWER_SENSOR, WINDOW, advance, set_power, state_of


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    recorder_mock: Recorder, enable_custom_integrations: None
) -> None:
    """Start the recorder before Home Assistant, which the recorder requires."""


async def setup_kraftvakt(hass: HomeAssistant, hass_storage: dict[str, Any]) -> None:
    hass_storage[STORAGE_KEY] = {
        "version": STORAGE_VERSION,
        "minor_version": 1,
        "key": STORAGE_KEY,
        "data": {
            "general": {
                "power_sensor": POWER_SENSOR,
                "regulation_window_s": int(WINDOW.total_seconds()),
            }
        },
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


async def record_power(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, when, value: str
) -> None:
    freezer.move_to(when)
    set_power(hass, value)
    await async_wait_recording_done(hass)


async def test_capacity_average_starts_from_the_recorded_history(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
) -> None:
    """The hour before the start is taken from the recorder.

    2 kW until 20 minutes before the start, unavailable for a while (the last
    valid value holds), then 8 kW: the first window's hour has 39 minutes of
    2 kW and 21 minutes of 8 kW.
    """
    started = dt_util.utcnow()
    await record_power(hass, freezer, started - timedelta(minutes=70), "2000")
    await record_power(hass, freezer, started - timedelta(minutes=50), "unavailable")
    await record_power(hass, freezer, started - timedelta(minutes=20), "8000")
    freezer.move_to(started)

    await setup_kraftvakt(hass, hass_storage)
    await advance(hass, freezer, WINDOW)

    assert float(state_of(hass, "capacity_average")) == pytest.approx(4.1)
    assert float(state_of(hass, "regulation_average")) == pytest.approx(8.0)


async def test_capacity_average_without_history_uses_the_first_measurement(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    hass_storage: dict[str, Any],
) -> None:
    """A power sensor without recorded history fills the hour as before."""
    set_power(hass, "3000")

    await setup_kraftvakt(hass, hass_storage)
    await advance(hass, freezer, WINDOW)

    assert float(state_of(hass, "capacity_average")) == pytest.approx(3.0)
