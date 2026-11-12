"""Unit tests for overconsumption and the penalty period."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt.regulation.penalty import (
    PenaltyLimits,
    PenaltyOutcome,
    PenaltyState,
)

LIMITS = PenaltyLimits(
    power_limit_w=10_000, threshold_w=1000, window=timedelta(seconds=60)
)
NO_THRESHOLD = PenaltyLimits(
    power_limit_w=10_000, threshold_w=0, window=timedelta(seconds=60)
)
WH_PER_W_WINDOW = 1 / 60


def overconsuming_state() -> PenaltyState:
    """Return a state whose overconsumption state started at this decision."""
    state = PenaltyState()
    assert state.decide(LIMITS, 10500, ()) is PenaltyOutcome.NONE
    assert state.overconsuming
    return state


def test_no_overconsumption_at_or_under_the_limit() -> None:
    """The state starts only when the tariff average is above the limit."""
    state = PenaltyState()

    assert state.decide(LIMITS, 10000, (12000,)) is PenaltyOutcome.NONE
    assert not state.overconsuming
    assert state.overconsumption_wh == 0


def test_overconsumption_starts_at_zero() -> None:
    """The state starts with 0, and only later averages are counted."""
    state = PenaltyState()

    assert state.decide(LIMITS, 12000, (15000, 15000)) is PenaltyOutcome.NONE

    assert state.overconsuming
    assert state.overconsumption_wh == 0


def test_overconsumption_is_net_energy_over_the_limit() -> None:
    """12 kW for one window adds 2 kW for one minute, 8 kW takes it back."""
    state = overconsuming_state()

    state.decide(LIMITS, 10500, (12000,))
    assert state.overconsumption_wh == pytest.approx(2000 * WH_PER_W_WINDOW)

    state.decide(LIMITS, 10000, (8000,))
    assert not state.overconsuming
    assert state.overconsumption_wh == 0


def test_every_average_since_the_previous_decision_counts() -> None:
    """With a longer interval, every average in between is counted."""
    state = overconsuming_state()

    state.decide(LIMITS, 10500, (13000, 11000, 9000))

    assert state.overconsumption_wh == pytest.approx(3000 * WH_PER_W_WINDOW)


def test_overconsumption_state_ends_when_paid_back() -> None:
    """The state ends when the overconsumption is zero or less."""
    state = overconsuming_state()
    state.decide(LIMITS, 10500, (11000,))

    assert state.decide(LIMITS, 10000, (9000,)) is PenaltyOutcome.NONE

    assert not state.overconsuming


def test_rounding_errors_count_as_paid_back() -> None:
    """0.01 + 0.46 - 0.47 kW over the limit is paid back."""
    state = overconsuming_state()

    state.decide(LIMITS, 10000, (10010, 10460, 9530))

    assert not state.overconsuming


def test_overconsumption_state_starts_again_at_once() -> None:
    """A new state starts at 0 if the tariff average is still above."""
    state = overconsuming_state()

    state.decide(LIMITS, 10500, (9000,))

    assert state.overconsuming
    assert state.overconsumption_wh == 0


def test_penalty_starts_above_limit_plus_threshold() -> None:
    """The tariff average must exceed limit plus threshold."""
    state = overconsuming_state()

    assert state.decide(LIMITS, 11000, (12000,)) is PenaltyOutcome.NONE
    assert state.decide(LIMITS, 11010, (12000,)) is PenaltyOutcome.STARTED
    assert state.active


def test_no_penalty_when_overconsumption_is_paid_back() -> None:
    """No penalty when the overconsumption is already zero or less."""
    state = overconsuming_state()

    assert state.decide(LIMITS, 12000, (12000, 7000)) is PenaltyOutcome.NONE
    assert not state.active


def test_zero_threshold_starts_the_penalty_at_the_next_decision() -> None:
    """With threshold 0, the penalty comes the decision after D0."""
    state = PenaltyState()

    assert state.decide(NO_THRESHOLD, 10100, (10100,)) is PenaltyOutcome.NONE
    assert state.decide(NO_THRESHOLD, 10100, (10100,)) is PenaltyOutcome.STARTED


def test_penalty_lasts_until_the_overconsumption_is_paid_back() -> None:
    """Counting goes on during the penalty, until paid back."""
    state = overconsuming_state()
    assert state.decide(LIMITS, 12000, (14000,)) is PenaltyOutcome.STARTED

    assert state.decide(LIMITS, 12000, (13000,)) is PenaltyOutcome.ONGOING
    assert state.overconsumption_wh == pytest.approx(7000 * WH_PER_W_WINDOW)
    assert state.decide(LIMITS, 12000, (5000,)) is PenaltyOutcome.ONGOING
    assert state.decide(LIMITS, 12000, (8000,)) is PenaltyOutcome.ENDED

    assert state == PenaltyState()


def test_penalty_does_not_end_when_the_tariff_average_falls() -> None:
    """Only paying back the overconsumption ends the penalty."""
    state = overconsuming_state()
    state.decide(LIMITS, 12000, (14000,))

    assert state.decide(LIMITS, 2000, (11000,)) is PenaltyOutcome.ONGOING


def test_recovery_starts_at_the_first_average_under_the_limit() -> None:
    """Recovery starts under the limit and goes on net."""
    state = overconsuming_state()
    state.decide(LIMITS, 12000, (16000,))
    assert not state.recovery_started

    state.decide(LIMITS, 12000, (12000, 10000))
    assert not state.recovery_started

    state.decide(LIMITS, 12000, (9000,))
    assert state.recovery_started
    assert state.overconsumption_wh == pytest.approx(7000 * WH_PER_W_WINDOW)

    state.decide(LIMITS, 12000, (12000,))
    assert state.recovery_started
    assert state.overconsumption_wh == pytest.approx(9000 * WH_PER_W_WINDOW)


def test_recovery_is_not_tracked_outside_a_penalty() -> None:
    """Recovery only concerns a penalty period."""
    state = overconsuming_state()

    state.decide(LIMITS, 10500, (12000, 9000))

    assert not state.recovery_started


def test_energy_follows_the_regulation_window() -> None:
    """Each average covers one regulation window."""
    limits = PenaltyLimits(10.0, 1.0, timedelta(seconds=600))
    state = PenaltyState()
    state.decide(limits, 10.5, ())

    state.decide(limits, 10.5, (16.0,))

    assert state.overconsumption_wh == pytest.approx(1.0)
