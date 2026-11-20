"""Unit tests for the rules for the EV chargers."""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.kraftvakt.config_model import (
    Charger,
    ChargerGroup,
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
    estimated_draw_w,
    in_charging_window,
    may_step_up,
    override_arms,
    override_ended,
)

OSLO = ZoneInfo("Europe/Oslo")
NIGHT = ChargingWindow(time(22, 0), time(6, 0))
DAY = ChargingWindow(time(9, 0), time(15, 30))
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
WINDOW = timedelta(minutes=1)
CHARGING = ChargerReading(actively_charging=True, car_connected=True, charging_power_w=4000)
IDLE = ChargerReading(car_connected=True, charging_power_w=0)


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


@pytest.mark.parametrize(
    ("reading", "expected"),
    [
        (ChargerReading(actively_charging=True, charging_power_w=2000), True),
        (ChargerReading(actively_charging=True, charging_power_w=1999), False),
        (ChargerReading(actively_charging=True), False),
        (ChargerReading(charging_power_w=2000), False),
    ],
)
def test_car_may_step_up_when_it_charges_with_half_of_the_power_at_minimum_current(reading: ChargerReading, expected: bool) -> None:
    assert may_step_up(charger(min_current_power_w=4000), reading) is expected


def test_estimated_draw_follows_the_current_and_never_exceeds_what_the_car_draws() -> None:
    """With 4 ampere steps from 6 A, the current is 9 A."""
    six_to_sixteen = charger()

    assert estimated_draw_w(six_to_sixteen, 10_000, 4, 690) == pytest.approx(6210)
    assert estimated_draw_w(six_to_sixteen, 5000, 4, 690) == 5000
    assert estimated_draw_w(six_to_sixteen, 5000, 0, 690) == 0


def chargers(*ids: str) -> list[Charger]:
    return [charger(charger_id) for charger_id in ids]


def group_of(configured: list[Charger], *, one_at_a_time: bool = True, dynamic_order: bool = False) -> ChargerGroup:
    return ChargerGroup("ev", chargers=tuple(configured), one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)


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
) -> list[str]:
    """Evaluate with each charger allowed by its window unless `allowed` says else."""

    def permission(charger_id: str) -> ChargingPermission:
        if charger_id in faulty:
            return ChargingPermission.FAULT
        if charger_id in overridden:
            return ChargingPermission.OVERRIDE
        return ChargingPermission.WINDOW if allowed is None or charger_id in allowed else ChargingPermission.OUTSIDE_WINDOW

    group = group_of(configured, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    return state.evaluate(group, readings, {c.id: permission(c.id) for c in configured}, now)


def activated(configured: list[Charger], **ampere_steps_on: int) -> ChargingState:
    state = ChargingState.for_chargers(configured)
    for charger_id, count in ampere_steps_on.items():
        state.set_ampere_steps_on(charger_id, count, NOW)
    return state


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

    assert evaluate(fixed, configured, readings) == ["a"]
    evaluate(dynamic, configured, readings, dynamic_order=True)
    assert evaluate(fixed, configured, readings) == []

    assert fixed.bypassed == dynamic.bypassed == {"a"}
    assert fixed.priority == ["a", "b"]
    assert dynamic.priority == ["b", "a"]


def test_car_that_does_not_draw_enough_is_held_at_minimum() -> None:
    """A car that charges with less than half of the power at minimum current, or does not charge, is held. Kraftvakt never guesses that it is done."""
    configured = chargers("a", "b", "c")
    state = activated(configured, a=3, b=3, c=3)

    evaluate(state, configured, {"a": CHARGING, "b": replace(CHARGING, charging_power_w=1000), "c": IDLE}, one_at_a_time=False)

    assert state.held_at_min == {"b", "c"}
    assert state.may_charge == {"a", "b", "c"}
    assert state.charging == {"a", "b"}


def test_chargers_that_start_charging_move_ahead_and_those_that_stop_move_back_with_dynamic_order() -> None:
    """Each keeping their order. A charger with a fault moves back too."""
    configured = chargers("a", "b", "c", "d", "e")
    state = activated(configured, a=1, c=1, e=1)
    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": CHARGING, "d": IDLE, "e": CHARGING}, one_at_a_time=False, dynamic_order=True)
    assert state.priority == ["c", "e", "a", "b", "d"]

    readings = {"a": CHARGING, "b": ChargerReading(car_connected=False), "c": IDLE, "d": IDLE, "e": CHARGING}
    evaluate(state, configured, readings, faulty=("e",), one_at_a_time=False, dynamic_order=True)

    assert state.priority == ["a", "d", "c", "e", "b"]


def test_several_at_once_may_all_charge_when_allowed_and_not_bypassed() -> None:
    configured = chargers("a", "b", "c")
    state = ChargingState.for_chargers(configured)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": ChargerReading(car_connected=False)}, allowed=("a", "c"), one_at_a_time=False)

    assert state.may_charge == {"a"}
    assert state.waiting == set()


def test_with_dynamic_order_the_activated_chargers_come_first_and_the_others_are_queued() -> None:
    """The activated chargers are in the configured priority, the queued ones in the current charging priority."""
    configured = chargers("a", "b", "c", "d")
    group = group_of(configured, one_at_a_time=False, dynamic_order=True)
    state = activated(configured, b=2, d=2)
    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING, "d": CHARGING}, one_at_a_time=False, dynamic_order=True)

    assert state.order(group) == ["b", "d", "a", "c"]
    assert state.queued(group) == ["a", "c"]
    assert state.waiting == {"a", "c"}
    assert state.status(group)["a"].state is ChargerState.QUEUED


