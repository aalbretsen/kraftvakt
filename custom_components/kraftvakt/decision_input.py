"""Reads what a decision is based on from Home Assistant and the user's switches."""

from __future__ import annotations

from collections.abc import Sequence

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .conditions import condition_evidence, evaluate_condition
from .config_model import Charger, Condition
from .measurement import WindowAverages
from .regulation.charging import ChargerReading
from .regulation.model import DecisionInput
from .settings import Settings


def read_decision_input(
    hass: HomeAssistant,
    settings: Settings,
    averages: WindowAverages,
    windows_since_decision: Sequence[WindowAverages],
    power_sensor_lost: bool,
) -> DecisionInput:
    config = settings.config
    return DecisionInput(
        now=averages.end,
        regulation_average_w=averages.regulation_average_w,
        tariff_average_w=averages.tariff_average_w,
        regulation_averages_w=[window.regulation_average_w for window in windows_since_decision if window.regulation_average_w is not None],
        power_sensor_valid=averages.sensor_valid,
        power_sensor_lost=power_sensor_lost,
        variant_conditions={variant.id: evaluate_condition(hass, variant.condition, appliance.entity_id) for appliance in config.appliances for variant in appliance.variants},
        chargers={charger.id: _charger_reading(hass, settings, charger) for charger in config.chargers},
        excluded_appliances=excluded_appliances(settings),
        time_zone=dt_util.get_default_time_zone(),
    )


def excluded_appliances(settings: Settings) -> frozenset[str]:
    return frozenset(appliance.id for appliance in settings.config.appliances if settings.appliance_switches(appliance.id).excluded)


def excluded_chargers(settings: Settings) -> frozenset[str]:
    return frozenset(charger.id for charger in settings.config.chargers if settings.charger_switches(charger.id).excluded)


def _charger_reading(hass: HomeAssistant, settings: Settings, charger: Charger) -> ChargerReading:
    switches = settings.charger_switches(charger.id)
    car_connected = _evidence(hass, charger.car_connected, charger.entity_id)
    actively_charging = _evidence(hass, charger.actively_charging, charger.entity_id)
    return ChargerReading(
        actively_charging=actively_charging is True,
        car_connected=None if charger.car_connected is None else car_connected is True,
        car_disconnected=car_connected is False,
        charging_stopped=actively_charging is False,
        excluded=switches.excluded,
        window_override=switches.window_override,
        override_armed=settings.override_armed(charger.id),
        finish_after_window=charger.finish_after_window,
    )


def _evidence(hass: HomeAssistant, condition: Condition | None, entity_id: str | None) -> bool | None:
    if condition is None:
        return None
    return condition_evidence(hass, condition, entity_id)
