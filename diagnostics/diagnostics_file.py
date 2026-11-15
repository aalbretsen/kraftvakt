"""The file Download diagnostics gives: Home Assistant's wrapper, with Kraftvakt's diagnostics under `data`."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class NotADiagnosticsFileError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DiagnosticsFile:
    content: Mapping[str, Any]

    @property
    def data(self) -> Mapping[str, Any]:
        data: Mapping[str, Any] = self.content["data"]
        return data

    @property
    def wrapper(self) -> Mapping[str, Any]:
        """Return what Home Assistant puts around the diagnostics: its own system information, the custom integrations, the manifest and more."""
        return {key: value for key, value in self.content.items() if key != "data"}


def read_diagnostics_file(path: Path) -> DiagnosticsFile:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NotADiagnosticsFileError(f"{path} cannot be read as JSON: {error}") from error
    if not isinstance(content, dict) or not isinstance(content.get("data"), dict):
        raise NotADiagnosticsFileError(f"{path} is not a diagnostics file from Home Assistant: it has no data object")
    return DiagnosticsFile(content)