def test_one_at_a_time_without_dynamic_order_the_chargers_before_the_one_that_charges_may_wait_at_their_minimum() -> None:
    """Those after it are queued and deactivated."""
    configured = chargers("a", "b", "c")
    group = group_of(configured)
    state = activated(configured, a=1, b=3, c=1)

    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING})

    assert state.may_charge == {"a", "b"}
    assert state.waiting == {"c"}
    assert not state.must_deactivate(group, "a")
    assert state.must_deactivate(group, "c")


def test_one_at_a_time_every_charger_with_a_car_may_be_activated_while_none_charges() -> None:
    configured = chargers("a", "b", "c")
    state = activated(configured, a=1)

    evaluate(state, configured, {"a": IDLE, "b": IDLE, "c": ChargerReading(car_connected=False)})

    assert state.may_charge == {"a", "b"}
    assert state.waiting == set()


def test_one_at_a_time_with_dynamic_order_the_charger_that_charges_keeps_its_turn() -> None:
    """Of two that start at once, the first in the current priority goes first. One that is not activated does not charge."""
    configured = chargers("a", "b", "c")
    state = activated(configured, b=1, c=1)

    evaluate(state, configured, {"a": CHARGING, "b": CHARGING, "c": CHARGING}, dynamic_order=True)
    assert state.may_charge == {"b"}
    assert state.waiting == {"a", "c"}

    state.set_ampere_steps_on("a", 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": CHARGING, "c": IDLE}, dynamic_order=True)
    assert state.priority == ["b", "a", "c"]
    assert state.may_charge == {"b"}


def test_one_at_a_time_charger_that_may_not_charge_or_has_no_car_does_not_hold_the_others() -> None:
    """Also not when it seems to charge."""
    configured = chargers("a", "b", "c")
    group = group_of(configured)
    state = activated(configured, a=1, b=1)

    evaluate(state, configured, {"a": replace(CHARGING, car_connected=False), "b": CHARGING, "c": IDLE}, allowed=("a", "c"), dynamic_order=True)

    assert state.may_charge == {"c"}
    assert not state.must_deactivate(group, "a")
    assert state.must_deactivate(group, "b")


def test_with_dynamic_order_a_charger_whose_car_is_disconnected_is_deactivated() -> None:
    configured = chargers("a")
    state = activated(configured, a=1)

    evaluate(state, configured, {"a": ChargerReading(car_disconnected=True)}, one_at_a_time=False, dynamic_order=True)

    assert state.must_deactivate(group_of(configured, one_at_a_time=False, dynamic_order=True), "a")
    assert not state.must_deactivate(group_of(configured, one_at_a_time=False), "a")


def test_status_of_each_charger() -> None:
    """The override shows only for a charger that is deactivated."""
    configured = chargers("a", "b", "c", "d", "e", "f")
    group = group_of(configured, one_at_a_time=False)
    state = activated(configured, e=1)
    assert state.status(group)["a"].state is ChargerState.FIRST_DECISION
    state.set_ampere_steps_on("a", 4, NOW)
    evaluate(
        state,
        configured,
        {"a": CHARGING, "b": IDLE, "c": ChargerReading(car_connected=False), "d": IDLE, "e": IDLE, "f": IDLE},
        allowed=("c", "d"),
        overridden=("a", "e", "f"),
        one_at_a_time=False,
    )

    assert state.status(group) == {
        "a": ChargerStatus(ChargerState.CHARGING, 4, 9, False, True, True),
        "b": ChargerStatus(ChargerState.OUTSIDE_WINDOW, 0, None, False, False, True),
        "c": ChargerStatus(ChargerState.NO_CAR, 0, None, True, False, False),
        "d": ChargerStatus(ChargerState.DEACTIVATED, 0, None, False, False, True),
        "e": ChargerStatus(ChargerState.ACTIVATED, 1, 6, False, False, True),
        "f": ChargerStatus(ChargerState.OVERRIDE, 0, None, False, False, True),
    }


def test_charging_needs_an_activated_charger() -> None:
    """A charger is not charging once it is deactivated, nor before it is."""
    configured = chargers("a", "b")
    state = activated(configured, a=1)
    evaluate(state, configured, {"a": CHARGING, "b": CHARGING})

    state.set_ampere_steps_on("a", 0)

    assert not state.status(group_of(configured))["a"].charging
    assert not state.status(group_of(configured))["b"].charging


@pytest.mark.parametrize(("cloud_controlled", "one_at_a_time", "dynamic_order", "starting"), [(True, True, False, True), (False, False, True, False)])
def test_cloud_controlled_charger_holds_its_power_in_its_start_delay_until_it_charges(cloud_controlled: bool, one_at_a_time: bool, dynamic_order: bool, starting: bool) -> None:
    configured = [charger("a", cloud_controlled=cloud_controlled, start_delay_s=300)]
    group = group_of(configured, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    state = activated(configured, a=1)

    evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    assert ("a" in state.starting) is starting
    if starting:
        assert state.status(group)["a"] == ChargerStatus(ChargerState.STARTING, 1, 6, False, False, True, starting_until=NOW + timedelta(minutes=5))
    evaluate(state, configured, {"a": CHARGING}, now=NOW + 2 * WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    assert state.starting == {}
    evaluate(state, configured, {"a": IDLE}, now=NOW + 5 * WINDOW, one_at_a_time=one_at_a_time, dynamic_order=dynamic_order)
    assert state.starting == {}


def test_activating_needs_the_time() -> None:
    state = ChargingState.for_chargers(chargers("a"))

    with pytest.raises(ValueError, match="time"):
        state.set_ampere_steps_on("a", 1)


def test_power_per_ampere_is_measured_while_the_activated_charger_draws_power_and_kept_after() -> None:
    """Before it is measured, it is the power at minimum current divided by the minimum current."""
    configured = [charger("a", min_current_power_w=4140), charger("b", min_current_power_w=4140)]
    state = activated(configured, a=5)
    assert state.power_per_ampere_w(configured[0]) == pytest.approx(690)

    evaluate(state, configured, {"a": ChargerReading(actively_charging=True, charging_power_w=2300), "b": ChargerReading(actively_charging=True, charging_power_w=2000)})
    assert state.power_per_ampere_w(configured[0]) == pytest.approx(230)
    assert state.power_per_ampere_w(configured[1]) == pytest.approx(690)

    evaluate(state, configured, {"a": ChargerReading(actively_charging=True)})
    assert state.power_per_ampere_w(configured[0]) == pytest.approx(230)

    evaluate(state, configured, {"a": ChargerReading(charging_power_w=50)})
    assert state.power_per_ampere_w(configured[0]) == pytest.approx(230)
