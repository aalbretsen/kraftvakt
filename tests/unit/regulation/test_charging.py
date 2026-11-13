"""Unit tests for the rules for the EV chargers."""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.kraftvakt.config_model import (
    Charger,
    ChargingWindow,
    OverrideEnd,
)
from custom_components.kraftvakt.regulation.charging import (
    ChargerReading,
    ChargerState,
    ChargerStatus,
    ChargingPermission,
    ChargingState,
    ampere_step_count,
    charging_allowed_now,
    charging_current,
    charging_permission,
    in_charging_window,
    override_arms,
    override_ended,
)

OSLO = ZoneInfo("Europe/Oslo")
NIGHT = ChargingWindow(time(22, 0), time(6, 0))
DAY = ChargingWindow(time(9, 0), time(15, 30))
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
WINDOW = timedelta(minutes=1)
CHARGING = ChargerReading(actively_charging=True)
IDLE = ChargerReading(actively_charging=False)


def charger(
    charger_id: str = "c", min_a: int = 6, max_a: int = 16, **settings
) -> Charger:
    return Charger(charger_id, min_current_a=min_a, max_current_a=max_a, **settings)


def oslo(hour: int, minute: int = 0, day: int = 7) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=OSLO)


def test_one_ampere_step_per_ampere() -> None:
    """6 A to 16 A gives 11 ampere steps."""
    assert ampere_step_count(charger(min_a=6, max_a=16)) == 11
    assert ampere_step_count(charger(min_a=6, max_a=6)) == 1


def test_current_follows_the_ampere_steps_that_are_on() -> None:
    """Four on gives 9 A, and a deactivated charger gets the minimum."""
    assert charging_current(charger(), 4) == 9
    assert charging_current(charger(), 11) == 16
    assert charging_current(charger(), 0) == 6


@pytest.mark.parametrize(
    ("window", "local_time", "expected"),
    [
        (DAY, time(9, 0), True),
        (DAY, time(15, 29), True),
        (DAY, time(15, 30), False),
        (DAY, time(8, 59), False),
        (NIGHT, time(22, 0), True),
        (NIGHT, time(23, 59), True),
        (NIGHT, time(0, 0), True),
        (NIGHT, time(5, 59), True),
        (NIGHT, time(6, 0), False),
        (NIGHT, time(12, 0), False),
    ],
)
def test_charging_window_can_reach_across_midnight(
    window: ChargingWindow, local_time: time, expected: bool
) -> None:
    """The start is inside the window and the end is not."""
    assert in_charging_window(window, local_time) is expected


DISCONNECTING = charger(
    charging_window=NIGHT, override_ends=OverrideEnd.CAR_DISCONNECTED
)
STOPPING = charger(charging_window=NIGHT, override_ends=OverrideEnd.CHARGING_STOPPED)
MANUAL = charger(charging_window=NIGHT, override_ends=OverrideEnd.MANUAL)


def test_override_ends_on_evidence_once_it_is_armed() -> None:
    """A charger that the regulation has deactivated does not stop charging."""
    armed = ChargerReading(window_override=True, override_armed=True)
    gone = replace(armed, car_disconnected=True)
    full = replace(armed, charging_stopped=True)

    assert override_ended(DISCONNECTING, gone, False)
    assert not override_ended(DISCONNECTING, full, True)
    assert override_ended(STOPPING, full, True)
    assert not override_ended(STOPPING, full, False)
    assert not override_ended(STOPPING, gone, True)
    assert not override_ended(MANUAL, replace(gone, charging_stopped=True), True)
    assert not override_ended(DISCONNECTING, replace(gone, override_armed=False), True)
    assert not override_ended(DISCONNECTING, replace(gone, window_override=False), True)
    assert not override_ended(
        charger(override_ends=OverrideEnd.CAR_DISCONNECTED), gone, True
    )


def test_override_arms_when_the_car_is_connected_or_charging() -> None:
    connected = ChargerReading(window_override=True, car_connected=True)
    charging = ChargerReading(window_override=True, actively_charging=True)

    assert override_arms(DISCONNECTING, connected, False)
    assert not override_arms(DISCONNECTING, charging, True)
    assert override_arms(STOPPING, charging, True)
    assert not override_arms(STOPPING, charging, False)
    assert not override_arms(STOPPING, replace(charging, window_override=False), True)
    assert not override_arms(MANUAL, replace(charging, car_connected=True), True)


def test_charging_permission() -> None:
    night = charger(charging_window=NIGHT)
    excluded = ChargerReading(excluded=True)
    finishing = ChargerReading(actively_charging=True, finish_after_window=True)

    assert charging_permission(charger(), IDLE, False, time(12), False) == "window"
    assert charging_permission(charger(), excluded, True, time(12), True) == "excluded"
    assert charging_permission(night, IDLE, False, time(23), False) == "window"
    assert charging_permission(night, IDLE, True, time(23), False) == "window"
    assert charging_permission(night, IDLE, True, time(12), False) == "override"
    assert charging_permission(night, IDLE, False, time(12), True) == "outside_window"
    assert charging_permission(night, finishing, False, time(12), True) == "finishing"
    assert (
        charging_permission(night, finishing, False, time(12), False)
        == "outside_window"
    )


