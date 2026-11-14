"""When the decisions are made, counted in closed windows."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from .measurement import WindowAverages


class DecisionClock:
    """Counts the windows closed since the start of the regulation or the last decision.

    A decision is due when the N-th window that started at or after the start
    has closed, where N is the regulation interval. Windows that started before
    the start do not count, also when the engine starts again itself at a
    decision after the safe state or a penalty.
    """

    def __init__(self) -> None:
        self._windows: list[WindowAverages] = []

    def restart(self) -> None:
        self._windows.clear()

    def add(self, window: WindowAverages) -> None:
        self._windows.append(window)

    def take_windows(self) -> list[WindowAverages]:
        """Return the windows closed since the last decision, and count from none again."""
        windows, self._windows = self._windows, []
        return windows

    def is_due(self, started_at: datetime | None, interval: int) -> bool:
        return self._counted(started_at) >= interval

    def next_decision_at(
        self,
        started_at: datetime,
        interval: int,
        window_start: datetime,
        window_end: datetime,
        window_length: timedelta,
    ) -> datetime:
        """Return when the next decision is made, with the window from `window_start` to `window_end` running."""
        windows_left = interval - self._counted(started_at) - (window_start >= started_at)
        return window_end + windows_left * window_length

    def _counted(self, started_at: datetime | None) -> int:
        return sum(1 for window in self._windows if started_at is not None and window.start >= started_at)


def first_decision_from(moment: datetime, next_decision_at: datetime, interval: timedelta) -> datetime:
    """Return the first decision at or after `moment`."""
    if moment <= next_decision_at:
        return next_decision_at
    return next_decision_at + interval * math.ceil((moment - next_decision_at) / interval)
