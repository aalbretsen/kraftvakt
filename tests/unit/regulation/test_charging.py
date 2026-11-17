"""Unit tests for the rules for the EV chargers."""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.kraftvakt.config_model import (
    Charger,
    ChargerGroup,
    ChargingWindow,
    Condition,
    ConditionType,
    OverrideEnd,
)
from custom_components.kraftvakt.regulation.charging import (
    ChargerChanges,
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
CHARGING = ChargerReading(actively_charging=True, car_connected=True)
IDLE = ChargerReading(car_connected=True)
FULL = ChargerReading(car_connected=True, car_done=True)
NOT_FULL = ChargerReading(car_connected=True, car_not_done=True)
DONE_FLAG = Condition(ConditionType.ENTITY, "binary_sensor.done")


def charger(charger_id: str = "c", min_a: int = 6, max_a: int = 16, **settings) -> Charger:
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
def test_charging_window_can_reach_across_midnight(window: ChargingWindow, local_time: time, expected: bool) -> None:
    """The start is inside the window and the end is not."""
    assert in_charging_window(window, local_time) is expected


DISCONNECTING = charger(charging_window=NIGHT, override_ends=OverrideEnd.CAR_DISCONNECTED)
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
    assert not override_ended(charger(override_ends=OverrideEnd.CAR_DISCONNECTED), gone, True)
    assert not override_ended(DISCONNECTING, replace(gone, fault=True), False)


def test_override_arms_when_the_car_is_connected_or_charging() -> None:
    connected = ChargerReading(window_override=True, car_connected=True)
    charging = ChargerReading(window_override=True, actively_charging=True)

    assert override_arms(DISCONNECTING, connected, False)
    assert not override_arms(DISCONNECTING, charging, True)
    assert override_arms(STOPPING, charging, True)
    assert not override_arms(STOPPING, charging, False)
    assert not override_arms(STOPPING, replace(charging, window_override=False), True)
    assert not override_arms(MANUAL, replace(charging, car_connected=True), True)
    assert not override_arms(DISCONNECTING, replace(connected, fault=True), False)


def test_charging_permission() -> None:
    night = charger(charging_window=NIGHT)
    excluded = ChargerReading(excluded=True)
    finishing = replace(CHARGING, finish_after_window=True)

    assert charging_permission(charger(), IDLE, False, time(12), False) == "window"
    assert charging_permission(charger(), excluded, True, time(12), True) == "excluded"
    assert charging_permission(night, replace(excluded, fault=True), True, time(23), True) == "fault"
    assert charging_permission(night, IDLE, False, time(23), False) == "window"
    assert charging_permission(night, IDLE, True, time(23), False) == "window"
    assert charging_permission(night, IDLE, True, time(12), False) == "override"
    assert charging_permission(night, IDLE, False, time(12), True) == "outside_window"
    assert charging_permission(night, finishing, False, time(12), True) == "finishing"
    assert charging_permission(night, finishing, False, time(12), False) == "outside_window"


def test_finishing_ends_without_a_car() -> None:
    no_car = ChargerReading(actively_charging=True, finish_after_window=True, car_connected=False)

    assert charging_permission(charger(charging_window=NIGHT), no_car, False, time(12), True) == "outside_window"


def test_charging_allowed_now() -> None:
    """Finishing is judged from the status after the last decision."""
    night = charger(charging_window=NIGHT, finish_after_window=True)
    charging = ChargerStatus(ChargerState.CHARGING, 2, 7, False, True, True)
    no_car = ChargerStatus(ChargerState.CHARGING, 2, 7, False, True, False)
    deactivated = ChargerStatus(ChargerState.DEACTIVATED, 0, None, False, False, True)
    fault = ChargerStatus(ChargerState.FAULT, 0, None, False, False, True)

    assert charging_allowed_now(charger(), None, False, False, time(12))
    assert not charging_allowed_now(charger(), None, True, False, time(12))
    assert charging_allowed_now(night, None, False, True, time(12))
    assert not charging_allowed_now(night, None, False, False, time(12))
    assert charging_allowed_now(night, charging, False, False, time(12))
    assert not charging_allowed_now(night, charging, True, False, time(12))
    assert not charging_allowed_now(night, no_car, False, False, time(12))
    assert not charging_allowed_now(night, deactivated, False, False, time(12))
    assert not charging_allowed_now(charger(charging_window=NIGHT), charging, False, False, time(12))
    assert not charging_allowed_now(charger(), fault, False, False, time(12))


def chargers(*ids: str) -> list[Charger]:
    return [charger(charger_id) for charger_id in ids]


def evaluate(
    state: ChargingState,
    configured: list[Charger],
    readings: dict[str, ChargerReading],
    *,
    allowed: tuple[str, ...] | None = None,
    overridden: tuple[str, ...] = (),
    faulty: tuple[str, ...] = (),
    now: datetime = NOW,
    one_at_a_time: bool = True,
    dynamic_order: bool = False,
) -> ChargerChanges:
    """Evaluate with each charger allowed by its window unless `allowed` says else."""

    def permission(charger_id: str) -> ChargingPermission:
        if charger_id in faulty:
            return ChargingPermission.FAULT
        if charger_id in overridden:
            return ChargingPermission.OVERRIDE
        return ChargingPermission.WINDOW if allowed is None or charger_id in allowed else ChargingPermission.OUTSIDE_WINDOW

    group = ChargerGroup("ev", chargers=tuple(configured), one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    return state.evaluate(group, readings, {c.id: permission(c.id) for c in configured}, now, WINDOW)


def group_of(configured: list[Charger], *, one_at_a_time: bool = True, dynamic_order: bool = False) -> ChargerGroup:
    return ChargerGroup("ev", chargers=tuple(configured), one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)


def test_priority_starts_as_configured() -> None:
    state = ChargingState.for_chargers(chargers("a", "b"))

    assert state.priority == ["a", "b"]
    assert state.ampere_steps_on == {"a": 0, "b": 0}
    assert state.activated() == []


def test_charger_without_car_is_bypassed_and_moves_back_only_with_dynamic_order() -> None:
    """Also when it has never been activated."""
    configured = chargers("a", "b")
    fixed = ChargingState.for_chargers(configured)
    dynamic = ChargingState.for_chargers(configured)
    readings = {"a": ChargerReading(car_connected=False), "b": IDLE}

    assert evaluate(fixed, configured, readings).bypassed == ["a"]
    evaluate(dynamic, configured, readings, dynamic_order=True)

    assert fixed.bypassed == dynamic.bypassed == {"a"}
    assert fixed.priority == ["a", "b"]
    assert dynamic.priority == ["b", "a"]


def test_car_that_does_not_start_is_done_until_it_is_disconnected() -> None:
    """The first ampere step must have been on two windows. Only evidence of a disconnected car ends it."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)

    assert evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW).done == []
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 2 * WINDOW).done == ["a"]
    state.set_ampere_steps_on("a", 0)
    evaluate(state, configured, {"a": ChargerReading()}, now=NOW + 3 * WINDOW)
    assert state.done == {"a"}
    assert state.may_charge == set()

    evaluate(state, configured, {"a": ChargerReading(car_disconnected=True)}, now=NOW + 4 * WINDOW)
    assert state.done == set()
    evaluate(state, configured, {"a": IDLE}, now=NOW + 5 * WINDOW)
    assert state.may_charge == {"a"}


def test_car_that_stops_charging_is_in_grace_and_done_when_the_grace_period_ends() -> None:
    """A car that charges again within the grace period goes on, and starts a new grace period when it stops again."""
    configured = [charger("a", grace_period_s=300)]
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 3, NOW)
    evaluate(state, configured, {"a": CHARGING})

    assert evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW).grace == ["a"]
    assert state.charging == {"a"}
    assert state.status(group_of(configured))["a"] == ChargerStatus(ChargerState.GRACE, 3, 8, False, True, True, grace_until=NOW + WINDOW + timedelta(minutes=5))
    assert evaluate(state, configured, {"a": CHARGING}, now=NOW + 5 * WINDOW).resumed == {"a"}
    assert state.grace == {}

    evaluate(state, configured, {"a": IDLE}, now=NOW + 6 * WINDOW)
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 10 * WINDOW).done == []
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 11 * WINDOW).done == ["a"]
    assert state.charging == set()


@pytest.mark.parametrize("charged", [False, True])
def test_done_flag_makes_a_charger_on_trial_or_in_grace_done_at_once(charged: bool) -> None:
    configured = [charger("a", detect_done=True, done_flag=DONE_FLAG)]
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 2, NOW)
    if charged:
        evaluate(state, configured, {"a": CHARGING})
        evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW)

    assert evaluate(state, configured, {"a": FULL}, now=NOW + WINDOW).done == ["a"]


def test_done_flag_makes_a_charger_done_before_it_is_tried() -> None:
    """So a full car is not tried after a start. Not while it charges, nor without a car, or when it may not charge."""
    configured = [charger(charger_id, detect_done=True, done_flag=DONE_FLAG) for charger_id in ("a", "b", "c", "d")]
    state = ChargingState.for_chargers(configured)
    full_without_car = ChargerReading(car_done=True)
    full_and_charging = replace(CHARGING, car_done=True)

    changes = evaluate(state, configured, {"a": FULL, "b": full_and_charging, "c": full_without_car, "d": FULL}, allowed=("a", "b", "c"), one_at_a_time=False)

    assert changes.done == ["a"]
    assert state.may_charge == {"b"}
    assert evaluate(state, configured, {"a": FULL, "d": FULL}, now=NOW + WINDOW, one_at_a_time=False).done == ["d"]


def test_without_evidence_from_the_done_flag_neither_the_time_to_start_nor_the_grace_period_ends() -> None:
    """The car stays on trial or in grace until the done flag tells whether it is done."""
    configured = [charger("a", detect_done=True, done_flag=DONE_FLAG, grace_period_s=60), charger("b", detect_done=True, done_flag=DONE_FLAG)]
    group = group_of(configured, one_at_a_time=False)
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 2, NOW)
    state.set_ampere_steps_on("b", 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": IDLE}, one_at_a_time=False)
    evaluate(state, configured, {"a": IDLE, "b": IDLE}, now=NOW + WINDOW, one_at_a_time=False)

    assert evaluate(state, configured, {"a": IDLE, "b": IDLE}, now=NOW + 10 * WINDOW, one_at_a_time=False).done == []
    assert state.grace == {"a": NOW + WINDOW}
    assert state.on_trial == {"a", "b"}
    assert state.status(group)["a"].grace_until is None
    assert evaluate(state, configured, {"a": NOT_FULL, "b": NOT_FULL}, now=NOW + 11 * WINDOW, one_at_a_time=False).done == ["a", "b"]


def test_charger_waiting_for_its_done_flag_holds_its_reserve() -> None:
    configured = [charger("a", detect_done=True, done_flag=DONE_FLAG, cloud_controlled=True, start_delay_s=0)]
    group = group_of(configured)
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)

    evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW)
    assert state.status(group)["a"] == ChargerStatus(ChargerState.STARTING, 1, 6, False, False, True, starting_until=NOW + 2 * WINDOW)
    evaluate(state, configured, {"a": IDLE}, now=NOW + 5 * WINDOW)
    assert state.status(group)["a"] == ChargerStatus(ChargerState.STARTING, 1, 6, False, False, True)
    evaluate(state, configured, {"a": NOT_FULL}, now=NOW + 6 * WINDOW)
    assert state.starting == {}


@pytest.mark.parametrize(
    ("reading", "faulty", "allowed"),
    [
        (ChargerReading(car_connected=False), (), None),
        (IDLE, ("a",), None),
        (IDLE, (), ()),
    ],
)
def test_charger_without_car_with_a_fault_or_not_allowed_is_neither_in_grace_nor_done(reading: ChargerReading, faulty: tuple[str, ...], allowed: tuple[str, ...] | None) -> None:
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 2, NOW)
    evaluate(state, configured, {"a": CHARGING})

    changes = evaluate(state, configured, {"a": reading}, faulty=faulty, allowed=allowed, now=NOW + 10 * WINDOW)

    assert changes.grace == changes.done == []


def test_car_connected_again_gets_two_windows_on_a_charger_that_stayed_activated() -> None:
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)
    evaluate(state, configured, {"a": ChargerReading(car_connected=False)}, now=NOW + 10 * WINDOW)
    connected = ChargerReading(car_connected=True)

    assert evaluate(state, configured, {"a": connected}, now=NOW + 11 * WINDOW).done == []
    assert evaluate(state, configured, {"a": connected}, now=NOW + 12 * WINDOW).done == []
    assert state.bypassed == set()
    assert evaluate(state, configured, {"a": connected}, now=NOW + 13 * WINDOW).done == ["a"]


def test_chargers_that_stop_charging_move_back_with_dynamic_order_keeping_their_order() -> None:
    """A charger with a fault moves back too."""
    configured = chargers("a", "b", "c", "d", "e")
    state = ChargingState.for_chargers(configured)
    for charger_id in ("a", "c", "e"):
        state.set_ampere_steps_on(charger_id, 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": IDLE, "c": CHARGING, "d": IDLE, "e": CHARGING}, one_at_a_time=False, dynamic_order=True)

    state.set_ampere_steps_on("a", 0)
    state.set_ampere_steps_on("c", 0)
    evaluate(
        state,
        configured,
        {"a": IDLE, "b": ChargerReading(car_connected=False), "c": IDLE, "d": IDLE, "e": IDLE},
        faulty=("e",),
        one_at_a_time=False,
        dynamic_order=True,
    )

    assert state.priority == ["d", "a", "b", "c", "e"]


def test_several_at_once_may_all_charge_when_allowed_and_not_bypassed_or_done() -> None:
    configured = chargers("a", "b", "c", "d")
    state = ChargingState.for_chargers(configured)
    state.done = {"d"}

    evaluate(
        state,
        configured,
        {"a": IDLE, "b": IDLE, "c": ChargerReading(car_connected=False), "d": IDLE},
        allowed=("a", "c", "d"),
        one_at_a_time=False,
    )

    assert state.may_charge == {"a"}
    assert state.waiting == set()


def test_with_dynamic_order_the_chargers_that_charge_come_first_and_the_others_are_queued() -> None:
    """The chargers that charge are in the configured priority, one that charges again after its grace period first."""
    configured = chargers("a", "b", "c", "d")
    group = group_of(configured, one_at_a_time=False, dynamic_order=True)
    state = ChargingState.for_chargers(configured)
    for charger_id in ("b", "c", "d"):
        state.set_ampere_steps_on(charger_id, 2, NOW)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING, "d": CHARGING}, one_at_a_time=False, dynamic_order=True)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING, "d": IDLE}, one_at_a_time=False, dynamic_order=True)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING, "d": CHARGING}, one_at_a_time=False, dynamic_order=True)

    assert state.order(group) == ["d", "b", "c", "a"]
    assert state.queued(group) == ["a"]
    assert state.waiting == {"a"}
    assert state.status(group)["a"].state is ChargerState.QUEUED


def test_one_at_a_time_without_dynamic_order_takes_the_first_allowed_whatever_charges() -> None:
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("c", 3, NOW)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": CHARGING}, allowed=("b", "c"))

    assert state.may_charge == {"b"}
    assert state.waiting == {"c"}


def test_one_at_a_time_with_dynamic_order_the_charging_charger_goes_first() -> None:
    """The others are queued, whatever their priority."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": CHARGING}, dynamic_order=True)

    assert state.may_charge == {"c"}
    assert state.waiting == {"a", "b"}


