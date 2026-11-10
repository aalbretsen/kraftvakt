"""Unit tests for the averages of the power sensor."""

import math
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from custom_components.kraftvakt.measurement import (
    CAPACITY_WINDOW,
    PowerAverager,
    WindowAverages,
    power_w,
)

START = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
WINDOW = timedelta(seconds=60)


def at(seconds: float) -> datetime:
    return START + timedelta(seconds=seconds)


def close_windows_until(averager: PowerAverager, end: datetime) -> WindowAverages:
    """Close windows up to and including the one ending at `end`."""
    averages = averager.close_window()
    while averages.end < end:
        averages = averager.close_window()
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
def test_power_w_converts_valid_measurements(
    state: str | None, unit: str | None, expected: float | None
) -> None:
    """W and kW are converted, a missing unit is watt."""
    assert power_w(state, unit) == expected


def test_window_without_measurement_has_no_averages() -> None:
    """Before the first valid measurement the averages are unknown."""
    averager = PowerAverager(WINDOW, START)

    averages = averager.close_window()

    assert averages == WindowAverages(at(0), at(60), None, None, sensor_valid=False)


def test_window_end_follows_the_window_length() -> None:
    """Windows start at the given time and follow each other."""
    averager = PowerAverager(WINDOW, START)
    assert averager.window_end == at(60)

    first = averager.close_window()
    second = averager.close_window()

    assert (first.start, first.end) == (at(0), at(60))
    assert (second.start, second.end) == (at(60), at(120))
    assert averager.window_end == at(180)


def test_new_window_length_applies_from_the_next_window() -> None:
    """A new regulation window keeps the current window and the history."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)

    averager.change_window_length(timedelta(seconds=30))
    first = averager.close_window()
    averager.add_measurement(at(70), 5.0)
    second = averager.close_window()

    assert (first.start, first.end) == (at(0), at(60))
    assert (second.start, second.end) == (at(60), at(90))
    assert second.regulation_average_w == pytest.approx((10 * 2.0 + 20 * 5.0) / 30)
    assert second.capacity_average_w == pytest.approx((3580 * 2.0 + 20 * 5.0) / 3600)


def test_first_measurement_fills_both_windows_backwards() -> None:
    """At startup the first measurement replaces the missing ones."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(20), 4.0)

    averages = averager.close_window()

    assert averages.regulation_average_w == 4.0
    assert averages.capacity_average_w == 4.0
    assert averages.sensor_valid


def test_regulation_average_is_weighted_by_time() -> None:
    """The average is the energy in the window divided by its length."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)
    averager.add_measurement(at(15), 6.0)

    averages = averager.close_window()

    assert averages.regulation_average_w == pytest.approx(5.0)


def test_regulation_windows_do_not_overlap() -> None:
    """Each regulation average covers its own window only."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 8.0)
    averager.add_measurement(at(60), 2.0)
    averager.add_measurement(at(90), 4.0)

    first = averager.close_window()
    second = averager.close_window()

    assert first.regulation_average_w == pytest.approx(8.0)
    assert second.regulation_average_w == pytest.approx(3.0)


