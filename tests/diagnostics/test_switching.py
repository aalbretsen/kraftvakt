"""The switching report of a diagnostics file downloaded from the test harness with the recorder."""

import json
import runpy
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder import Recorder
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import _get_diagnostics_for_config_entry
from pytest_homeassistant_custom_component.components.recorder.common import async_wait_recording_done
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION
from diagnostics.switching.__main__ import main

DEFAULT = {"mode": "default"}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(recorder_mock: Recorder, enable_custom_integrations: None) -> None:
    """Start the recorder before Home Assistant, which the recorder requires."""


@pytest.fixture
async def diagnostics_file(hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_storage: dict[str, Any], freezer: FrozenDateTimeFactory, tmp_path: Path) -> Path:
    """Return the file Download diagnostics gives after a charger's current went up and down, and its on/off entity was switched."""
    for domain, service in (("light", "turn_on"), ("light", "turn_off"), ("input_boolean", "turn_on"), ("input_boolean", "turn_off"), ("input_number", "set_value")):
        hass.services.async_register(domain, service, lambda call: None)
    charger = {
        "id": "c",
        "on_off_entity": "input_boolean.charger",
        "set_current": {"mode": "entity", "entity_id": "input_number.current"},
        "car_connected": {"type": "entity", "value": "binary_sensor.car"},
        "charging_power": {"type": "power_sensor", "value": "sensor.charger_power"},
    }
    data = {
        "general": {"power_sensor": "sensor.han_power"},
        "appliances": [{"id": "a", "entity_id": "light.water_heater", "turn_on": DEFAULT, "turn_off": DEFAULT}],
        "charger_groups": [{"id": "g", "name": "Garage", "chargers": [charger]}],
    }
    hass_storage[STORAGE_KEY] = {"version": STORAGE_VERSION, "minor_version": 1, "key": STORAGE_KEY, "data": data}
    now = dt_util.utcnow()
    changes = [
        ("input_number.current", ["6", "7", "8", "7", "8", "unavailable", "8"]),
        ("input_boolean.charger", [STATE_ON, STATE_OFF, STATE_ON]),
    ]
    for entity_id, states in changes:
        for minute, state in enumerate(states):
            freezer.move_to(now - timedelta(hours=1) + timedelta(minutes=minute))
            hass.states.async_set(entity_id, state)
            await async_wait_recording_done(hass)
    freezer.move_to(now)
    assert await async_setup_component(hass, "diagnostics", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    content = await _get_diagnostics_for_config_entry(hass, hass_client, entry)
    path = tmp_path / "kraftvakt-diagnostics.json"
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return path


def test_the_report_counts_the_changes_of_each_charger_and_appliance(diagnostics_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(diagnostics_file)]) == 0

    report = capsys.readouterr().out
    assert report.startswith("Recorded history from ")
    sections = report.split("\n\n")
    assert sections[1].startswith("Power sensor and regulation\n")
    assert "switch.kraftvakt_regulation " in sections[1]
    assert sections[2].startswith("Appliance light.water_heater\n")
    charger = sections[3].splitlines()
    assert charger[0] == "EV charger input_boolean.charger in Garage"
    assert charger[1].split() == ["entity", "fields", "changes", "up", "down", "reversals", "shortest", "hold", "busiest", "hour", "lost", "values"]
    current = next(line for line in charger if line.lstrip().startswith("input_number.current"))
    assert current.split()[:8] == ["input_number.current", "set_current", "4", "3", "1", "2", "60", "s"]
    assert current.split()[-1] == "1"
    on_off = next(index for index, line in enumerate(charger) if line.lstrip().startswith("input_boolean.charger"))
    assert charger[on_off].split()[:6] == ["input_boolean.charger", "controlled_entity", "2", "-", "-", "-"]
    assert charger[on_off + 1] == "    changes to: off 1, on 1"


def test_a_file_without_history_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "diagnostics.json"
    path.write_text(json.dumps({"data": {"config": {}, "history": None}}))

    assert main([str(path)]) == 1

    assert "no recorded history" in capsys.readouterr().err


def test_runs_as_a_module(diagnostics_file: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["switching", str(diagnostics_file)])
    monkeypatch.delitem(sys.modules, "diagnostics.switching.__main__")

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("diagnostics.switching", run_name="__main__")

    assert exit_info.value.code == 0
    assert "EV charger" in capsys.readouterr().out