def test_finishing_ends_without_a_car() -> None:
    no_car = ChargerReading(
        actively_charging=True, finish_after_window=True, car_connected=False
    )

    assert (
        charging_permission(
            charger(charging_window=NIGHT), no_car, False, time(12), True
        )
        == "outside_window"
    )


def test_charging_allowed_now() -> None:
    """Finishing is judged from the status after the last decision."""
    night = charger(charging_window=NIGHT, finish_after_window=True)
    charging = ChargerStatus(ChargerState.CHARGING, 2, 7, False, True, None)
    no_car = ChargerStatus(ChargerState.CHARGING, 2, 7, False, True, False)
    deactivated = ChargerStatus(ChargerState.DEACTIVATED, 0, None, False, False, None)

    assert charging_allowed_now(charger(), None, False, False, time(12))
    assert not charging_allowed_now(charger(), None, True, False, time(12))
    assert charging_allowed_now(night, None, False, True, time(12))
    assert not charging_allowed_now(night, None, False, False, time(12))
    assert charging_allowed_now(night, charging, False, False, time(12))
    assert not charging_allowed_now(night, charging, True, False, time(12))
    assert not charging_allowed_now(night, no_car, False, False, time(12))
    assert not charging_allowed_now(night, deactivated, False, False, time(12))
    assert not charging_allowed_now(
        charger(charging_window=NIGHT), charging, False, False, time(12)
    )


def chargers(*ids: str) -> list[Charger]:
    return [charger(charger_id) for charger_id in ids]


def evaluate(
    state: ChargingState,
    configured: list[Charger],
    readings: dict[str, ChargerReading],
    *,
    allowed: tuple[str, ...] | None = None,
    overridden: tuple[str, ...] = (),
    now: datetime = NOW,
    one_at_a_time: bool = True,
) -> list[str]:
    """Evaluate with each charger allowed by its window unless `allowed` says else."""
    permissions = {
        c.id: ChargingPermission.OVERRIDE
        if c.id in overridden
        else ChargingPermission.WINDOW
        if allowed is None or c.id in allowed
        else ChargingPermission.OUTSIDE_WINDOW
        for c in configured
    }
    return state.evaluate(configured, readings, permissions, now, WINDOW, one_at_a_time)


def test_priority_starts_as_configured() -> None:
    state = ChargingState.for_chargers(chargers("a", "b"))

    assert state.priority == ["a", "b"]
    assert state.ampere_steps_on == {"a": 0, "b": 0}
    assert state.activated() == []


def test_charger_without_car_is_bypassed() -> None:
    """Also when it has never been activated."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)

    newly = evaluate(
        state, configured, {"a": ChargerReading(car_connected=False), "b": IDLE}
    )

    assert newly == ["a"]
    assert state.bypassed == {"a"}
    assert state.priority == ["b", "a"]


def test_charger_that_does_not_draw_power_is_bypassed_after_two_windows() -> None:
    """The first ampere step must have been on two windows."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)

    assert evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW) == []
    assert evaluate(state, configured, {"a": CHARGING}, now=NOW + 2 * WINDOW) == []
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 2 * WINDOW) == ["a"]
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 3 * WINDOW) == []
    assert state.bypassed == {"a"}


def test_charger_that_did_not_charge_rests_also_when_deactivated() -> None:
    """It may be tried again after 15 minutes."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)
    bypassed_at = NOW + 2 * WINDOW
    evaluate(state, configured, {"a": IDLE}, now=bypassed_at)
    state.set_ampere_steps_on("a", 0)

    evaluate(state, configured, {"a": IDLE}, now=bypassed_at + timedelta(minutes=14))
    assert state.bypassed == {"a"}
    evaluate(state, configured, {"a": IDLE}, now=bypassed_at + timedelta(minutes=15))
    assert state.bypassed == set()


def test_rest_ends_when_the_charger_charges_or_the_car_is_disconnected() -> None:
    """The next rest is the first again."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)
    later = NOW + 2 * WINDOW
    evaluate(state, configured, {"a": IDLE}, now=later)
    evaluate(state, configured, {"a": IDLE}, now=later + timedelta(minutes=15))
    assert state.rests["a"].count == 1

    evaluate(state, configured, {"a": CHARGING}, now=later + timedelta(minutes=16))
    assert state.rests == {}
    evaluate(state, configured, {"a": IDLE}, now=later + timedelta(minutes=17))
    assert state.rests["a"].count == 0

    evaluate(
        state,
        configured,
        {"a": ChargerReading(car_connected=False)},
        now=later + timedelta(minutes=18),
    )
    assert state.rests == {}


