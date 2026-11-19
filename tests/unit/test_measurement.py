"""Unit tests for the averages of the power sensor."""

import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.measurement import (
    TARIFF_WINDOW,
    MissedWindows,
    PowerAverager,
    WindowAverages,
    power_w,
    update_interval_s,
)

START = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
WINDOW = timedelta(seconds=60)
UPDATES = 6


def at(seconds: float) -> datetime:
    return START + timedelta(seconds=seconds)


def close_next(averager: PowerAverager, length: timedelta = WINDOW) -> WindowAverages:
    """Close the window when it has lasted `length`."""
    return averager.close_window(averager.window_start + length)


def close_windows_until(averager: PowerAverager, end: datetime) -> WindowAverages:
    """Close windows of one minute up to and including the one ending at `end`."""
    averages = close_next(averager)
    while averages.end < end:
        averages = close_next(averager)
    assert averages.end == end
    return averages


@pytest.mark.parametrize(
    ("state", "unit", "expected"),
    [
        ("2500", "W", 2500),
        ("2.5", "kW", 2500),
        ("1500", None, 1500),
        ("1500", "", 1500),
        ("-300", "W", 0.0),
        ("0", "kW", 0.0),
        ("2.5", "MW", None),
        ("2500", "BTU/h", None),
        ("unavailable", "W", None),
        ("unknown", "W", None),
        ("", "W", None),
        ("nan", "W", None),
        ("inf", "kW", None),
        (None, "W", None),
    ],
)
def test_power_w_converts_valid_measurements(state: str | None, unit: str | None, expected: float | None) -> None:
    """W and kW are converted, a missing unit is watt."""
    assert power_w(state, unit) == expected


def test_window_without_measurement_has_no_averages() -> None:
    """Before the first valid measurement the averages are unknown."""
    averager = PowerAverager(UPDATES, START)

    averages = averager.close_window(at(60))

    assert averages == WindowAverages(at(0), at(60), None, None, sensor_valid=False)


def test_window_is_complete_at_its_number_of_updates() -> None:
    """Invalid updates count, the state when the sensor is first followed does not, and the count starts again in the next window."""
    averager = PowerAverager(3, START)
    averager.add_measurement(at(0), 2.0, update=False)
    averager.add_measurement(at(10), 2.0)
    averager.add_measurement(at(20), None)
    assert not averager.window_complete

    averager.add_measurement(at(30), 2.0)
    assert averager.window_complete
    averager.close_window(at(30))
    assert not averager.window_complete
    assert averager.diagnostics()["updates"] == 0


def test_window_with_its_updates_at_its_start_is_not_complete() -> None:
    """A window closed at its start would last no time."""
    averager = PowerAverager(1, START)
    averager.add_measurement(at(0), 2.0)

    assert not averager.window_complete


def test_new_number_of_updates_applies_from_the_next_window() -> None:
    averager = PowerAverager(3, START)
    averager.change_updates_per_window(1)
    averager.add_measurement(at(10), 2.0)
    assert not averager.window_complete

    averager.close_window(at(10))
    averager.add_measurement(at(20), 2.0)
    assert averager.window_complete


def test_windows_follow_each_other() -> None:
    averager = PowerAverager(UPDATES, START)

    first = averager.close_window(at(60))
    second = averager.close_window(at(130))

    assert (first.start, first.end) == (at(0), at(60))
    assert (second.start, second.end) == (at(60), at(130))
    assert averager.window_start == at(130)


def test_skipped_windows_start_the_next_window() -> None:
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), None)

    assert averager.skip_windows(at(120)) == MissedWindows(at(0), at(120))
    assert averager.window_start == at(120)
    assert averager.diagnostics()["last_missed_windows"] == MissedWindows(at(0), at(120))
    assert averager.diagnostics()["updates"] == 0


