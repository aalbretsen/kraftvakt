"""The HTML document of a diagnostics file: every section by the same rules, so new sections show up by themselves."""

import re
from html.parser import HTMLParser
from typing import Any

from diagnostics.diagnostics_file import DiagnosticsFile
from diagnostics.to_html import html_document

WRAPPER = {"home_assistant": {"version": "2026.10.4"}, "integration_manifest": {"name": "Kraftvakt", "version": "0.8.0"}}


class Structure(HTMLParser):
    """Checks that every element that is opened is closed in order, and collects the text."""

    VOID = frozenset({"meta", "br"})

    def __init__(self) -> None:
        super().__init__()
        self.open: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.VOID:
            self.open.append(tag)

    def handle_endtag(self, tag: str) -> None:
        assert self.open.pop() == tag

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def document(data: dict[str, Any], wrapper: dict[str, Any] | None = None) -> str:
    html = html_document(DiagnosticsFile({**(WRAPPER if wrapper is None else wrapper), "data": data}), "kraftvakt.json")
    structure = Structure()
    structure.feed(html)
    assert structure.open == ["html"] or structure.open == []
    return html


def test_the_table_of_contents_links_every_section_of_the_diagnostics_and_of_the_wrapper() -> None:
    html = document({"config": {"general": {}}, "engine": {"state": {"running": True}}})

    assert "<title>Kraftvakt diagnostics: kraftvakt.json</title>" in html
    assert "kraftvakt.json: Kraftvakt 0.8.0, Home Assistant 2026.10.4." in html
    assert re.findall(r'<a href="#(s\d)">(\w+)</a>', html) == [("s1", "config"), ("s2", "engine"), ("s3", "home_assistant"), ("s4", "integration_manifest")]
    assert all(f'id="s{number}"' in html for number in range(1, 5))


def test_a_file_without_a_manifest_still_gets_a_title() -> None:
    html = document({"empty": {}}, wrapper={})

    assert "<h1>Integration diagnostics</h1>" in html
    assert "Integration, Home Assistant unknown." in html
    assert '<div id="s1"><span class="key">empty:</span> <span class="literal">{}</span></div>' in html


def test_objects_and_lists_expand_and_collapse_and_are_open_two_levels_below_a_section() -> None:
    html = document({"section": {"one": {"two": {"three": {"four": 4}}}}}, wrapper={})

    assert re.findall(r"<details[^>]*>", html) == ['<details id="s1" open>', "<details open>", "<details open>", "<details>"]
    assert '<summary><span class="key">three</span> <small>1 key</small></summary>' in html
    assert '<span class="key">four:</span> <span class="literal">4</span>' in html


def test_plain_values_are_shown_as_strings_or_as_in_json() -> None:
    html = document({"values": {"text": "on", "empty": "", "none": None, "flag": False, "number": 1.5, "list": []}})

    assert '<span class="key">text:</span> <span class="value">on</span>' in html
    assert '<span class="key">empty:</span> <span class="literal">&quot;&quot;</span>' in html
    assert '<span class="key">none:</span> <span class="literal">null</span>' in html
    assert '<span class="key">flag:</span> <span class="literal">false</span>' in html
    assert '<span class="key">number:</span> <span class="literal">1.5</span>' in html
    assert '<span class="key">list:</span> <span class="literal">[]</span>' in html


def test_a_list_of_flat_objects_is_a_table_with_a_column_for_every_key() -> None:
    rows = [
        {"time": "10:00", "commands": ["TurnOn(a)", "TurnOff(b)"], "attributes": {"unit": "W", "options": ["on", "off"]}},
        {"time": "10:01", "waiting": None},
    ]

    html = document({"recent_decisions": rows})

    assert "<tr><th>time</th><th>commands</th><th>attributes</th><th>waiting</th></tr>" in html
    assert '<td class="value"><span class="value">TurnOn(a)</span><br><span class="value">TurnOff(b)</span></td>' in html
    assert '<span class="key">options:</span> <span class="value">on</span>, <span class="value">off</span>' in html
    assert '<td class="value"></td><td class="value"></td><td class="value"><span class="literal">null</span></td>' in html


def test_a_list_of_nested_objects_is_a_tree_named_by_the_items() -> None:
    groups = [{"id": "g1", "name": "Garage", "chargers": [{"id": "c1", "actions": {"steps": [{"action": "a"}]}}]}, {"other": {}}]

    html = document({"charger_groups": groups})

    assert "<table>" not in html.split("chargers")[0]
    assert '<summary><span class="key">0 Garage g1</span> <small>3 keys</small></summary>' in html
    assert '<summary><span class="key">1</span> <small>1 key</small></summary>' in html


def test_a_list_of_plain_values_is_a_list() -> None:
    html = document({"integrations": ["easee", 2, {"nested": [1]}], "services": ["a", None]})

    assert '<ol><li><span class="value"><span class="value">a</span></span></li><li><span class="value"><span class="literal">null</span></span></li></ol>' in html
    assert '<summary><span class="key">2</span> <small>1 key</small></summary>' in html


def test_every_key_and_value_is_escaped() -> None:
    html = document({"<script>": {"name": "<b>Garage</b> & more", "rows": [{"<i>": "<u>"}]}}, wrapper={"integration_manifest": {"name": "<Kraft>"}})

    assert "<script>" not in html
    assert "<b>" not in html and "<i>" not in html and "<u>" not in html and "<Kraft>" not in html
    assert "&lt;b&gt;Garage&lt;/b&gt; &amp; more" in html
    assert "<th>&lt;i&gt;</th>" in html
