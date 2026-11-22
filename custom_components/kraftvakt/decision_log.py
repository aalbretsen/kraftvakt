"""The decisions kept for the diagnostics."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from .json_values import plain
from .measurement import TARIFF_WINDOW
from .regulation.model import Command, command_dict, without_superseded


class DecisionLog:
    """Keeps the decisions of the hour before the last one, and the commands that set the appliances and chargers before them.

    The commands before the decisions are those of the last start, with the
    commands of each later decision that has left the hour, so what each
    appliance and charger was set to is known from the last start on.
    """

    def __init__(self) -> None:
        self._decisions: deque[tuple[datetime, list[Command], dict[str, Any]]] = deque()
        self._before: tuple[datetime, list[Command]] | None = None

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return the decisions, oldest first, as JSON."""
        return [record for _, _, record in self._decisions]

    @property
    def commands_before(self) -> dict[str, Any] | None:
        """Return the commands before the decisions and when they had all been sent, as JSON, None before the first start."""
        if self._before is None:
            return None
        time, commands = self._before
        before: dict[str, Any] = plain({"time": time, "commands": [command_dict(command) for command in commands]})
        return before

    def start(self, now: datetime, commands: Sequence[Command]) -> None:
        self._before = (now, list(commands))

    def add(self, now: datetime, commands: Sequence[Command], record: dict[str, Any]) -> None:
        """Keep a decision with its commands and its record, and let the decisions that have left the hour go."""
        self._decisions.append((now, list(commands), record))
        while self._decisions[0][0] <= now - TARIFF_WINDOW:
            time, left, _ = self._decisions.popleft()
            if self._before is not None and time > self._before[0]:
                self._before = (time, without_superseded([*self._before[1], *left]))
