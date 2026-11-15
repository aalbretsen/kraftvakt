"""The HTML document of a diagnostics file from the test harness."""

import json
import runpy
import sys
from pathlib import Path

import pytest

from diagnostics.to_html import main


def test_every_section_of_the_file_is_in_the_document(diagnostics_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(diagnostics_file)]) == 0

    output = diagnostics_file.with_suffix(".html")
    assert capsys.readouterr().out == f"Wrote {output}\n"
    html = output.read_text()
    content = json.loads(diagnostics_file.read_text())
    sections = [*content["data"], *(key for key in content if key != "data")]
    assert "home_assistant" in sections and "charger_devices" in sections
    assert all(f">{section}</a>" in html for section in sections)
    assert "&lt;b&gt;Garage&lt;/b&gt; &amp; more" in html
    assert "<th>entity_id</th>" in html
    assert '<td class="value"><span class="value">sensor.driveway_status</span></td>' in html


def test_the_document_is_written_where_asked(diagnostics_file: Path, tmp_path: Path) -> None:
    output = tmp_path / "report.html"

    assert main([str(diagnostics_file), "--output", str(output)]) == 0

    assert output.read_text().startswith("<!doctype html>")


def test_a_file_that_is_not_json_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "diagnostics.json"
    path.write_text("not json")

    assert main([str(path)]) == 1

    assert "cannot be read as JSON" in capsys.readouterr().err
    assert not path.with_suffix(".html").exists()


def test_runs_as_a_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "diagnostics.json"
    path.write_text('{"data": {}}')
    monkeypatch.setattr(sys, "argv", ["to_html", str(path)])
    monkeypatch.delitem(sys.modules, "diagnostics.to_html")

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_module("diagnostics.to_html", run_name="__main__")

    assert exit_info.value.code == 0
    assert path.with_suffix(".html").exists()
