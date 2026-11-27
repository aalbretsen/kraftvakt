"""How the power sensor reports, from the times of its updates, pure Python without Home Assistant."""

from __future__ import annotations

import bisect
import math
import statistics
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise
from typing import Any, Final

ANALYSED_PERIOD: Final = timedelta(hours=1)
FEWEST_INTERVALS: Final = 3


@dataclass(frozen=True, slots=True)
class ReportAnalysis:
    """The updates of the power sensor over a period.

    `lost_updates` counts the updates missing between steady ones: an interval
    of about two update intervals or more has lost one less than its whole
    update intervals. It means something only when the updates are steady.
    """

    updates: int
    update_interval: timedelta | None
    steady: bool
    shortest: timedelta | None
    longest_silence: timedelta | None
    lost_updates: int

    @property
    def known(self) -> bool:
        """Return whether there are enough updates to tell how the sensor reports: an update interval, or uneven updates without one."""
        return self.update_interval is not None or self.updates > FEWEST_INTERVALS


def analyse_reports(times: Sequence[datetime]) -> ReportAnalysis:
    """Return how a sensor reports, from the times of its updates, oldest first."""
    intervals = sorted(seconds for earlier, later in pairwise(times) if (seconds := (later - earlier).total_seconds()) > 0)
    interval_s = _update_interval_s(intervals)
    if interval_s is None:
        return ReportAnalysis(len(times), None, False, _duration(intervals, 0), _duration(intervals, -1), 0)
    regular = sum(1 for interval in intervals if abs(interval - interval_s) <= interval_s / 4)
    lost = sum(round(interval / interval_s) - 1 for interval in intervals if interval >= 1.5 * interval_s)
    return ReportAnalysis(
        updates=len(times),
        update_interval=timedelta(seconds=interval_s),
        steady=regular >= 0.9 * len(intervals),
        shortest=_duration(intervals, 0),
        longest_silence=_duration(intervals, -1),
        lost_updates=lost,
    )


def _update_interval_s(intervals: list[float]) -> float | None:
    """Return the median of the intervals within a quarter of the shortest interval that has at least three of them, to a tenth of a second.

    Why the shortest: a reader that reports only when the power changes
    reports at whole multiples of the meter's interval, and an extra report,
    as a Kamstrup meter's hourly list, comes too seldom to count.
    """
    for candidate in intervals:
        near = intervals[bisect.bisect_left(intervals, candidate * 0.75) : bisect.bisect_right(intervals, candidate * 1.25)]
        if len(near) >= FEWEST_INTERVALS:
            return round(statistics.median(near), 1)
    return None


def _duration(sorted_intervals: list[float], index: int) -> timedelta | None:
    return timedelta(seconds=sorted_intervals[index]) if sorted_intervals else None


def suggested_timeout_s(analysis: ReportAnalysis, default_s: int, longest_s: int) -> int:
    """Return a power sensor timeout of five longest silences, in whole minutes, but at least the default and at most the longest timeout."""
    if analysis.longest_silence is None:
        return default_s
    minutes = math.ceil(5 * analysis.longest_silence.total_seconds() / 60)
    return min(max(default_s, minutes * 60), longest_s)


class ReportLog:
    """The times of the updates of the power sensor over the last hour."""

    def __init__(self) -> None:
        self._times: deque[datetime] = deque()

    def diagnostics(self) -> dict[str, Any]:
        return {"updates": len(self._times), "first_update": self._times[0] if self._times else None}

    def add(self, when: datetime) -> None:
        """Record an update at `when`, which is never older than the one before."""
        self._times.append(when)
        self._forget_before(when - ANALYSED_PERIOD)

    def clear(self) -> None:
        self._times.clear()

    def analysis(self, now: datetime) -> ReportAnalysis:
        self._forget_before(now - ANALYSED_PERIOD)
        return analyse_reports(self._times)

    def _forget_before(self, horizon: datetime) -> None:
        while self._times and self._times[0] < horizon:
            self._times.popleft()