def test_capacity_average_slides_over_the_last_hour() -> None:
    """The capacity average covers exactly one hour back in time."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 10.0)
    averager.add_measurement(at(30 * 60), 0.0)

    assert close_windows_until(averager, at(30 * 60)).capacity_average_w == 10.0
    assert close_windows_until(
        averager, at(60 * 60)
    ).capacity_average_w == pytest.approx(5.0)
    assert close_windows_until(
        averager, at(75 * 60)
    ).capacity_average_w == pytest.approx(2.5)
    assert close_windows_until(averager, at(90 * 60)).capacity_average_w == 0.0
    assert close_windows_until(averager, at(5 * 3600)).capacity_average_w == 0.0


def test_capacity_window_does_not_depend_on_the_window_length() -> None:
    """The capacity window is one hour also when 3600 s is not a multiple of
    the regulation window."""
    window = timedelta(seconds=70)
    averager = PowerAverager(window, START)
    averager.add_measurement(at(0), 6.0)
    averager.add_measurement(at(100), 0.0)

    for _ in range(60):
        averages = averager.close_window()
        end_s = (averages.end - START).total_seconds()
        seconds_with_power = min(3600, max(0, 3700 - end_s))
        assert averages.capacity_average_w == pytest.approx(
            6.0 * seconds_with_power / 3600
        )


def changing_power(seconds: int) -> float:
    """Power that changes every 30 seconds, in kW."""
    return 1.0 + (seconds // 30 % 7) * 1.25


def run_with_updates_every(
    interval_s: int, power_at: Callable[[int], float], window_s: int = 60
) -> list[WindowAverages]:
    """Feed the power once per interval through two hours and close all windows."""
    averager = PowerAverager(timedelta(seconds=window_s), START)
    results = []
    for second in range(0, 2 * 3600, interval_s):
        while averager.window_end <= at(second):
            results.append(averager.close_window())
        averager.add_measurement(at(second), power_at(second))
    while averager.window_end <= at(2 * 3600):
        results.append(averager.close_window())
    return results


def expected_average(
    interval_s: int, power_at: Callable[[int], float], start: datetime, end: datetime
) -> float:
    """Average of samples held until the next one, counted second by second.

    Before the first sample the first one applies.
    """
    first = int((start - START).total_seconds())
    last = int((end - START).total_seconds())
    total = sum(
        power_at(max(0, second - second % interval_s)) for second in range(first, last)
    )
    return total / (last - first)


@pytest.mark.parametrize("interval_s", [1, 10, 30, 47])
def test_averages_are_correct_for_any_update_rate(interval_s: int) -> None:
    """The averages are correct whether the sensor updates every second, every
    10 seconds or less often, through the whole capacity window."""
    for averages in run_with_updates_every(interval_s, changing_power):
        assert averages.regulation_average_w == pytest.approx(
            expected_average(interval_s, changing_power, averages.start, averages.end)
        )
        assert averages.capacity_average_w == pytest.approx(
            expected_average(
                interval_s,
                changing_power,
                averages.end - CAPACITY_WINDOW,
                averages.end,
            )
        )


def test_update_rate_does_not_change_the_result() -> None:
    """The same power gives the same averages updated every 1 s or 10 s."""
    every_second = run_with_updates_every(1, changing_power, window_s=45)
    every_ten_seconds = run_with_updates_every(10, changing_power, window_s=45)

    assert len(every_second) == len(every_ten_seconds) == 160
    for one, ten in zip(every_second, every_ten_seconds, strict=True):
        assert one.regulation_average_w == pytest.approx(ten.regulation_average_w)
        assert one.capacity_average_w == pytest.approx(ten.capacity_average_w)


def test_one_invalid_close_uses_the_last_valid_measurement() -> None:
    """One window closing without valid measurement is tolerated."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 3.0)
    averager.add_measurement(at(30), None)

    averages = averager.close_window()

    assert averages.regulation_average_w == 3.0
    assert averages.capacity_average_w == 3.0
    assert not averages.sensor_valid


def test_validity_is_the_state_when_the_window_closes() -> None:
    """A gap inside the window is filled, and only the close counts."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)
    averager.add_measurement(at(10), None)
    averager.add_measurement(at(40), 8.0)

    averages = averager.close_window()

    assert averages.sensor_valid
    assert averages.regulation_average_w == pytest.approx((2.0 * 40 + 8.0 * 20) / 60)


def test_valid_close_between_invalid_ones_keeps_the_history() -> None:
    """Only invalid closes in a row discard the history."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 3.0)
    averager.add_measurement(at(30), None)
    averager.close_window()
    averager.add_measurement(at(90), 3.0)
    averager.close_window()
    averager.add_measurement(at(150), None)

    averages = averager.close_window()

    assert averages.regulation_average_w == 3.0
    assert not averages.sensor_valid


