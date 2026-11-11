"""Unit tests for the rules for the EV chargers."""

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.kraftvakt.config_model import Charger, ChargingWindow
from custom_components.kraftvakt.regulation.charging import (
    ChargerReading,
    ChargerStatus,
    ChargingState,
    actively_charging,
    allowed_to_charge,
    charging_current,
    charging_window_started,
    fictive_appliance_count,
    in_charging_window,
    override_expired,
    window_overridden,
)

OSLO = ZoneInfo("Europe/Oslo")
NIGHT = ChargingWindow(time(22, 0), time(6, 0))
DAY = ChargingWindow(time(9, 0), time(15, 30))
NOW = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
WINDOW = timedelta(minutes=1)
CHARGING = ChargerReading(charge_power_w=7000)
IDLE = ChargerReading(charge_power_w=0)


def charger(
    charger_id: str = "c", min_a: int = 6, max_a: int = 16, **settings
) -> Charger:
    return Charger(charger_id, min_current_a=min_a, max_current_a=max_a, **settings)


def oslo(hour: int, minute: int = 0, day: int = 7) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=OSLO)


def test_one_fictive_appliance_per_ampere() -> None:
    """6 A to 16 A gives 11 fictive appliances."""
    assert fictive_appliance_count(charger(min_a=6, max_a=16)) == 11
    assert fictive_appliance_count(charger(min_a=6, max_a=6)) == 1


def test_current_follows_the_fictive_appliances_that_are_on() -> None:
    """Four on gives 9 A, and a deactivated charger gets the minimum."""
    assert charging_current(charger(), 4) == 9
    assert charging_current(charger(), 11) == 16
    assert charging_current(charger(), 0) == 6


@pytest.mark.parametrize(
    ("reading", "expected"),
    [
        (ChargerReading(charge_power_w=100), False),
        (ChargerReading(charge_power_w=110), True),
        (ChargerReading(charge_power_w=0), False),
        (ChargerReading(charge_power_w=None), True),
    ],
)
def test_actively_charging_above_100_watt_or_without_a_valid_value(
    reading: ChargerReading, expected: bool
) -> None:
    assert actively_charging(reading) is expected


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


def test_charging_window_start_is_found_in_the_time_zone() -> None:
    """The window is given in the time zone of Home Assistant."""
    assert charging_window_started(NIGHT, oslo(21, 0), oslo(22, 0), OSLO)
    assert not charging_window_started(NIGHT, oslo(22, 0), oslo(23, 0), OSLO)
    assert not charging_window_started(NIGHT, oslo(23, 0), oslo(21, 59, day=8), OSLO)
    assert charging_window_started(NIGHT, oslo(23, 0), oslo(22, 0, day=8), OSLO)
    assert charging_window_started(DAY, oslo(10, 0), oslo(10, 0, day=9), OSLO)
    assert not charging_window_started(NIGHT, oslo(21, 0), oslo(21, 0), UTC)


def test_override_ends_when_the_next_window_has_started() -> None:
    """Counted from when the switch was switched on."""
    night = charger(charging_window=NIGHT)
    switched_on = ChargerReading(window_override=True, override_switched_on_at=oslo(12))

    assert not override_expired(night, switched_on, oslo(8), oslo(21, 59), OSLO)
    assert override_expired(night, switched_on, oslo(8), oslo(22, 0), OSLO)


def test_override_counts_from_the_switch_also_over_a_later_start() -> None:
    """A window that started while the regulation was stopped counts."""
    night = charger(charging_window=NIGHT)
    long_ago = ChargerReading(
        window_override=True, override_switched_on_at=oslo(8, day=5)
    )

    assert override_expired(night, long_ago, oslo(12), oslo(12, 10), OSLO)


def test_override_counts_from_the_start_when_switched_on_is_unknown() -> None:
    """The start of the regulation counts when the switch time is not known."""
    night = charger(charging_window=NIGHT)
    unknown = ChargerReading(window_override=True)

    assert not override_expired(night, unknown, oslo(12), oslo(21, 0), OSLO)
    assert override_expired(night, unknown, oslo(12), oslo(22, 1), OSLO)


def test_override_without_window_or_switched_off_never_ends() -> None:
    """An override has no effect without a charging window."""
    switched_on = ChargerReading(window_override=True, override_switched_on_at=oslo(1))
    switched_off = ChargerReading(
        window_override=False, override_switched_on_at=oslo(1)
    )

    assert not override_expired(charger(), switched_on, oslo(1), oslo(23), OSLO)
    assert not override_expired(
        charger(charging_window=NIGHT), switched_off, oslo(1), oslo(23), OSLO
    )


def test_allowed_to_charge() -> None:
    night = charger(charging_window=NIGHT)
    excluded = ChargerReading(excluded=True)

    assert allowed_to_charge(charger(), IDLE, False, time(12))
    assert not allowed_to_charge(charger(), excluded, True, time(12))
    assert allowed_to_charge(night, IDLE, False, time(23))
    assert not allowed_to_charge(night, IDLE, False, time(12))
    assert allowed_to_charge(night, IDLE, True, time(12))
    assert not allowed_to_charge(night, excluded, True, time(23))


