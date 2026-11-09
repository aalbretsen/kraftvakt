"""Scenario tests for increasing waiting time on persistent cycling."""

from datetime import timedelta

from .configs import make_config
from .scenario import Scenario, off, on

ABOVE_LIMIT = 10_500
NO_LOAD = 0


def minutes_until_on(scenario: Scenario, appliance_id: str) -> float:
    """Decide without load until the appliance is on and return the waiting time.

    Without load, the waiting time from the curve is 0, so only persistent
    cycling makes the regulation wait.
    """
    assert scenario.decide(NO_LOAD) in ([], on(appliance_id))
    waiting_started = scenario.now
    while appliance_id not in scenario.engine.appliances_on:
        assert scenario.decide(NO_LOAD) in ([], on(appliance_id))
    return (scenario.now - waiting_started) / timedelta(minutes=1)


def cycle(scenario: Scenario, appliance_id: str) -> float:
    """Switch the appliance off above the limit and return the wait to turn it on."""
    assert scenario.decide(ABOVE_LIMIT) == off(appliance_id)
    return minutes_until_on(scenario, appliance_id)


def test_waiting_time_grows_on_persistent_cycling() -> None:
    """From the second time on again: 5, 7, 9, 11, 13 and then 15 minutes."""
    scenario = Scenario(make_config("a"))
    scenario.turn_on("a")

    waits = [cycle(scenario, "a") for _ in range(8)]

    assert waits == [0, 5, 7, 9, 11, 13, 15, 15]


def test_waiting_time_grows_with_the_configured_step_and_cap() -> None:
    """Step 1 minute and cap 8 minutes: 5, 6, 7 and then 8 minutes."""
    scenario = Scenario(make_config("a", appliance_cycling_s=(60, 480)))
    scenario.turn_on("a")

    waits = [cycle(scenario, "a") for _ in range(6)]

    assert waits == [0, 5, 6, 7, 8, 8]


def test_switching_another_appliance_resets_the_increase() -> None:
    """The increase is reset as soon as another appliance is switched."""
    scenario = Scenario(make_config("a", "b"))
    scenario.turn_on("a", "b")
    assert [cycle(scenario, "b") for _ in range(3)] == [0, 5, 7]

    assert scenario.decide(ABOVE_LIMIT) == off("b")
    assert scenario.decide(ABOVE_LIMIT) == off("a")

    assert minutes_until_on(scenario, "a") == 0
    assert minutes_until_on(scenario, "b") == 0
    assert cycle(scenario, "b") == 0
    assert cycle(scenario, "b") == 5


def test_restart_resets_the_increase() -> None:
    """The counters for increasing waiting time start again."""
    scenario = Scenario(make_config("a"))
    scenario.turn_on("a")
    assert [cycle(scenario, "a") for _ in range(3)] == [0, 5, 7]

    scenario.engine.start(scenario.now)

    assert minutes_until_on(scenario, "a") == 0
    assert cycle(scenario, "a") == 0
    assert cycle(scenario, "a") == 5


def test_persistent_cycling_still_needs_room_under_the_limit() -> None:
    """The appliance still needs room under the limit while the waiting runs."""
    scenario = Scenario(make_config("a"))
    scenario.turn_on("a")
    assert [cycle(scenario, "a") for _ in range(2)] == [0, 5]
    assert scenario.decide(ABOVE_LIMIT) == off("a")

    assert scenario.decide_many(NO_LOAD, 4) == [[], [], [], []]
    assert scenario.decide(10000) == []
    assert scenario.decide_many(NO_LOAD, 7) == [[]] * 7
    assert scenario.decide(NO_LOAD) == on("a")
