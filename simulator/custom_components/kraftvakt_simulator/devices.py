"""The simulated devices and the power board the HAN reads from."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN
from .model import ChargerState, DutyCycle

POWER_BOARD: HassKey[PowerBoard] = HassKey(DOMAIN)


class Observable:
    """Calls its listeners when it changes."""

    def __init__(self) -> None:
        """Start without listeners."""
        self._listeners: list[CALLBACK_TYPE] = []

    @callback
    def async_add_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Call `listener` on every change until the returned callback is called."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    @callback
    def _async_notify(self) -> None:
        for listener in list(self._listeners):
            listener()


class PowerBoard(Observable):
    """The power of every simulated consumer, summed by the HAN."""

    def __init__(self) -> None:
        """Start with no consumers."""
        super().__init__()
        self._power_w: dict[str, float] = {}

    @property
    def total_w(self) -> float:
        """Return the total power in W."""
        return sum(self._power_w.values())

    @callback
    def async_set_power(self, consumer_id: str, power_w: float) -> None:
        """Set the power of a consumer."""
        if self._power_w.get(consumer_id) != power_w:
            self._power_w[consumer_id] = power_w
            self._async_notify()

    @callback
    def async_remove(self, consumer_id: str) -> None:
        """Remove a consumer that is unloaded."""
        if self._power_w.pop(consumer_id, None) is not None:
            self._async_notify()


@callback
def async_get_power_board(hass: HomeAssistant) -> PowerBoard:
    """Return the power board, shared by every config entry of the simulator."""
    return hass.data.setdefault(POWER_BOARD, PowerBoard())


class SimulatedDevice(Observable, ABC):
    """A simulated device that reports its power to the power board."""

    def __init__(self, hass: HomeAssistant, consumer_id: str) -> None:
        """Report to the power board as `consumer_id`."""
        super().__init__()
        self.hass = hass
        self._consumer_id = consumer_id
        self._board = async_get_power_board(hass)

    @property
    @abstractmethod
    def power_w(self) -> float:
        """Return the power the device consumes now, in W."""

    @callback
    def async_start(self) -> None:
        """Report the starting power."""
        self._async_changed()

    @callback
    def async_stop(self) -> None:
        """Stop consuming power when the config entry is unloaded."""
        self._board.async_remove(self._consumer_id)

    @callback
    def _async_changed(self) -> None:
        self._board.async_set_power(self._consumer_id, self.power_w)
        self._async_notify()


class SimulatedHan(SimulatedDevice):
    """The background consumption of the house, not covered by other devices."""

    def __init__(
        self,
        hass: HomeAssistant,
        consumer_id: str,
        background_w: float,
        store_background: Callable[[float], None],
    ) -> None:
        """Start with `background_w`, and store every change with the callback."""
        super().__init__(hass, consumer_id)
        self.background_w = background_w
        self._store_background = store_background

    @property
    def power_w(self) -> float:
        """Return the background power in W."""
        return self.background_w

    @callback
    def async_set_background(self, background_w: float) -> None:
        """Change the background power."""
        self.background_w = background_w
        self._store_background(background_w)
        self._async_changed()


class PluggedInDevice(SimulatedDevice):
    """A device that can be unplugged, so it uses no power whatever its state."""

    def __init__(self, hass: HomeAssistant, consumer_id: str) -> None:
        """Start plugged in."""
        super().__init__(hass, consumer_id)
        self.unplugged = False

    @property
    def power_w(self) -> float:
        """Return the power in W: what the device demands, or 0 while unplugged."""
        return 0.0 if self.unplugged else self.demand_w

    @property
    @abstractmethod
    def demand_w(self) -> float:
        """Return the power the device would consume if plugged in, in W."""

    @callback
    def async_set_unplugged(self, unplugged: bool) -> None:
        """Unplug the device or plug it in again."""
        self.unplugged = unplugged
        self._async_changed()


class SimulatedHeater(PluggedInDevice):
    """A heating device with a duty cycle and an on/off switch in front of it.

    The cycle starts in its off part each time the switch is turned on, and
    runs on while the device is unplugged.
    """

    def __init__(self, hass: HomeAssistant, consumer_id: str, cycle: DutyCycle) -> None:
        """Start switched off."""
        super().__init__(hass, consumer_id)
        self.cycle = cycle
        self._switched_on_at: datetime | None = None
        self._cancel_timer: CALLBACK_TYPE | None = None

    @property
    def is_on(self) -> bool:
        """Return whether the switch is on."""
        return self._switched_on_at is not None

    @property
    def demand_w(self) -> float:
        """Return the power in W: the cycle's power while switched on."""
        if self._switched_on_at is None:
            return 0.0
        return self.cycle.power_at(self._elapsed())

    @callback
    def async_set_on(self, on: bool) -> None:
        """Turn the switch on or off. Turning on restarts the cycle."""
        if on == self.is_on:
            return
        self._async_cancel_timer()
        self._switched_on_at = dt_util.utcnow() if on else None
        if on:
            self._async_schedule_next_change()
        self._async_changed()

    @callback
    def async_stop(self) -> None:
        """Stop the cycle and consume nothing."""
        self._async_cancel_timer()
        super().async_stop()

    def _elapsed(self) -> timedelta:
        assert self._switched_on_at is not None
        return dt_util.utcnow() - self._switched_on_at

    @callback
    def _async_schedule_next_change(self) -> None:
        delay = self.cycle.time_to_next_change(self._elapsed())
        if delay is not None:
            self._cancel_timer = async_track_point_in_utc_time(
                self.hass, self._async_cycle_changed, dt_util.utcnow() + delay
            )

    @callback
    def _async_cycle_changed(self, _now: datetime) -> None:
        self._cancel_timer = None
        self._async_schedule_next_change()
        self._async_changed()

    @callback
    def _async_cancel_timer(self) -> None:
        if self._cancel_timer is not None:
            self._cancel_timer()
            self._cancel_timer = None


class SimulatedCharger(PluggedInDevice):
    """A 400 V three-phase EV charger with a simulated car."""

    def __init__(
        self,
        hass: HomeAssistant,
        consumer_id: str,
        min_current_a: int,
        max_current_a: int,
    ) -> None:
        """Start with charging not allowed, no car and the minimum current."""
        super().__init__(hass, consumer_id)
        self.min_current_a = min_current_a
        self.max_current_a = max_current_a
        self.state = ChargerState(
            charging_allowed=False,
            current_a=min_current_a,
            car_connected=False,
            car_fully_charged=False,
        )

    @property
    def demand_w(self) -> float:
        """Return the charging power in W."""
        return self.state.power_w

    @callback
    def async_set_charging_allowed(self, allowed: bool) -> None:
        """Allow or stop charging."""
        self._async_update(charging_allowed=allowed)

    @callback
    def async_set_car_connected(self, connected: bool) -> None:
        """Connect or disconnect the simulated car."""
        self._async_update(car_connected=connected)

    @callback
    def async_set_car_fully_charged(self, fully_charged: bool) -> None:
        """Let the simulated car be fully charged, so it draws no power."""
        self._async_update(car_fully_charged=fully_charged)

    @callback
    def async_set_current(self, current_a: float) -> None:
        """Set the charging current, kept between the minimum and maximum."""
        clamped = min(max(current_a, self.min_current_a), self.max_current_a)
        self._async_update(current_a=clamped)

    @callback
    def _async_update(self, **changes: bool | float) -> None:
        self.state = replace(self.state, **changes)
        self._async_changed()
