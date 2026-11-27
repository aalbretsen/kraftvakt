"""Unit tests for how the power sensor reports."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.report_analysis import ReportAnalysis, ReportLog, analyse_reports, suggested_timeout_s

START = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)


def at(seconds: float) -> datetime:
    return START + timedelta(seconds=seconds)


def reports(*intervals_s: float) -> list[datetime]:
    return [at(sum(intervals_s[:count])) for count in range(len(intervals_s) + 1)]


def test_steady_updates() -> None:
    analysis = analyse_reports(reports(10, 10.1, 9.9, 10, 10))

    assert analysis == ReportAnalysis(6, timedelta(seconds=10), True, timedelta(seconds=9.9), timedelta(seconds=10.1), 0)


def test_updates_only_when_the_power_changes_vary_on_the_meters_interval() -> None:
    """The update interval is the shortest interval that repeats, and the others are whole multiples of it."""
    analysis = analyse_reports(reports(2.5, 2.5, 47.5, 2.5, 12.5, 5, 30))

    assert analysis.update_interval == timedelta(seconds=2.5)
    assert not analysis.steady
    assert analysis.longest_silence == timedelta(seconds=47.5)


def test_an_extra_report_does_not_count_as_the_update_interval() -> None:
    """A Kamstrup meter sends its hourly list a few seconds after a report."""
    analysis = analyse_reports(reports(10, 10, 3.4, 6.6, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10))

    assert analysis.update_interval == timedelta(seconds=10)
    assert analysis.steady
    assert analysis.shortest == timedelta(seconds=3.4)


def test_lost_updates_are_counted_from_the_gaps_of_whole_update_intervals() -> None:
    analysis = analyse_reports(reports(*[10] * 30, 20, 30, 14))

    assert analysis.steady
    assert analysis.lost_updates == 1 + 2


@pytest.mark.parametrize("times", [[], [at(0)], reports(10, 10), reports(2, 9, 30, 70)])
def test_the_update_interval_is_unknown_without_three_similar_intervals(times: list[datetime]) -> None:
    analysis = analyse_reports(times)

    assert analysis.update_interval is None
    assert not analysis.steady
    assert analysis.updates == len(times)
    assert analysis.lost_updates == 0


def test_without_intervals_nothing_is_known_of_the_silence() -> None:
    assert analyse_reports([at(0)]).longest_silence is None


@pytest.mark.parametrize(
    ("longest_silence_s", "expected"),
    [(None, 300), (10, 300), (61, 360), (125, 660), (800, 3600)],
)
def test_suggested_timeout_is_five_longest_silences_in_whole_minutes(longest_silence_s: float | None, expected: int) -> None:
    silence = None if longest_silence_s is None else timedelta(seconds=longest_silence_s)
    analysis = ReportAnalysis(10, timedelta(seconds=2.5), False, timedelta(seconds=2.5), silence, 0)

    assert suggested_timeout_s(analysis, 300, 3600) == expected


def test_the_report_log_keeps_the_last_hour() -> None:
    log = ReportLog()
    for seconds in range(0, 3700, 10):
        log.add(at(seconds))

    analysis = log.analysis(at(3690))

    assert analysis.updates == 361
    assert analysis.update_interval == timedelta(seconds=10)
    assert log.diagnostics() == {"updates": 361, "first_update": at(90)}
    assert log.analysis(at(7300)).updates == 0


def test_a_cleared_report_log_has_no_updates() -> None:
    log = ReportLog()
    log.add(at(0))
    log.clear()

    assert log.diagnostics() == {"updates": 0, "first_update": None}


@pytest.mark.parametrize(
    ("times", "known"),
    [(reports(10, 10), False), (reports(10, 10, 10), True), (reports(2, 9), False), (reports(2, 9, 30), True)],
)
def test_it_is_known_how_a_sensor_reports_with_an_update_interval_or_more_updates_than_one_needs(times: list[datetime], known: bool) -> None:
    """More updates than an update interval needs, without one, are uneven."""
    assert analyse_reports(times).known is known
