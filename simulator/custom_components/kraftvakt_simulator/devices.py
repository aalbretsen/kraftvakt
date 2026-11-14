"""The simulated devices and the power board the HAN reads from."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.climate import HVACMode
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util
from homeassistant.util.hass_dict import HassKey

from .const import (
    CONF_BACKGROUND_W,
    CONF_DUTY_CYCLE_PCT,
    CONF_PERIOD_MIN,
    CONF_POWER_W,
    CONF_ROOM_TEMPERATURE,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
)
from .model import HEATING_MODES, ChargerState, DutyCycle, thermostat_heats

POWER_BOARD: HassKey[PowerBoard] = HassKey(DOMAIN)

type StoreSetting = Callable[[str, float], None]


class Observable:
    """Calls its listeners when it changes."""

    def __init__(self) -> None:
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
        super().__init__()
        self._power_w: dict[str, float] = {}

    @property
    def total_w(self) -> float:
        return sum(self._power_w.values())

    @callback
    def async_set_power(self, consumer_id: str, power_w: float) -> None:
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
        store_setting: StoreSetting,
    ) -> None:
        """Start with `background_w`, and store every change with the callback."""
        super().__init__(hass, consumer_id)
        self.background_w = background_w
        self._store_setting = store_setting

    @property
    def power_w(self) -> float:
        return self.background_w

    @callback
    def async_set_background(self, background_w: float) -> None:
        self.background_w = background_w
        self._store_setting(CONF_BACKGROUND_W, background_w)
        self._async_changed()


class PluggedInDevice(SimulatedDevice):
    """A device that can be unplugged, so it uses no power whatever its state."""

    def __init__(self, hass: HomeAssistant, consumer_id: str) -> None:
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

    The cycle starts in its on part each time the switch is turned on or the
    cycle is changed, and runs on while the device is unplugged.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        consumer_id: str,
        cycle: DutyCycle,
        store_setting: StoreSetting,
    ) -> None:
        """Start switched off, and store every change of the cycle with the callback."""
        super().__init__(hass, consumer_id)
        self.cycle = cycle
        self._store_setting = store_setting
        self._switched_on_at: datetime | None = None
        self._cancel_timer: CALLBACK_TYPE | None = None

    @property
    def is_on(self) -> bool:
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
        if on:
            self._async_restart_cycle()
        else:
            self._async_cancel_timer()
            self._switched_on_at = None
        self._async_changed()

    @callback
    def async_set_power(self, power_w: float) -> None:
        """Change the power while heating, in whole watts."""
        self._async_set_cycle(replace(self.cycle, power_w=int(power_w)), CONF_POWER_W, int(power_w))

    @callback
    def async_set_duty_cycle(self, duty_cycle_pct: float) -> None:
        """Change the share of the period the device heats."""
        self._async_set_cycle(
            replace(self.cycle, duty_cycle_pct=int(duty_cycle_pct)),
            CONF_DUTY_CYCLE_PCT,
            int(duty_cycle_pct),
        )

    @callback
    def async_set_period(self, period_min: float) -> None:
        """Change the length of one cycle, in whole minutes."""
        self._async_set_cycle(
            replace(self.cycle, period=timedelta(minutes=int(period_min))),
            CONF_PERIOD_MIN,
            int(period_min),
        )

    @callback
    def async_stop(self) -> None:
        """Stop the cycle and consume nothing."""
        self._async_cancel_timer()
        super().async_stop()

    @callback
    def _async_set_cycle(self, cycle: DutyCycle, key: str, value: float) -> None:
        if cycle == self.cycle:
            return
        self.cycle = cycle
        self._store_setting(key, value)
        if self.is_on:
            self._async_restart_cycle()
        self._async_changed()

    @callback
    def _async_restart_cycle(self) -> None:
        self._async_cancel_timer()
        self._switched_on_at = dt_util.utcnow()
        self._async_schedule_next_change()

    def _elapsed(self) -> timedelta:
        assert self._switched_on_at is not None
        return dt_util.utcnow() - self._switched_on_at

    @callback
    def _async_schedule_next_change(self) -> None:
        delay = self.cycle.time_to_next_change(self._elapsed())
        if delay is not None:
            self._cancel_timer = async_track_point_in_utc_time(self.hass, self._async_cycle_changed, dt_util.utcnow() + delay)

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


class SimulatedThermostat(SimulatedHeater):
    """A heating device controlled by a thermostat with a chosen set of HVAC modes.

    It runs the duty cycle in a heating mode while the target temperature is
    above the room temperature. The cycle starts again each time it starts
    heating. Turning it on returns it to the last heating mode it was in, the
    first supported heating mode at first.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        consumer_id: str,
        cycle: DutyCycle,
        store_setting: StoreSetting,
        hvac_modes: list[HVACMode],
        room_temperature: float,
    ) -> None:
        """Start in off, or its first mode without off, at the default target."""
        super().__init__(hass, consumer_id, cycle, store_setting)
        self.hvac_modes = hvac_modes
        self.room_temperature = room_temperature
        self.hvac_mode = HVACMode.OFF if HVACMode.OFF in hvac_modes else hvac_modes[0]
        self.target_temperature = DEFAULT_TARGET_TEMPERATURE
        self._last_heating_mode = next(mode for mode in hvac_modes if mode in HEATING_MODES)

    @callback
    def async_start(self) -> None:
        """Start heating if the first mode heats, and report the power."""
        self._async_follow_thermostat()
        super().async_start()

    @callback
    def async_set_hvac_mode(self, mode: HVACMode) -> None:
        if mode in HEATING_MODES:
            self._last_heating_mode = mode
        self.hvac_mode = mode
        self._async_follow_thermostat()

    @callback
    def async_turn_on(self) -> None:
        """Return to the last heating mode."""
        self.async_set_hvac_mode(self._last_heating_mode)

    @callback
    def async_set_target_temperature(self, temperature: float) -> None:
        self.target_temperature = temperature
        self._async_follow_thermostat()

    @callback
    def async_set_room_temperature(self, temperature: float) -> None:
        self.room_temperature = temperature
        self._store_setting(CONF_ROOM_TEMPERATURE, temperature)
        self._async_follow_thermostat()

    @callback
    def _async_follow_thermostat(self) -> None:
        heats = thermostat_heats(self.hvac_mode, self.target_temperature, self.room_temperature)
        if heats != self.is_on:
            self.async_set_on(heats)
        else:
            self._async_notify()


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
        return self.state.power_w

    @callback
    def async_set_charging_allowed(self, allowed: bool) -> None:
        self._async_update(charging_allowed=allowed)

    @callback
    def async_set_car_connected(self, connected: bool) -> None:
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
    def _async_update(self, **changes: Any) -> None:
        self.state = replace(self.state, **changes)
        self._async_changed()