def test_two_invalid_closes_in_a_row_make_the_averages_unknown() -> None:
    """The history is kept, and the last valid measurement fills the gap
    when a valid measurement comes again."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 9.0)
    averager.add_measurement(at(30), None)
    averager.close_window()

    second = averager.close_window()
    third = averager.close_window()
    averager.add_measurement(at(200), 2.0)
    fourth = averager.close_window()

    assert second == WindowAverages(at(60), at(120), None, None, sensor_valid=False)
    assert third == WindowAverages(at(120), at(180), None, None, sensor_valid=False)
    assert fourth.regulation_average_w == pytest.approx((9.0 * 20 + 2.0 * 40) / 60)
    assert fourth.capacity_average_w == pytest.approx(
        (9.0 * 3600 - 9.0 * 40 + 2.0 * 40) / 3600
    )
    assert fourth.sensor_valid


def test_short_value_after_the_gap_does_not_fill_the_hour() -> None:
    """A value that lasts one millisecond after the safe state does not fill
    the whole hour."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 7.0)
    close_windows_until(averager, at(3600))
    averager.add_measurement(at(3610), None)
    close_windows_until(averager, at(3720))
    averager.add_measurement(at(3720.5), 7.85)
    averager.add_measurement(at(3720.501), 3.0)

    averages = close_windows_until(averager, at(3780))

    assert averages.capacity_average_w == pytest.approx(
        (7.0 * 3540.5 + 3.0 * 59.5) / 3600, abs=1e-4
    )


def test_without_first_measurement_windows_stay_unknown() -> None:
    """Windows without any measurement at all are invalid."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(10), None)

    results = [averager.close_window() for _ in range(3)]

    assert all(
        averages.regulation_average_w is None and not averages.sensor_valid
        for averages in results
    )


def test_measurement_after_window_end_does_not_count_in_that_window() -> None:
    """A measurement made after the window end belongs to the next window."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)
    averager.add_measurement(at(61), 8.0)

    first = averager.close_window()
    second = averager.close_window()

    assert first.regulation_average_w == 2.0
    assert second.regulation_average_w == pytest.approx((2.0 * 1 + 8.0 * 59) / 60)


def test_late_measurement_never_changes_a_closed_window() -> None:
    """A measurement older than the latest one counts from the latest time."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)
    averager.close_window()
    averager.add_measurement(at(30), 8.0)

    averages = averager.close_window()

    assert averages.regulation_average_w == 8.0
    assert averages.capacity_average_w == pytest.approx((2.0 * 3540 + 8.0 * 60) / 3600)


def test_latest_measurement_at_the_same_time_wins() -> None:
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(at(0), 2.0)
    averager.add_measurement(at(30), 5.0)
    averager.add_measurement(at(30), 2.0)

    assert averager.close_window().regulation_average_w == 2.0


def test_long_run_keeps_only_the_last_hour() -> None:
    """Old measurements are forgotten, so memory stays bounded over time."""
    averager = PowerAverager(WINDOW, START)
    for second in range(0, 6 * 3600):
        averager.add_measurement(at(second), float(second % 2))
        if averager.window_end <= at(second + 1):
            averages = averager.close_window()

    assert math.isclose(averages.capacity_average_w or 0, 0.5, rel_tol=1e-3)
    assert len(averager._steps) <= 3600 + 2


def test_history_fills_the_hour_before_the_first_measurement() -> None:
    """Invalid history keeps the last valid value; history after the start is left
    out, and the oldest value fills the time before it."""
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(START, 6.0)

    averager.add_history(
        [
            (at(-30 * 60), 2.0),
            (at(-20 * 60), None),
            (at(-10 * 60), 6.0),
            (at(0), 50.0),
            (at(30), 50.0),
        ]
    )
    averages = averager.close_window()

    assert averages.capacity_average_w == pytest.approx((2.0 * 49 + 6.0 * 11) / 60)
    assert averages.regulation_average_w == 6.0


def test_history_without_a_measurement_since_the_start_holds_its_last_value() -> None:
    averager = PowerAverager(WINDOW, START)

    averager.add_history([(at(-60 * 60), 1.0), (at(-15 * 60), 5.0)])
    averages = averager.close_window()

    assert averages.capacity_average_w == pytest.approx((1.0 * 44 + 5.0 * 16) / 60)
    assert averages.regulation_average_w == 5.0
    assert not averages.sensor_valid


def test_empty_history_keeps_the_first_measurement_filling_backwards() -> None:
    averager = PowerAverager(WINDOW, START)
    averager.add_measurement(START, 4.0)

    averager.add_history([(at(-5 * 60), None)])

    assert averager.close_window().capacity_average_w == 4.0
