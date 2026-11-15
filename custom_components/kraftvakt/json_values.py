"""State held in memory as JSON, for the diagnostics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from homeassistant.util import dt as dt_util


def plain(value: Any) -> Any:
    """Return the value as JSON: times in ISO 8601 in Home Assistant's time zone, durations in seconds, enums as their values, sets sorted and dataclasses as objects.

    An object that is not a dataclass describes itself with `diagnostics()`.
    """
    match value:
        case Enum():
            return plain(value.value)
        case None | bool() | int() | float() | str():
            return value
        case datetime():
            return dt_util.as_local(value).isoformat()
        case timedelta():
            return value.total_seconds()
        case Mapping():
            return {str(key): plain(item) for key, item in value.items()}
        case set() | frozenset():
            return sorted((plain(item) for item in value), key=str)
        case Sequence():
            return [plain(item) for item in value]
        case _ if is_dataclass(value) and not isinstance(value, type):
            return {field.name: plain(getattr(value, field.name)) for field in fields(value)}
        case _ if hasattr(value, "diagnostics"):
            return plain(value.diagnostics())
    raise TypeError(f"{type(value).__name__} cannot be shown in the diagnostics")