def test_bypassed_charger_is_no_longer_bypassed_when_a_car_connects() -> None:
    """It stays at the back until the priority is corrected."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)
    evaluate(state, configured, {"a": ChargerReading(car_connected=False), "b": IDLE})

    evaluate(state, configured, {"a": ChargerReading(car_connected=True), "b": IDLE})

    assert state.bypassed == set()
    assert state.priority == ["b", "a"]


def test_chargers_bypassed_at_once_keep_their_order_at_the_back() -> None:
    configured = chargers("a", "b", "c", "d")
    state = ChargingState.for_chargers(configured)
    no_car = ChargerReading(car_connected=False)
    evaluate(state, configured, {"a": IDLE, "b": no_car, "c": IDLE, "d": IDLE})

    newly = evaluate(
        state, configured, {"a": no_car, "b": no_car, "c": no_car, "d": IDLE}
    )

    assert newly == ["a", "c"]
    assert state.priority == ["d", "b", "a", "c"]


def test_priority_is_corrected_when_a_charger_has_all_ampere_steps_on() -> None:
    """Bypassed chargers stay at the back."""
    configured = [charger("a"), charger("b"), charger("c", min_a=6, max_a=7)]
    state = ChargingState.for_chargers(configured)
    no_car = ChargerReading(car_connected=False)
    evaluate(state, configured, {"a": no_car, "b": no_car, "c": IDLE})
    assert state.priority == ["c", "a", "b"]
    evaluate(state, configured, {"a": IDLE, "b": no_car, "c": IDLE})
    assert state.priority == ["c", "a", "b"]

    state.set_ampere_steps_on("c", 2, NOW)
    evaluate(state, configured, {"a": IDLE, "b": no_car, "c": CHARGING})

    assert state.priority == ["a", "c", "b"]


def test_several_at_once_may_all_charge_when_allowed_and_not_bypassed() -> None:
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(
        state,
        configured,
        {"a": IDLE, "b": IDLE, "c": ChargerReading(car_connected=False)},
        allowed=("a", "c"),
        one_at_a_time=False,
    )

    assert state.may_charge == {"a"}
    assert state.waiting == set()


def test_one_at_a_time_without_charging_takes_the_first_allowed() -> None:
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": IDLE}, allowed=("b", "c"))

    assert state.may_charge == {"b"}
    assert state.waiting == set()


def test_one_at_a_time_the_charging_charger_goes_first() -> None:
    """The others are waiting, whatever their priority."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": CHARGING})

    assert state.may_charge == {"c"}
    assert state.waiting == {"a", "b"}


def test_one_at_a_time_charging_charger_not_allowed_does_not_hold_others() -> None:
    """Not a charger without valid charging power, nor one that charges."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(
        state,
        configured,
        {"a": ChargerReading(), "b": CHARGING, "c": IDLE},
        allowed=("c",),
    )

    assert state.may_charge == {"c"}
    assert state.waiting == set()


def test_one_at_a_time_the_activated_one_of_several_charging_goes_first() -> None:
    """Then the first in the current priority."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("c", 3, NOW)

    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING})
    assert state.may_charge == {"c"}

    state.set_ampere_steps_on("c", 0)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING})
    assert state.may_charge == {"b"}
    assert state.waiting == {"a", "c"}


def test_bypassed_charger_does_not_stand_in_the_way() -> None:
    """Also not when it seems to charge."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)

    evaluate(
        state,
        configured,
        {"a": ChargerReading(actively_charging=True, car_connected=False), "b": IDLE},
    )

    assert state.may_charge == {"b"}


def test_status_of_each_charger() -> None:
    configured = chargers("a", "b", "c", "d")
    state = ChargingState.for_chargers(configured)
    assert state.status(configured)["a"].state is ChargerState.FIRST_DECISION
    state.set_ampere_steps_on("a", 4, NOW)
    evaluate(
        state,
        configured,
        {
            "a": ChargerReading(actively_charging=True, car_connected=True),
            "b": IDLE,
            "c": ChargerReading(car_connected=False),
            "d": IDLE,
        },
        allowed=("a", "c", "d"),
        overridden=("a",),
        one_at_a_time=False,
    )

    assert state.status(configured) == {
        "a": ChargerStatus(ChargerState.OVERRIDE, 4, 9, False, True, True),
        "b": ChargerStatus(ChargerState.OUTSIDE_WINDOW, 0, None, False, False, None),
        "c": ChargerStatus(ChargerState.NO_CAR, 0, None, True, False, False),
        "d": ChargerStatus(ChargerState.DEACTIVATED, 0, None, False, False, None),
    }


def test_charging_needs_an_activated_charger() -> None:
    """A charger is not charging once it is deactivated, nor before it is."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": CHARGING})

    state.set_ampere_steps_on("a", 0)

    assert not state.status(configured)["a"].charging
    assert not state.status(configured)["b"].charging


def test_activating_needs_the_time() -> None:
    state = ChargingState.for_chargers(chargers("a"))

    with pytest.raises(ValueError, match="time"):
        state.set_ampere_steps_on("a", 1)
