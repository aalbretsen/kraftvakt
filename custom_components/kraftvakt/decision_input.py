"""Reads what a decision is based on from Home Assistant and the user's switches."""

from __future__ import annotations

from collections.abc import Sequence

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .conditions import charging_evidence, condition_evidence, evaluate_condition, group_variables, item_variables, power_value_w
from .config_model import Charger
from .measurement import WindowAverages
from .regulation.charging import ChargerReading
from .regulation.model import DecisionInput
from .regulation.penalty import RegulationAverage
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
        window_start=averages.start,
        regulation_average_w=averages.regulation_average_w,
        tariff_average_w=averages.tariff_average_w,
        regulation_averages=[
            RegulationAverage(window.regulation_average_w, window.end - window.start) for window in windows_since_decision if window.regulation_average_w is not None
        ],
        power_sensor_valid=averages.sensor_valid,
        power_sensor_lost=power_sensor_lost,
        variant_conditions={
            variant.id: evaluate_condition(hass, variant.condition, item_variables(hass, appliance)) for appliance in config.appliances for variant in appliance.variants
        },
        one_at_a_time_conditions={group.id: evaluate_condition(hass, condition, group_variables(config)) for group in config.charger_groups for _, condition in group.conditions()},
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
    return frozenset(charger.id for charger in settings.config.chargers if condition_evidence(hass, charger.car_connected, item_variables(hass, charger)) is False)


def _charger_reading(hass: HomeAssistant, settings: Settings, charger: Charger) -> ChargerReading:
    switches = settings.charger_switches(charger.id)
    variables = item_variables(hass, charger)
    car_connected = condition_evidence(hass, charger.car_connected, variables)
    power_w = power_value_w(hass, charger.charging_power, variables)
    charging = [
        *([] if charger.actively_charging is None else [condition_evidence(hass, charger.actively_charging, variables)]),
        *([] if charger.charging_power is None else [charging_evidence(power_w)]),
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
        charge_until_disconnected=charger.charge_until_disconnected,
        charged_in_window=settings.charged_in_window(charger.id),
        fault=charger.deactivate_on_fault and charger.fault_flag is not None and evaluate_condition(hass, charger.fault_flag, variables),
    )