def test_skipped_time_counts_with_the_last_valid_measurement() -> None:
    """Nothing is measured while the event loop is paused, as while Home Assistant is down. A late report counts from the window start."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 2.0)
    averager.add_measurement(at(30), None)

    averager.skip_windows(at(1800))
    averager.add_measurement(at(1790), 8.0)
    averager.add_measurement(at(1810), 8.0)
    averages = averager.close_window(at(1860))

    assert averages.regulation_average_w == 8.0
    assert averages.tariff_average_w == pytest.approx((2.0 * 3540 + 8.0 * 60) / 3600)


def test_first_measurement_fills_both_windows_backwards() -> None:
    """At startup the first measurement replaces the missing ones."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(20), 4.0)

    averages = averager.close_window(at(60))

    assert averages.regulation_average_w == 4.0
    assert averages.tariff_average_w == 4.0
    assert averages.sensor_valid


def test_each_measurement_covers_the_time_before_it() -> None:
    """The measurement that closes the window counts in it, and the average is the energy in the window divided by its length."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(15), 2.0)
    averager.add_measurement(at(60), 6.0)

    averages = averager.close_window(at(60))

    assert averages.regulation_average_w == pytest.approx(5.0)


def test_latest_measurement_covers_the_time_after_it_until_the_close() -> None:
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(30), 2.0)
    averager.add_measurement(at(40), 8.0)

    assert averager.close_window(at(60)).regulation_average_w == pytest.approx((2.0 * 30 + 8.0 * 30) / 60)


def test_regulation_windows_do_not_overlap() -> None:
    """Each regulation average covers its own window only, and a measurement after a close covers the time since it."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(60), 8.0)
    first = averager.close_window(at(60))
    averager.add_measurement(at(90), 2.0)
    averager.add_measurement(at(120), 4.0)
    second = averager.close_window(at(120))

    assert first.regulation_average_w == pytest.approx(8.0)
    assert second.regulation_average_w == pytest.approx(3.0)


def test_tariff_average_slides_over_the_last_hour() -> None:
    """The tariff average covers exactly one hour back in time."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(0), 10.0)

    assert close_windows_until(averager, at(30 * 60)).tariff_average_w == 10.0
    averager.add_measurement(at(31 * 60), 0.0)
    assert close_windows_until(averager, at(60 * 60)).tariff_average_w == pytest.approx(5.0)
    assert close_windows_until(averager, at(75 * 60)).tariff_average_w == pytest.approx(2.5)
    assert close_windows_until(averager, at(90 * 60)).tariff_average_w == 0.0
    assert close_windows_until(averager, at(5 * 3600)).tariff_average_w == 0.0


def test_tariff_window_does_not_depend_on_the_window_length() -> None:
    """The tariff window is one hour also when 3600 s is not a multiple of the regulation window."""
    window = timedelta(seconds=70)
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(0), 6.0)
    close_next(averager, window)
    averager.add_measurement(at(100), 0.0)

    for _ in range(60):
        averages = close_next(averager, window)
        end_s = (averages.end - START).total_seconds()
        seconds_with_power = min(3600, max(0, 3670 - end_s))
        assert averages.tariff_average_w == pytest.approx(6.0 * seconds_with_power / 3600)


def changing_power(seconds: int) -> float:
    """Power in kW that changes every 30 seconds, the same from just after a whole half minute up to the next."""
    return 1.0 + (math.ceil(seconds / 30) % 7) * 1.25


def run_with_updates_every(interval_s: int, power_at: Callable[[int], float], updates: int) -> list[WindowAverages]:
    """Feed the power once per interval through two hours, closing a window at every `updates`-th update."""
    averager = PowerAverager(updates, START)
    results = []
    for second in range(interval_s, 2 * 3600 + 1, interval_s):
        averager.add_measurement(at(second), power_at(second))
        if averager.window_complete:
            results.append(averager.close_window(at(second)))
    return results


def expected_average(interval_s: int, power_at: Callable[[int], float], start: datetime, end: datetime) -> float:
    """Average of samples that each cover the time since the sample before, counted second by second.

    Before the first sample the first one applies.
    """
    first = int((start - START).total_seconds())
    last = int((end - START).total_seconds())
    total = sum(power_at(interval_s * (max(0, second) // interval_s + 1)) for second in range(first, last))
    return total / (last - first)


@pytest.mark.parametrize("interval_s", [1, 10, 30, 47])
def test_averages_are_correct_for_any_update_rate(interval_s: int) -> None:
    """The averages are correct whether the sensor updates every second, every 10 seconds or less often, through the whole tariff window."""
    for averages in run_with_updates_every(interval_s, changing_power, max(1, 60 // interval_s)):
        assert averages.regulation_average_w == pytest.approx(expected_average(interval_s, changing_power, averages.start, averages.end))
        assert averages.tariff_average_w == pytest.approx(expected_average(interval_s, changing_power, averages.end - TARIFF_WINDOW, averages.end))


def test_update_rate_does_not_change_the_result() -> None:
    """The same power gives the same averages in windows of a minute, updated every 1 s or 10 s."""
    every_second = run_with_updates_every(1, changing_power, 60)
    every_ten_seconds = run_with_updates_every(10, changing_power, 6)

    assert len(every_second) == len(every_ten_seconds) == 120
    for one, ten in zip(every_second, every_ten_seconds, strict=True):
        assert one.regulation_average_w == pytest.approx(ten.regulation_average_w)
        assert one.tariff_average_w == pytest.approx(ten.tariff_average_w)


def test_one_invalid_close_uses_the_last_valid_measurement() -> None:
    """One window closing without valid measurement is tolerated."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 3.0)
    averager.add_measurement(at(30), None)

    averages = averager.close_window(at(60))

    assert averages.regulation_average_w == 3.0
    assert averages.tariff_average_w == 3.0
    assert not averages.sensor_valid


