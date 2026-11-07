"""Unit tests for overconsumption and the penalty period (STR-001 to STR-009)."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.penalty import (
    PenaltyLimits,
    PenaltyOutcome,
    PenaltyState,
)

LIMITS = PenaltyLimits(
    power_limit_kw=10.0, threshold_kw=1.0, window=timedelta(seconds=60)
)
NO_THRESHOLD = PenaltyLimits(
    power_limit_kw=10.0, threshold_kw=0.0, window=timedelta(seconds=60)
)
KWH_PER_KW_WINDOW = 1 / 60


def overconsuming_state() -> PenaltyState:
    """Return a state whose overconsumption state started at this decision."""
    state = PenaltyState()
    assert state.decide(LIMITS, 10.5, ()) is PenaltyOutcome.NONE
    assert state.overconsuming
    return state


def test_no_overconsumption_at_or_under_the_limit() -> None:
    """STR-004: the state starts only when the capacity average is above the limit."""
    state = PenaltyState()

    assert state.decide(LIMITS, 10.0, (12.0,)) is PenaltyOutcome.NONE
    assert not state.overconsuming
    assert state.overconsumption_kwh == 0


def test_overconsumption_starts_at_zero() -> None:
    """T4: the state starts with 0, and only later averages are counted."""
    state = PenaltyState()

    assert state.decide(LIMITS, 12.0, (15.0, 15.0)) is PenaltyOutcome.NONE

    assert state.overconsuming
    assert state.overconsumption_kwh == 0


def test_overconsumption_is_net_energy_over_the_limit() -> None:
    """STR-005: 12 kW for one window adds 2 kW for one minute, 8 kW takes it back."""
    state = overconsuming_state()

    state.decide(LIMITS, 10.5, (12.0,))
    assert state.overconsumption_kwh == pytest.approx(2 * KWH_PER_KW_WINDOW)

    state.decide(LIMITS, 10.0, (8.0,))
    assert not state.overconsuming
    assert state.overconsumption_kwh == 0


def test_every_average_since_the_previous_decision_counts() -> None:
    """STR-005: with a longer interval, every average in between is counted."""
    state = overconsuming_state()

    state.decide(LIMITS, 10.5, (13.0, 11.0, 9.0))

    assert state.overconsumption_kwh == pytest.approx(3 * KWH_PER_KW_WINDOW)


def test_overconsumption_state_ends_when_paid_back() -> None:
    """STR-004: the state ends when the overconsumption is zero or less."""
    state = overconsuming_state()
    state.decide(LIMITS, 10.5, (11.0,))

    assert state.decide(LIMITS, 10.0, (9.0,)) is PenaltyOutcome.NONE

    assert not state.overconsuming


def test_rounding_errors_count_as_paid_back() -> None:
    """STR-004: 0.01 + 0.46 - 0.47 kW over the limit is paid back."""
    state = overconsuming_state()

    state.decide(LIMITS, 10.0, (10.01, 10.46, 9.53))

    assert not state.overconsuming


def test_overconsumption_state_starts_again_at_once() -> None:
    """STR-004: a new state starts at 0 if the capacity average is still above."""
    state = overconsuming_state()

    state.decide(LIMITS, 10.5, (9.0,))

    assert state.overconsuming
    assert state.overconsumption_kwh == 0


def test_penalty_starts_above_limit_plus_threshold() -> None:
    """STR-001, STR-002: the capacity average must exceed limit plus threshold."""
    state = overconsuming_state()

    assert state.decide(LIMITS, 11.0, (12.0,)) is PenaltyOutcome.NONE
    assert state.decide(LIMITS, 11.01, (12.0,)) is PenaltyOutcome.STARTED
    assert state.active


def test_no_penalty_when_overconsumption_is_paid_back() -> None:
    """STR-009: no penalty when the overconsumption is already zero or less."""
    state = overconsuming_state()

    assert state.decide(LIMITS, 12.0, (12.0, 7.0)) is PenaltyOutcome.NONE
    assert not state.active


def test_zero_threshold_starts_the_penalty_at_the_next_decision() -> None:
    """STR-002, T4: with threshold 0, the penalty comes the decision after D0."""
    state = PenaltyState()

    assert state.decide(NO_THRESHOLD, 10.1, (10.1,)) is PenaltyOutcome.NONE
    assert state.decide(NO_THRESHOLD, 10.1, (10.1,)) is PenaltyOutcome.STARTED


def test_penalty_lasts_until_the_overconsumption_is_paid_back() -> None:
    """STR-005, STR-006: counting goes on during the penalty, until paid back."""
    state = overconsuming_state()
    assert state.decide(LIMITS, 12.0, (14.0,)) is PenaltyOutcome.STARTED

    assert state.decide(LIMITS, 12.0, (13.0,)) is PenaltyOutcome.ONGOING
    assert state.overconsumption_kwh == pytest.approx(7 * KWH_PER_KW_WINDOW)
    assert state.decide(LIMITS, 12.0, (5.0,)) is PenaltyOutcome.ONGOING
    assert state.decide(LIMITS, 12.0, (8.0,)) is PenaltyOutcome.ENDED

    assert state == PenaltyState()


def test_penalty_does_not_end_when_the_capacity_average_falls() -> None:
    """STR-006: only paying back the overconsumption ends the penalty."""
    state = overconsuming_state()
    state.decide(LIMITS, 12.0, (14.0,))

    assert state.decide(LIMITS, 2.0, (11.0,)) is PenaltyOutcome.ONGOING


def test_recovery_starts_at_the_first_average_under_the_limit() -> None:
    """STR-007, T5: recovery starts under the limit and goes on net."""
    state = overconsuming_state()
    state.decide(LIMITS, 12.0, (16.0,))
    assert not state.recovery_started

    state.decide(LIMITS, 12.0, (12.0, 10.0))
    assert not state.recovery_started

    state.decide(LIMITS, 12.0, (9.0,))
    assert state.recovery_started
    assert state.overconsumption_kwh == pytest.approx(7 * KWH_PER_KW_WINDOW)

    state.decide(LIMITS, 12.0, (12.0,))
    assert state.recovery_started
    assert state.overconsumption_kwh == pytest.approx(9 * KWH_PER_KW_WINDOW)


def test_recovery_is_not_tracked_outside_a_penalty() -> None:
    """STR-007: recovery only concerns a penalty period."""
    state = overconsuming_state()

    state.decide(LIMITS, 10.5, (12.0, 9.0))

    assert not state.recovery_started


def test_energy_follows_the_regulation_window() -> None:
    """STR-005: each average covers one regulation window (MAL-002)."""
    limits = PenaltyLimits(10.0, 1.0, timedelta(seconds=600))
    state = PenaltyState()
    state.decide(limits, 10.5, ())

    state.decide(limits, 10.5, (16.0,))

    assert state.overconsumption_kwh == pytest.approx(1.0)
