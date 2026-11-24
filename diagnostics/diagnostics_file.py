"""The file Download diagnostics gives: Home Assistant's wrapper, with Kraftvakt's diagnostics under `data`."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from custom_components.kraftvakt.config_model import ConfigValidationError, KraftvaktConfig
from custom_components.kraftvakt.config_reader import read_config


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
    def config(self) -> KraftvaktConfig:
        """Return Kraftvakt's configuration, read by the integration's own rules."""
        config_data = self.data.get("config")
        if not isinstance(config_data, Mapping):
            raise NotADiagnosticsFileError("The diagnostics have no Kraftvakt configuration")
        try:
            return read_config(config_data)
        except ConfigValidationError as error:
            raise NotADiagnosticsFileError(f"The Kraftvakt configuration in the diagnostics cannot be read: {error}") from error

    @property
    def history(self) -> Mapping[str, Any]:
        """Return the recorded history of the entities the regulation reads and sets."""
        history: Any = self.data.get("history")
        if not isinstance(history, Mapping):
            raise NotADiagnosticsFileError("The diagnostics have no recorded history: the recorder was not loaded, or the file is from a version of Kraftvakt without it")
        return history

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