def test_validity_is_the_state_when_the_window_closes() -> None:
    """A gap inside the window keeps the last valid measurement, and only the close counts."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 2.0)
    averager.add_measurement(at(20), None)
    averager.add_measurement(at(60), 8.0)

    averages = averager.close_window(at(60))

    assert averages.sensor_valid
    assert averages.regulation_average_w == pytest.approx((2.0 * 20 + 8.0 * 40) / 60)


def test_valid_close_between_invalid_ones_keeps_the_history() -> None:
    """Only invalid closes in a row discard the history."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 3.0)
    averager.add_measurement(at(30), None)
    averager.close_window(at(60))
    averager.add_measurement(at(90), 3.0)
    averager.close_window(at(120))
    averager.add_measurement(at(150), None)

    averages = averager.close_window(at(180))

    assert averages.regulation_average_w == 3.0
    assert not averages.sensor_valid


def test_two_invalid_closes_in_a_row_make_the_averages_unknown() -> None:
    """The history is kept, and the last valid measurement fills the gap when a valid measurement comes again."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 9.0)
    averager.add_measurement(at(30), None)
    averager.close_window(at(60))

    second = averager.close_window(at(120))
    third = averager.close_window(at(180))
    averager.add_measurement(at(200), 2.0)
    fourth = averager.close_window(at(240))

    assert second == WindowAverages(at(60), at(120), None, None, sensor_valid=False)
    assert third == WindowAverages(at(120), at(180), None, None, sensor_valid=False)
    assert fourth.regulation_average_w == pytest.approx(2.0)
    assert fourth.tariff_average_w == pytest.approx((9.0 * 3540 + 2.0 * 60) / 3600)
    assert fourth.sensor_valid


def test_short_value_after_the_gap_does_not_fill_the_hour() -> None:
    """A value that lasts one millisecond after the safe state does not fill the whole hour."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(0), 7.0)
    close_windows_until(averager, at(3600))
    averager.add_measurement(at(3610), None)
    close_windows_until(averager, at(3720))
    averager.add_measurement(at(3720.5), 7.85)
    averager.add_measurement(at(3720.501), 3.0)

    averages = close_windows_until(averager, at(3780))

    assert averages.tariff_average_w == pytest.approx((7.0 * 3540 + 7.85 * 0.5 + 3.0 * 59.5) / 3600)


