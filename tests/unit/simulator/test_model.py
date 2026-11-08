"""Unit tests for the power models of the simulated devices."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt_simulator.model import (
    ChargerState,
    DutyCycle,
    three_phase_power_w,
)

HOUR = timedelta(hours=1)


def minutes(value: float) -> timedelta:
    return timedelta(minutes=value)


def heating_cable(duty_cycle_pct: int = 25) -> DutyCycle:
    return DutyCycle(power_w=750, duty_cycle_pct=duty_cycle_pct, period=HOUR)


@pytest.mark.parametrize(
    ("elapsed", "heating"),
    [
        (minutes(0), False),
        (minutes(44.99), False),
        (minutes(45), True),
        (minutes(59.99), True),
        (minutes(60), False),
        (minutes(105), True),
    ],
)
def test_the_cycle_is_off_first_then_on(elapsed: timedelta, heating: bool) -> None:
    """750 W at 25 % of an hour: off 45 minutes, on 15, again and again."""
    cycle = heating_cable()

    assert cycle.is_heating(elapsed) is heating
    assert cycle.power_at(elapsed) == (750 if heating else 0)


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [
        (minutes(0), minutes(45)),
        (minutes(30), minutes(15)),
        (minutes(45), minutes(15)),
        (minutes(50), minutes(10)),
        (minutes(60), minutes(45)),
    ],
)
def test_time_to_next_change(elapsed: timedelta, expected: timedelta) -> None:
    assert heating_cable().time_to_next_change(elapsed) == expected


@pytest.mark.parametrize(("duty_cycle_pct", "heating"), [(0, False), (100, True)])
def test_a_full_or_empty_duty_cycle_never_changes(
    duty_cycle_pct: int, heating: bool
) -> None:
    cycle = heating_cable(duty_cycle_pct)

    assert cycle.time_to_next_change(minutes(0)) is None
    assert cycle.is_heating(minutes(0)) is heating
    assert cycle.is_heating(minutes(59)) is heating


def test_three_phase_power() -> None:
    """6 A on 400 V three-phase with power factor 1 is 4.16 kW."""
    assert three_phase_power_w(6) == pytest.approx(4156.9, abs=0.1)
    assert three_phase_power_w(16) == pytest.approx(11085.1, abs=0.1)


@pytest.mark.parametrize(
    ("allowed", "connected", "fully_charged", "power_w"),
    [
        (True, True, False, three_phase_power_w(10)),
        (False, True, False, 0.0),
        (True, False, False, 0.0),
        (True, True, True, 0.0),
    ],
)
def test_the_charger_draws_power_only_for_a_car_that_charges(
    allowed: bool, connected: bool, fully_charged: bool, power_w: float
) -> None:
    state = ChargerState(
        charging_allowed=allowed,
        current_a=10,
        car_connected=connected,
        car_fully_charged=fully_charged,
    )

    assert state.power_w == power_w
