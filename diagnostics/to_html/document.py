"""The HTML document of a diagnostics file.

Every section is shown by the same rules, so sections added to the diagnostics show up without changes here:
a list or an object is a tree that expands and collapses, and a list of flat objects is a table.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from html import escape
from itertools import count
from typing import Any, Final

from ..diagnostics_file import DiagnosticsFile

# Levels of the tree below a section that are expanded when the document opens.
OPEN_LEVELS: Final = 2
# Keys whose values name an item in a list, shown next to its index while it is collapsed.
NAMING_KEYS: Final = ("name", "id", "entity_id", "time")

STYLE: Final = """
:root { color-scheme: light dark; font: 14px/1.5 system-ui, sans-serif; scroll-padding-top: 7rem; }
body { margin: 0 1rem 2rem; }
header { position: sticky; top: 0; background: Canvas; border-bottom: 1px solid GrayText; padding: 0.5rem 0; }
h1 { display: inline; font-size: 1.1rem; margin-right: 1rem; }
header div, header p { margin: 0.25rem 0; }
nav a { margin-right: 0.75rem; white-space: nowrap; }
summary { cursor: pointer; }
summary small { color: GrayText; }
.literal { font-family: ui-monospace, monospace; }
details > :not(summary) { margin-left: 1.25rem; }
main > details { margin-top: 0.75rem; }
main > details > summary { font-size: 1.1rem; font-weight: 600; }
ul, ol { list-style: none; margin: 0; padding: 0; }
.key { font-weight: 600; }
.value { white-space: pre-wrap; overflow-wrap: break-word; }
div.table { overflow-x: auto; }
table { border-collapse: collapse; }
th, td { border: 1px solid GrayText; padding: 0.1rem 0.4rem; text-align: left; vertical-align: top; }
"""


def html_document(diagnostics: DiagnosticsFile, file_name: str) -> str:
    """Return the document: a header with the table of contents, then a section for each part of the diagnostics and of Home Assistant's wrapper."""
    manifest = diagnostics.wrapper.get("integration_manifest")
    manifest = manifest if isinstance(manifest, Mapping) else {}
    home_assistant = diagnostics.wrapper.get("home_assistant")
    home_assistant = home_assistant if isinstance(home_assistant, Mapping) else {}
    name = str(manifest.get("name", "Integration"))
    integration = f"{name} {manifest['version']}" if "version" in manifest else name
    versions = f"{integration}, Home Assistant {home_assistant.get('version', 'unknown')}"
    numbers = count(1)
    navigation, sections = [], []
    for group, part in ((integration, diagnostics.data), ("Home Assistant", diagnostics.wrapper)):
        links = []
        for key, value in part.items():
            anchor = f"s{next(numbers)}"
            links.append(f'<a href="#{anchor}">{escape(key)}</a>')
            sections.append(_details(key, value, level=0, anchor=anchor))
        navigation.append(f"<p><strong>{escape(group)}:</strong> {' '.join(links)}</p>")
    buttons = "".join(
        f'<button type="button" onclick="document.querySelectorAll(\'details\').forEach(d => d.open = {state})">{label}</button> '
        for label, state in (("Expand all", "true"), ("Collapse all", "false"))
    )
    title = f"{name} diagnostics"
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escape(title)}: {escape(file_name)}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f"<header>\n<div><h1>{escape(title)}</h1>{escape(file_name)}: {escape(versions)}. {buttons}</div>\n<nav>{''.join(navigation)}</nav>\n</header>\n"
        f"<main>\n{''.join(sections)}\n</main>\n</body>\n</html>\n"
    )


def _details(label: str, value: Any, level: int, anchor: str | None = None) -> str:
    """Return a value under a label that expands and collapses, or on one line when it is a plain value or empty."""
    identity = f' id="{anchor}"' if anchor else ""
    if not _is_container(value) or not value:
        return f'<div{identity}><span class="key">{escape(label)}:</span> {_plain(value)}</div>'
    unit = "item" if isinstance(value, list) else "key"
    summary = f'<summary><span class="key">{escape(label)}</span> <small>{len(value)} {unit}{"" if len(value) == 1 else "s"}</small></summary>'
    return f"<details{identity}{' open' if level <= OPEN_LEVELS else ''}>{summary}{_tree(value, level + 1)}</details>"


def _tree(value: Mapping[str, Any] | list[Any], level: int) -> str:
    if isinstance(value, Mapping):
        return "<ul>" + "".join(f"<li>{_details(str(key), item, level)}</li>" for key, item in value.items()) + "</ul>"
    if all(isinstance(item, Mapping) and all(_fits_in_cell(cell) for cell in item.values()) for item in value):
        return _table(value)
    if not any(_is_container(item) for item in value):
        return "<ol>" + "".join(f'<li><span class="value">{_plain(item)}</span></li>' for item in value) + "</ol>"
    return "<ol>" + "".join(f"<li>{_details(_item_label(index, item), item, level)}</li>" for index, item in enumerate(value)) + "</ol>"


def _table(rows: list[Mapping[str, Any]]) -> str:
    """Return a list of flat objects as a table with a column for every key, since each object is then one line to compare with the others."""
    columns = list(dict.fromkeys(key for row in rows for key in row))
    header = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    lines = "".join("<tr>" + "".join(f'<td class="value">{_cell(row[column]) if column in row else ""}</td>' for column in columns) + "</tr>" for row in rows)
    return f'<div class="table"><table><thead><tr>{header}</tr></thead><tbody>{lines}</tbody></table></div>'


def _cell(value: Any) -> str:
    """Return a value in a table cell, with each item of a list or an object on a line of its own."""
    if isinstance(value, Mapping) and value:
        return "<br>".join(f'<span class="key">{escape(str(key))}:</span> {_inline(item)}' for key, item in value.items())
    if isinstance(value, list) and value:
        return "<br>".join(_inline(item) for item in value)
    return _plain(value)


def _inline(value: Any) -> str:
    """Return a flat value on one line, the items of a list or an object separated by commas."""
    if isinstance(value, Mapping) and value:
        return ", ".join(f'<span class="key">{escape(str(key))}:</span> {_plain(item)}' for key, item in value.items())
    if isinstance(value, list) and value:
        return ", ".join(_plain(item) for item in value)
    return _plain(value)


def _plain(value: Any) -> str:
    """Return a plain value: a string as it is, and anything else as in JSON, marked so it is not taken for a string."""
    if isinstance(value, str) and value:
        return f'<span class="value">{escape(value)}</span>'
    return f'<span class="literal">{escape(json.dumps(value, ensure_ascii=False))}</span>'


def _item_label(index: int, item: Any) -> str:
    names = [str(item[key]) for key in NAMING_KEYS if isinstance(item, Mapping) and isinstance(item.get(key), str | int)]
    return " ".join([str(index), *names])


def _is_container(value: Any) -> bool:
    return isinstance(value, Mapping | list)


def _items(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        return list(value.values())
    return value if isinstance(value, list) else []


def _is_flat(value: Any) -> bool:
    """Return whether the value is plain, or a list or an object of plain values."""
    return not any(_is_container(item) for item in _items(value))


def _fits_in_cell(value: Any) -> bool:
    """Return whether the value is flat, or a list or an object of flat values, so it shows in a table cell with one line for each item."""
    return all(_is_flat(item) for item in _items(value))
