"""Reads what a decision is based on from Home Assistant and the user's switches."""

from __future__ import annotations

from collections.abc import Sequence

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .conditions import ACTIVELY_CHARGING_ABOVE_W, condition_evidence, evaluate_condition, power_value_w
from .config_model import Charger
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


def chargers_without_car(hass: HomeAssistant, settings: Settings) -> frozenset[str]:
    """Return the chargers with evidence that no car is connected."""
    return frozenset(charger.id for charger in settings.config.chargers if condition_evidence(hass, charger.car_connected, charger.entity_id) is False)


def _charger_reading(hass: HomeAssistant, settings: Settings, charger: Charger) -> ChargerReading:
    switches = settings.charger_switches(charger.id)
    car_connected = condition_evidence(hass, charger.car_connected, charger.entity_id)
    power_w = power_value_w(hass, charger.charging_power, charger.entity_id)
    charging = [
        *([] if charger.actively_charging is None else [condition_evidence(hass, charger.actively_charging, charger.entity_id)]),
        *([] if charger.charging_power is None else [None if power_w is None else power_w > ACTIVELY_CHARGING_ABOVE_W]),
    ]
    return ChargerReading(
        actively_charging=True in charging,
        charging_power_w=power_w,
        car_connected=car_connected is True,
        car_disconnected=car_connected is False,
        charging_stopped=bool(charging) and all(evidence is False for evidence in charging),
        excluded=switches.excluded,
        window_override=switches.window_override,
        override_armed=settings.override_armed(charger.id),
        finish_after_window=charger.finish_after_window,
        fault=charger.deactivate_on_fault and charger.fault_flag is not None and evaluate_condition(hass, charger.fault_flag, charger.entity_id),
    )
