"""Unit tests for the waiting time."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.waiting import (
    CyclingCounter,
    CyclingSteps,
    WaitingCurve,
    waiting_time,
)

FIVE_MINUTES = timedelta(minutes=5)
DEFAULT_CURVE = WaitingCurve.from_settings(6, 80)
APPLIANCE_CYCLING = CyclingSteps.from_seconds(120, 900)
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


def test_waiting_time_follows_the_curve_until_persistent_cycling() -> None:
    """The first time a slot is turned on again, the curve still applies."""
    for reon_number in (0, 1):
        assert waiting_time(
            8000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, reon_number, APPLIANCE_CYCLING
        ) == pytest.approx(FIVE_MINUTES * 0.8)


def test_waiting_time_on_persistent_cycling_for_appliances() -> None:
    """5, 7, 9, 11, 13 and then 15 minutes, whatever the average."""
    minutes = [
        waiting_time(
            1000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, reon_number, APPLIANCE_CYCLING
        )
        / timedelta(minutes=1)
        for reon_number in range(2, 10)
    ]

    assert minutes == [5, 7, 9, 11, 13, 15, 15, 15]


def test_cycling_steps_are_parameters() -> None:
    """Chargers use other steps and another cap."""
    steps = CyclingSteps(step=timedelta(minutes=5), cap=timedelta(minutes=30))
    minutes = [
        waiting_time(1000, 10_000, FIVE_MINUTES, DEFAULT_CURVE, reon_number, steps)
        / timedelta(minutes=1)
        for reon_number in range(2, 9)
    ]

    assert minutes == [5, 10, 15, 20, 25, 30, 30]


def test_counter_counts_slot_turned_on_again() -> None:
    counter = CyclingCounter()

    assert counter.upcoming_reon_number("a") == 0
    counter.record("a", turned_on=True)
    assert counter.upcoming_reon_number("a") == 1
    counter.record("a", turned_on=False)
    assert counter.upcoming_reon_number("a") == 1
    counter.record("a", turned_on=True)
    counter.record("a", turned_on=False)
    assert counter.upcoming_reon_number("a") == 2


def test_counter_starting_with_turn_off_counts_the_next_turn_on() -> None:
    counter = CyclingCounter()

    counter.record("a", turned_on=False)

    assert counter.upcoming_reon_number("a") == 1


def test_command_for_another_slot_ends_the_count() -> None:
    """The increase is reset as soon as another slot is switched."""
    counter = CyclingCounter()
    for turned_on in (True, False, True, False):
        counter.record("a", turned_on)

    counter.record("b", turned_on=False)

    assert counter.upcoming_reon_number("a") == 0
    assert counter.upcoming_reon_number("b") == 1


def test_reset_forgets_only_the_given_slot() -> None:
    counter = CyclingCounter()
    for turned_on in (True, False, True, False):
        counter.record("a", turned_on)

    counter.reset("b")
    assert counter.upcoming_reon_number("a") == 2

    counter.reset("a")
    assert counter.upcoming_reon_number("a") == 0
