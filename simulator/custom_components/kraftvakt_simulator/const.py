"""Constants for the Kraftvakt simulator."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

DOMAIN: Final = "kraftvakt_simulator"


class DeviceKind(StrEnum):
    """The kinds of simulated devices, one config entry each."""

    HAN = "han"
    HEATER = "heater"
    THERMOSTAT = "thermostat"
    CHARGER = "charger"


class HeaterType(StrEnum):
    """Heating device types. They behave the same, but have their own icon."""

    HEATING_CABLE = "heating_cable"
    WATER_HEATER = "water_heater"
    PANEL_HEATER = "panel_heater"


CONF_KIND: Final = "kind"
CONF_BACKGROUND_W: Final = "background_w"
CONF_HEATER_TYPE: Final = "heater_type"
CONF_POWER_W: Final = "power_w"
CONF_DUTY_CYCLE_PCT: Final = "duty_cycle_pct"
CONF_PERIOD_MIN: Final = "period_min"
CONF_MIN_CURRENT_A: Final = "min_current_a"
CONF_MAX_CURRENT_A: Final = "max_current_a"

MAX_BACKGROUND_W: Final = 50_000
MAX_HEATER_POWER_W: Final = 20_000
MAX_PERIOD_MIN: Final = 24 * 60
MAX_CURRENT_A: Final = 63
DEFAULT_TARGET_TEMPERATURE: Final = 21.0
MIN_TARGET_TEMPERATURE: Final = 5.0
MAX_TARGET_TEMPERATURE: Final = 30.0
