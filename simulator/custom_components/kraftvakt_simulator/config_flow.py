"""Config flow for the Kraftvakt simulator: one config entry per device."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_NAME,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfPower,
)
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_BACKGROUND_W,
    CONF_DUTY_CYCLE_PCT,
    CONF_HEATER_TYPE,
    CONF_KIND,
    CONF_MAX_CURRENT_A,
    CONF_MIN_CURRENT_A,
    CONF_PERIOD_MIN,
    CONF_POWER_W,
    DOMAIN,
    MAX_BACKGROUND_W,
    MAX_CURRENT_A,
    MAX_HEATER_POWER_W,
    MAX_PERIOD_MIN,
    DeviceKind,
    HeaterType,
)


def whole_number(
    minimum: int, maximum: int, unit: str | None = None, step: int = 1
) -> vol.All:
    """Return a field for a whole number between `minimum` and `maximum`."""
    selector = NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )
    return vol.All(selector, vol.Coerce(int))


DUTY_CYCLE_FIELDS = {
    vol.Required(CONF_POWER_W, default=1000): whole_number(
        1, MAX_HEATER_POWER_W, UnitOfPower.WATT
    ),
    vol.Required(CONF_DUTY_CYCLE_PCT, default=50): whole_number(0, 100, PERCENTAGE),
    vol.Required(CONF_PERIOD_MIN, default=60): whole_number(1, MAX_PERIOD_MIN, "min"),
}

SCHEMAS = {
    DeviceKind.HAN: vol.Schema(
        {
            vol.Required(CONF_NAME, default="HAN"): TextSelector(),
            vol.Required(CONF_BACKGROUND_W, default=3500): whole_number(
                0, MAX_BACKGROUND_W, UnitOfPower.WATT, step=100
            ),
        }
    ),
    DeviceKind.HEATER: vol.Schema(
        {
            vol.Required(CONF_NAME): TextSelector(),
            vol.Required(CONF_HEATER_TYPE): SelectSelector(
                SelectSelectorConfig(
                    options=list(HeaterType),
                    translation_key=CONF_HEATER_TYPE,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            **DUTY_CYCLE_FIELDS,
        }
    ),
    DeviceKind.THERMOSTAT: vol.Schema(
        {vol.Required(CONF_NAME): TextSelector(), **DUTY_CYCLE_FIELDS}
    ),
    DeviceKind.CHARGER: vol.Schema(
        {
            vol.Required(CONF_NAME): TextSelector(),
            vol.Required(CONF_MIN_CURRENT_A, default=6): whole_number(
                1, MAX_CURRENT_A, UnitOfElectricCurrent.AMPERE
            ),
            vol.Required(CONF_MAX_CURRENT_A, default=16): whole_number(
                1, MAX_CURRENT_A, UnitOfElectricCurrent.AMPERE
            ),
        }
    ),
}


def validate(kind: DeviceKind, user_input: dict[str, Any]) -> dict[str, str]:
    """Return the errors per field in the settings of a device."""
    if (
        kind is DeviceKind.CHARGER
        and user_input[CONF_MIN_CURRENT_A] > user_input[CONF_MAX_CURRENT_A]
    ):
        return {CONF_MAX_CURRENT_A: "max_below_min"}
    return {}


class SimulatorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a simulated device of any kind, or change its settings."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which kind of device to add."""
        return self.async_show_menu(step_id="user", menu_options=list(DeviceKind))

    async def async_step_han(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the settings of the HAN. There can only be one."""
        if self.source != SOURCE_RECONFIGURE and any(
            entry.data[CONF_KIND] == DeviceKind.HAN
            for entry in self._async_current_entries(include_ignore=False)
        ):
            return self.async_abort(reason="single_han")
        return await self._async_device_step(DeviceKind.HAN, user_input)

    async def async_step_heater(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the settings of a heating device."""
        return await self._async_device_step(DeviceKind.HEATER, user_input)

    async def async_step_thermostat(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the settings of a thermostat."""
        return await self._async_device_step(DeviceKind.THERMOSTAT, user_input)

    async def async_step_charger(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the settings of an EV charger."""
        return await self._async_device_step(DeviceKind.CHARGER, user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the settings of a device, in the form of its kind."""
        kind = DeviceKind(self._get_reconfigure_entry().data[CONF_KIND])
        return await self._async_device_step(kind, None)

    async def _async_device_step(
        self, kind: DeviceKind, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = validate(kind, user_input)
            if not errors:
                return self._async_finish(kind, user_input)
        schema = SCHEMAS[kind]
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(schema, user_input)
        elif self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            schema = self.add_suggested_values_to_schema(
                schema, {CONF_NAME: entry.title, **entry.data}
            )
        return self.async_show_form(step_id=kind, data_schema=schema, errors=errors)

    def _async_finish(
        self, kind: DeviceKind, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        settings = {key: value for key, value in user_input.items() if key != CONF_NAME}
        data = {CONF_KIND: kind, **settings}
        title = user_input[CONF_NAME]
        if self.source == SOURCE_RECONFIGURE:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(), title=title, data=data
            )
        return self.async_create_entry(title=title, data=data)
