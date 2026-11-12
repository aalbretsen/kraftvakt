"""Unit tests for the waiting time."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.waiting import (
    RepeatedTurnOnCounter,
    RepeatedTurnOnGrowth,
    WaitingCurve,
    waiting_time,
)

FIVE_MINUTES = timedelta(minutes=5)
DEFAULT_CURVE = WaitingCurve.from_settings(6, 80)
APPLIANCE_GROWTH = RepeatedTurnOnGrowth(
    increment=timedelta(minutes=2), cap=timedelta(minutes=15)
)
UTILIZATIONS = (60, 70, 75, 80, 85, 90, 93, 96, 99, 100)


@pytest.mark.parametrize(
    ("steepness", "pivot", "shape", "shares"),
    [
        (
            6,
            80,
            0.012386,
            (0.52, 25.16, 56.47, 80, 91.6, 96.67, 98.23, 99.21, 99.84, 100),
        ),
        (
            3,
            70,
            0.017391,
            (32.05, 80, 89.31, 94.16, 96.83, 98.4, 99.03, 99.52, 99.89, 100),
        ),
        (
            1.5,
            95,
            133.166681,
            (9.01, 25.44, 35.53, 46.66, 58.75, 71.71, 79.87, 88.32, 97.04, 100),
        ),
        (9, 50, 0, (100,) * 10),
    ],
)
def test_waiting_curve_follows_the_specification(
    steepness: float, pivot: int, shape: float, shares: tuple[float, ...]
) -> None:
    """The test values of the specification, the pivot 95 capped silently."""
    curve = WaitingCurve.from_settings(steepness, pivot)

    assert curve.shape == pytest.approx(shape, abs=1e-6)
    assert [round(100 * curve.share(u / 100), 2) for u in UTILIZATIONS] == list(shares)


@pytest.mark.parametrize("utilization", [0, 0.25, 0.5])
def test_no_waiting_up_to_half_the_limit(utilization: float) -> None:
    for curve in (DEFAULT_CURVE, WaitingCurve.from_settings(9, 50)):
        assert curve.share(utilization) == 0


def test_whole_waiting_time_above_the_limit() -> None:
    assert DEFAULT_CURVE.share(1.4) == pytest.approx(1)


def test_waiting_time_follows_the_curve_until_repeated_turn_on() -> None:
    """The first time a step is turned on again, the curve still applies."""
    for repeat in (0, 1):
        assert waiting_time(
            8000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, repeat, APPLIANCE_GROWTH
        ) == pytest.approx(FIVE_MINUTES * 0.8)


def test_waiting_time_on_repeated_turn_on_for_appliances() -> None:
    """5, 7, 9, 11, 13 and then 15 minutes, whatever the average."""
    minutes = [
        waiting_time(
            1000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, repeat, APPLIANCE_GROWTH
        )
        / timedelta(minutes=1)
        for repeat in range(2, 10)
    ]

    assert minutes == [5, 7, 9, 11, 13, 15, 15, 15]


def test_growth_are_parameters() -> None:
    """Chargers use another increment and another cap."""
    growth = RepeatedTurnOnGrowth(
        increment=timedelta(minutes=5), cap=timedelta(minutes=30)
    )
    minutes = [
        waiting_time(1000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, repeat, growth)
        / timedelta(minutes=1)
        for repeat in range(2, 9)
    ]

    assert minutes == [5, 10, 15, 20, 25, 30, 30]


@pytest.mark.parametrize(
    ("wait_at_limit_s", "factor", "increments", "increment_s", "cap_s"),
    [(300, 0.5, 4, 150, 900), (300, 1.0, 4, 300, 1500), (0, 0.25, 9, 0, 0)],
)
def test_growth_from_the_waiting_time_at_the_limit(
    wait_at_limit_s: int, factor: float, increments: int, increment_s: int, cap_s: int
) -> None:
    """The increment is a share of the waiting time at the limit.

    The cap is the given number of increments above the waiting time at the limit.
    """
    growth = RepeatedTurnOnGrowth.from_waiting_at_limit(
        wait_at_limit_s, factor, increments
    )

    assert growth == RepeatedTurnOnGrowth(
        increment=timedelta(seconds=increment_s), cap=timedelta(seconds=cap_s)
    )


def test_counter_counts_slot_turned_on_again() -> None:
    counter = RepeatedTurnOnCounter()

    assert counter.upcoming_repeat("a") == 0
    counter.record("a", turned_on=True)
    assert counter.upcoming_repeat("a") == 1
    counter.record("a", turned_on=False)
    assert counter.upcoming_repeat("a") == 1
    counter.record("a", turned_on=True)
    counter.record("a", turned_on=False)
    assert counter.upcoming_repeat("a") == 2


def test_counter_starting_with_turn_off_counts_the_next_turn_on() -> None:
    counter = RepeatedTurnOnCounter()

    counter.record("a", turned_on=False)

    assert counter.upcoming_repeat("a") == 1


def test_command_for_another_slot_ends_the_count() -> None:
    """The increase is reset as soon as another step is switched."""
    counter = RepeatedTurnOnCounter()
    for turned_on in (True, False, True, False):
        counter.record("a", turned_on)

    counter.record("b", turned_on=False)

    assert counter.upcoming_repeat("a") == 0
    assert counter.upcoming_repeat("b") == 1


def test_reset_forgets_only_the_given_slot() -> None:
    counter = RepeatedTurnOnCounter()
    for turned_on in (True, False, True, False):
        counter.record("a", turned_on)

    counter.reset("b")
    assert counter.upcoming_repeat("a") == 2

    counter.reset("a")
    assert counter.upcoming_repeat("a") == 0
