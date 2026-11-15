"""The charger profile extractor on a diagnostics file from the test harness: its draft fills the charger again on any device of the kind."""

import runpy
import sys
from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kraftvakt.charger_profiles import recognition
from diagnostics.charger_profile.__main__ import PROFILE_TESTS, PROFILES, main

from ..charger_profiles.conftest import Command
from .drafted import PROFILE_TESTS_PACKAGE, PROFILES_PACKAGE, load


async def test_drafted_profile_passes_its_drafted_test(
    hass: HomeAssistant, command: Command, diagnostics_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main([str(diagnostics_file), "--output", str(tmp_path)]) == 0

    report = capsys.readouterr().out
    assert "Charger c1: Example EX-1" in report
    assert "car_connected: the template names sun.sun, which is not on the charger's device." in report
    profile = load(tmp_path / PROFILES / "example_ex_1.py", PROFILES_PACKAGE).PROFILE
    assert profile.cloud_controlled
    drafted_test = load(tmp_path / PROFILE_TESTS / "test_example_ex_1.py", PROFILE_TESTS_PACKAGE)
    monkeypatch.setattr(recognition, "PROFILES", (profile,))
    await drafted_test.test_example_ex_1_fills_the_fields_of_a_charger(hass, command)


async def test_drafts_are_not_written_over_existing_files(diagnostics_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    existing = tmp_path / PROFILES / "example_ex_1.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("kept")

    assert main([str(diagnostics_file), "--output", str(tmp_path)]) == 0

    assert existing.read_text() == "kept"
    assert not (tmp_path / PROFILE_TESTS / "test_example_ex_1.py").exists()
    assert f"Not written, since {PROFILES / 'example_ex_1.py'} exists." in capsys.readouterr().out


def test_a_file_that_is_not_from_download_diagnostics_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "config.json"
    path.write_text('{"config": {}}')

    assert main([str(path)]) == 1

    assert "is not a diagnostics file from Home Assistant" in capsys.readouterr().err


def test_runs_as_a_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "diagnostics.json"
    path.write_text('{"data": {"config": {"charger_groups": [{"id": "g1", "chargers": [{"id": "c1"}]}]}, "charger_devices": {}}}')
    monkeypatch.setattr(sys, "argv", ["charger_profile", str(path)])
    monkeypatch.delitem(sys.modules, "diagnostics.charger_profile.__main__")

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("diagnostics.charger_profile", run_name="__main__")

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == "Charger c1 has no device.\nNo charger in the file is filled in by hand.\n"
