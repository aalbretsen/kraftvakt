"""Scenario tests for the safe state in the engine."""

from .configs import make_config
from .scenario import Scenario, off, on

ABOVE_THRESHOLD = 11_500


def no_waiting(*appliances):
    return make_config(*appliances, wait_at_limit_s=0)


def test_lost_power_sensor_turns_everything_off_at_once() -> None:
    """Every appliance in the configuration, at one decision."""
    scenario = Scenario(no_waiting("a", "b", "c"))
    scenario.turn_on("a", "b")

    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == off("a", "b", "c")
    assert scenario.engine.safe_state
    assert scenario.engine.appliances_on == frozenset()


def test_one_invalid_close_is_tolerated() -> None:
    """The regulation goes on with the average from the last valid value."""
    scenario = Scenario(no_waiting("a", "b"))

    assert scenario.decide(2000, sensor_valid=False) == on("a")
    assert not scenario.engine.safe_state


def test_nothing_is_turned_on_in_the_safe_state() -> None:
    scenario = Scenario(no_waiting("a"))
    scenario.decide(None, sensor_valid=False, sensor_lost=True)

    assert scenario.decide(2000, sensor_valid=False) == []
    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == []
    assert scenario.engine.safe_state


def test_regulation_starts_again_when_the_sensor_is_back() -> None:
    """Everything off, a new state, then on one by one."""
    scenario = Scenario(no_waiting("a", "b"))
    scenario.turn_on("a")
    scenario.decide(None, sensor_valid=False, sensor_lost=True)

    assert scenario.decide(2000) == off("a", "b")
    assert not scenario.engine.safe_state
    assert scenario.engine.started_at == scenario.now
    assert scenario.decide(2000) == on("a")


def test_safe_state_without_any_average() -> None:
    """No measurement since the start also leads to the safe state."""
    scenario = Scenario(no_waiting("a"))

    assert scenario.decide(None, sensor_valid=False) == []
    assert scenario.decide(None, sensor_valid=False, sensor_lost=True) == off("a")
    assert scenario.engine.safe_state


def test_safe_state_ends_a_penalty() -> None:
    """The restart after the safe state forgets the overconsumption."""
    scenario = Scenario(no_waiting("a"))
    scenario.decide(10000, tariff=ABOVE_THRESHOLD)
    scenario.decide(16000, tariff=ABOVE_THRESHOLD)
    assert scenario.engine.penalty.active

    scenario.decide(None, sensor_valid=False, sensor_lost=True)
    scenario.decide(2000, tariff=ABOVE_THRESHOLD)

    assert not scenario.engine.penalty.active
    assert scenario.engine.penalty.overconsumption_wh == 0.0


def test_stop_leaves_the_safe_state() -> None:
    scenario = Scenario(no_waiting("a"))
    scenario.decide(None, sensor_valid=False, sensor_lost=True)

    scenario.engine.stop()

    assert not scenario.engine.safe_state
