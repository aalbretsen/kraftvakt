"""Unit tests for the waiting time (REG-013, REG-015, T6)."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.waiting import (
    APPLIANCE_CYCLING,
    CyclingCounter,
    CyclingSteps,
    linear_waiting_time,
    waiting_time,
)

FIVE_MINUTES = timedelta(minutes=5)


@pytest.mark.parametrize(
    ("average_kw", "expected"),
    [
        (0.0, timedelta(0)),
        (5.0, timedelta(minutes=2.5)),
        (7.5, timedelta(minutes=3.75)),
        (10.0, FIVE_MINUTES),
        (14.0, FIVE_MINUTES),
    ],
)
def test_linear_waiting_time(average_kw: float, expected: timedelta) -> None:
    """REG-013: proportional to the average, never longer than at the limit."""
    assert linear_waiting_time(average_kw, 10.0, FIVE_MINUTES) == expected


def test_waiting_time_is_linear_until_persistent_cycling() -> None:
    """The first time a slot is turned on again, the waiting time is linear (T6)."""
    for reon_number in (0, 1):
        assert waiting_time(
            5.0, 10.0, FIVE_MINUTES, reon_number, APPLIANCE_CYCLING
        ) == timedelta(minutes=2.5)


def test_waiting_time_on_persistent_cycling_for_appliances() -> None:
    """REG-015: 5, 7, 9, 11, 13 and then 15 minutes, whatever the average."""
    minutes = [
        waiting_time(1.0, 10.0, FIVE_MINUTES, reon_number, APPLIANCE_CYCLING)
        / timedelta(minutes=1)
        for reon_number in range(2, 10)
    ]

    assert minutes == [5, 7, 9, 11, 13, 15, 15, 15]


def test_cycling_steps_are_parameters() -> None:
    """Chargers use other steps and another cap (LAD-014)."""
    steps = CyclingSteps(step=timedelta(minutes=5), cap=timedelta(minutes=30))
    minutes = [
        waiting_time(1.0, 10.0, FIVE_MINUTES, reon_number, steps) / timedelta(minutes=1)
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
    """REG-015: the increase is reset as soon as another slot is switched."""
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