def test_without_first_measurement_windows_stay_unknown() -> None:
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), None)

    results = [close_next(averager) for _ in range(3)]

    assert all(averages.regulation_average_w is None and not averages.sensor_valid for averages in results)


def test_late_measurement_never_changes_a_closed_window() -> None:
    """A measurement older than the latest one counts from the latest time."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 2.0)
    averager.close_window(at(60))
    averager.add_measurement(at(30), 8.0)

    averages = averager.close_window(at(120))

    assert averages.regulation_average_w == 8.0
    assert averages.tariff_average_w == pytest.approx((2.0 * 3540 + 8.0 * 60) / 3600)


def test_latest_measurement_at_the_same_time_wins() -> None:
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(at(10), 2.0)
    averager.add_measurement(at(30), 5.0)
    averager.add_measurement(at(30), 2.0)

    assert averager.close_window(at(60)).regulation_average_w == 2.0


def test_long_run_keeps_only_the_last_hour() -> None:
    """Old measurements are forgotten, so memory stays bounded over time."""
    averager = PowerAverager(60, START)
    for second in range(1, 6 * 3600 + 1):
        averager.add_measurement(at(second), float(second % 2))
        if averager.window_complete:
            averages = averager.close_window(at(second))

    assert math.isclose(averages.tariff_average_w or 0, 0.5, rel_tol=1e-3)
    assert len(averager._steps) <= 3600 + 2


def test_history_fills_the_hour_before_the_first_measurement() -> None:
    """Each value in the history holds until the next, an invalid one keeps the last valid value,
    history after the start is left out, and the oldest value fills the time before it."""
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(START, 6.0, update=False)

    averager.add_history(
        [
            (at(-30 * 60), 2.0),
            (at(-20 * 60), None),
            (at(-10 * 60), 6.0),
            (at(0), 50.0),
            (at(30), 50.0),
        ]
    )
    averages = averager.close_window(at(60))

    assert averages.tariff_average_w == pytest.approx((2.0 * 49 + 6.0 * 11) / 60)
    assert averages.regulation_average_w == 6.0


def test_history_without_a_measurement_since_the_start_holds_its_last_value() -> None:
    averager = PowerAverager(UPDATES, START)

    averager.add_history([(at(-60 * 60), 1.0), (at(-15 * 60), 5.0)])
    averages = averager.close_window(at(60))

    assert averages.tariff_average_w == pytest.approx((1.0 * 44 + 5.0 * 16) / 60)
    assert averages.regulation_average_w == 5.0
    assert not averages.sensor_valid


def test_empty_history_keeps_the_first_measurement_filling_backwards() -> None:
    averager = PowerAverager(UPDATES, START)
    averager.add_measurement(START, 4.0, update=False)

    averager.add_history([(at(-5 * 60), None)])

    assert averager.close_window(at(60)).tariff_average_w == 4.0


def reports(*intervals_s: float) -> list[datetime]:
    return [at(sum(intervals_s[:count])) for count in range(len(intervals_s) + 1)]


@pytest.mark.parametrize(
    ("times", "fewest", "expected"),
    [
        (reports(10, 10.1, 9.9, 10), 2, 10.0),
        (reports(2.04, 2.0, 2.06), 2, 2.0),
        (reports(10, 20, 10, 30, 10), 2, 10.0),
        (reports(10), 2, None),
        (reports(10, 10, 10), 10, None),
        (reports(10, 25, 50, 90), 2, None),
        (reports(0, 0), 2, None),
    ],
)
def test_update_interval_is_the_median_of_regular_intervals(times: list[datetime], fewest: int, expected: float | None) -> None:
    """Repeated values left out of the history make some intervals longer, which the median is not moved by."""
    assert update_interval_s(times, fewest_intervals=fewest) == expected
