"""True/false values from a boolean entity, the states of an entity, a template or a power sensor, and the charging power."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

from .config_model import Condition, ConditionType
from .measurement import power_w

_LOGGER = logging.getLogger(__name__)

ACTIVELY_CHARGING_ABOVE_W: Final = 100


def context_variables(hass: HomeAssistant, entity_id: str | None) -> dict[str, Any]:
    """Return the variables every template and action gets."""
    return {
        "entity_id": entity_id,
        "entity": None if entity_id is None else hass.states.get(entity_id),
    }


def evaluate_condition(hass: HomeAssistant, condition: Condition, entity_id: str | None) -> bool:
    """Return whether there is evidence that the condition is true right now.

    Everything else is false: an unavailable entity or sensor, and a template
    that fails or does not render a boolean.
    """
    return condition_evidence(hass, condition, entity_id) is True


def condition_evidence(hass: HomeAssistant, condition: Condition | None, entity_id: str | None) -> bool | None:
    """Return the value of the condition when there is evidence for it, else None.

    Evidence is an entity that is on or off, a state of an entity that has
    one, a template that renders a boolean, or a valid power. A condition
    that is not set gives none.
    """
    if condition is None:
        return None
    if condition.type is ConditionType.TEMPLATE:
        result = _render(hass, condition, entity_id)
        return result if isinstance(result, bool) else None
    state = hass.states.get(condition.value)
    if state is None:
        return None
    if condition.type is ConditionType.POWER_SENSOR:
        power = power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
        return None if power is None else power > ACTIVELY_CHARGING_ABOVE_W
    if condition.type is ConditionType.STATE:
        if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        return (state.state in condition.states) is condition.states_are_true
    return {STATE_ON: True, STATE_OFF: False}.get(state.state)


def charging_power_w(hass: HomeAssistant, condition: Condition | None, entity_id: str | None) -> float | None:
    """Return the charging power in W from a power sensor, or a template that gives a number, or None without a valid value."""
    if condition is None:
        return None
    if condition.type is ConditionType.POWER_SENSOR:
        state = hass.states.get(condition.value)
        return None if state is None else power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
    result = _render(hass, condition, entity_id)
    if isinstance(result, bool):
        return None
    return power_w(str(result), None)


def _render(hass: HomeAssistant, condition: Condition, entity_id: str | None) -> Any:
    try:
        return Template(condition.value, hass).async_render(context_variables(hass, entity_id))
    except TemplateError as err:
        _LOGGER.debug("Template %s gives no value: %s", condition.value, err)
        return None