def test_one_at_a_time_charging_charger_not_allowed_does_not_hold_others() -> None:
    """Not a charger without valid charging power, nor one that charges."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": ChargerReading(), "b": CHARGING, "c": IDLE}, allowed=("c",), dynamic_order=True)

    assert state.may_charge == {"c"}
    assert state.waiting == set()


def test_one_at_a_time_the_activated_one_of_several_charging_goes_first() -> None:
    """Then the first in the current priority."""
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("c", 3, NOW)

    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING}, dynamic_order=True)
    assert state.may_charge == {"c"}

    state.set_ampere_steps_on("c", 0)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING}, dynamic_order=True)
    assert state.may_charge == {"b"}
    assert state.waiting == {"a", "c"}


def test_bypassed_charger_does_not_stand_in_the_way() -> None:
    """Also not when it seems to charge."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": ChargerReading(actively_charging=True, car_connected=False), "b": IDLE}, dynamic_order=True)

    assert state.may_charge == {"b"}


def test_status_of_each_charger() -> None:
    configured = chargers("a", "b", "c", "d", "e")
    group = group_of(configured, one_at_a_time=False)
    state = ChargingState.for_chargers(configured)
    assert state.status(group)["a"].state is ChargerState.FIRST_DECISION
    state.set_ampere_steps_on("a", 4, NOW)
    state.done = {"e"}
    evaluate(
        state,
        configured,
        {"a": CHARGING, "b": IDLE, "c": ChargerReading(car_connected=False), "d": IDLE, "e": IDLE},
        allowed=("a", "c", "d", "e"),
        overridden=("a",),
        one_at_a_time=False,
    )

    assert state.status(group) == {
        "a": ChargerStatus(ChargerState.OVERRIDE, 4, 9, False, True, True),
        "b": ChargerStatus(ChargerState.OUTSIDE_WINDOW, 0, None, False, False, True),
        "c": ChargerStatus(ChargerState.NO_CAR, 0, None, True, False, False),
        "d": ChargerStatus(ChargerState.DEACTIVATED, 0, None, False, False, True),
        "e": ChargerStatus(ChargerState.DONE, 0, None, False, False, True),
    }