def test_window_overridden_only_outside_the_window() -> None:
    night = charger(charging_window=NIGHT)

    assert window_overridden(night, IDLE, True, time(12))
    assert not window_overridden(night, IDLE, True, time(23))
    assert not window_overridden(night, IDLE, False, time(12))
    assert not window_overridden(charger(), IDLE, True, time(12))
    assert not window_overridden(night, ChargerReading(excluded=True), True, time(12))


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
    return state.evaluate(
        configured,
        readings,
        [c.id for c in configured] if allowed is None else allowed,
        now,
        WINDOW,
        one_at_a_time,
        overridden,
    )


def test_priority_starts_as_configured() -> None:
    state = ChargingState.for_chargers(chargers("a", "b"))

    assert state.priority == ["a", "b"]
    assert state.fictive_on == {"a": 0, "b": 0}
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
    """The first fictive appliance must have been on two windows."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_fictive_on("a", 1, NOW)

    assert evaluate(state, configured, {"a": IDLE}, now=NOW + WINDOW) == []
    assert evaluate(state, configured, {"a": CHARGING}, now=NOW + 2 * WINDOW) == []
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 2 * WINDOW) == ["a"]
    assert evaluate(state, configured, {"a": IDLE}, now=NOW + 3 * WINDOW) == []
    assert state.bypassed == {"a"}


def test_charger_without_valid_charging_power_is_bypassed_only_without_car() -> None:
    """An invalid charging power counts as charging."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_fictive_on("a", 1, NOW)
    later = NOW + 5 * WINDOW

    assert evaluate(state, configured, {"a": ChargerReading()}, now=later) == []
    assert evaluate(
        state, configured, {"a": ChargerReading(car_connected=False)}, now=later
    ) == ["a"]


def test_charger_that_did_not_charge_rests_also_when_deactivated() -> None:
    """It may be tried again after 15 minutes."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_fictive_on("a", 1, NOW)
    bypassed_at = NOW + 2 * WINDOW
    evaluate(state, configured, {"a": IDLE}, now=bypassed_at)
    state.set_fictive_on("a", 0)

    evaluate(state, configured, {"a": IDLE}, now=bypassed_at + timedelta(minutes=14))
    assert state.bypassed == {"a"}
    evaluate(state, configured, {"a": IDLE}, now=bypassed_at + timedelta(minutes=15))
    assert state.bypassed == set()


def test_rest_ends_when_the_charger_charges_or_the_car_is_disconnected() -> None:
    """The next rest is the first again."""
    configured = chargers("a")
    state = ChargingState.for_chargers(configured)
    state.set_fictive_on("a", 1, NOW)
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


def test_priority_is_corrected_when_a_charger_has_all_fictive_appliances_on() -> None:
    """Bypassed chargers stay at the back."""
    configured = [charger("a"), charger("b"), charger("c", min_a=6, max_a=7)]
    state = ChargingState.for_chargers(configured)
    no_car = ChargerReading(car_connected=False)
    evaluate(state, configured, {"a": no_car, "b": no_car, "c": IDLE})
    assert state.priority == ["c", "a", "b"]
    evaluate(state, configured, {"a": IDLE, "b": no_car, "c": IDLE})
    assert state.priority == ["c", "a", "b"]

    state.set_fictive_on("c", 2, NOW)
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
    state.set_fictive_on("c", 3, NOW)

    evaluate(state, configured, {"a": IDLE, "b": CHARGING, "c": CHARGING})
    assert state.may_charge == {"c"}

    state.set_fictive_on("c", 0)
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
        {"a": ChargerReading(charge_power_w=7000, car_connected=False), "b": IDLE},
    )

    assert state.may_charge == {"b"}


def test_status_of_each_charger() -> None:
    """Whether it is excluded and «car connected» are known after the first decision."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)
    assert state.status(configured)["a"].excluded is None
    assert state.status(configured)["a"].car_connected is None
    state.set_fictive_on("a", 4, NOW)
    evaluate(
        state,
        configured,
        {
            "a": ChargerReading(charge_power_w=7000, car_connected=True),
            "b": ChargerReading(charge_power_w=0, excluded=True),
        },
        allowed=("a",),
        overridden=("a",),
    )

    assert state.status(configured) == {
        "a": ChargerStatus(
            4,
            9,
            allowed=True,
            bypassed=False,
            waiting=False,
            excluded=False,
            charging=True,
            window_overridden=True,
            car_connected=True,
        ),
        "b": ChargerStatus(
            0, None, allowed=False, bypassed=False, waiting=False, excluded=True
        ),
    }


def test_charging_needs_an_activated_charger() -> None:
    """A charger is not charging once it is deactivated, nor before it is."""
    configured = chargers("a", "b")
    state = ChargingState.for_chargers(configured)
    state.set_fictive_on("a", 1, NOW)
    evaluate(state, configured, {"a": CHARGING, "b": CHARGING})

    state.set_fictive_on("a", 0)

    assert not state.status(configured)["a"].charging
    assert not state.status(configured)["b"].charging


def test_activating_needs_the_time() -> None:
    state = ChargingState.for_chargers(chargers("a"))

    with pytest.raises(ValueError, match="time"):
        state.set_fictive_on("a", 1)
