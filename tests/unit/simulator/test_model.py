"""Unit tests for the power models of the simulated devices."""

from datetime import timedelta

import pytest

from custom_components.kraftvakt_simulator.model import (
    ChargerState,
    DutyCycle,
    thermostat_heats,
    three_phase_power_w,
)


def minutes(value: float) -> timedelta:
    return timedelta(minutes=value)


def heating_cable(duty_cycle_pct: int = 25) -> DutyCycle:
    return DutyCycle(
        power_w=750, duty_cycle_pct=duty_cycle_pct, period=timedelta(hours=1)
    )


@pytest.mark.parametrize(
    ("elapsed", "heating"),
    [
        (minutes(0), True),
        (minutes(14.99), True),
        (minutes(15), False),
        (minutes(59.99), False),
        (minutes(60), True),
        (minutes(105), False),
    ],
)
def test_the_cycle_is_on_first_then_off(elapsed: timedelta, heating: bool) -> None:
    """750 W at 25 % of an hour: on 15 minutes, off 45, again and again."""
    cycle = heating_cable()

    assert cycle.is_heating(elapsed) is heating
    assert cycle.power_at(elapsed) == (750 if heating else 0)


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [
        (minutes(0), minutes(15)),
        (minutes(10), minutes(5)),
        (minutes(15), minutes(45)),
        (minutes(30), minutes(30)),
        (minutes(60), minutes(15)),
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


@pytest.mark.parametrize(
    ("hvac_mode", "target", "room", "heats"),
    [
        ("heat", 21, 5, True),
        ("heat_cool", 21, 5, True),
        ("auto", 21, 5, True),
        ("heat", 21, 21, False),
        ("off", 21, 5, False),
        ("cool", 21, 5, False),
        ("fan_only", 21, 5, False),
    ],
)
def test_thermostat_heats_in_a_heating_mode_below_the_target(
    hvac_mode: str, target: float, room: float, heats: bool
) -> None:
    assert thermostat_heats(hvac_mode, target, room) is heats