def test_charging_needs_an_activated_charger() -> None:
    """A charger is not charging once it is deactivated, nor before it is."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": CHARGING})

    state.set_ampere_steps_on("a", 0)

    assert not state.status(group_of(configured))["a"].charging
    assert not state.status(group_of(configured))["b"].charging


@pytest.mark.parametrize(
    ("cloud_controlled", "one_at_a_time", "dynamic_order", "starting"),
    [(True, True, False, True), (False, False, True, True), (False, False, False, False), (False, True, True, False)],
)
def test_charger_on_trial_holds_its_reserve_when_cloud_controlled_or_sharing_by_charging_power(
    cloud_controlled: bool, one_at_a_time: bool, dynamic_order: bool, starting: bool
) -> None:
    """Until it has charged, and for at most its time to start."""
    configured = [charger("a", cloud_controlled=cloud_controlled, start_delay_s=0)]
    state = ChargingState.for_chargers(configured)
    state.set_ampere_steps_on("a", 1, NOW)

    evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    assert ("a" in state.starting) is starting
    evaluate(state, configured, {"a": CHARGING}, now=NOW + WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    assert state.starting == {}


def test_activating_needs_the_time() -> None:
    state = ChargingState.for_chargers(chargers("a"))

    with pytest.raises(ValueError, match="time"):
        state.set_ampere_steps_on("a", 1)
