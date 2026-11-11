"""True/false values from a boolean entity, a template or a power sensor."""

from __future__ import annotations

import logging
from typing import Any, Final

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, STATE_OFF, STATE_ON
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


def evaluate_condition(
    hass: HomeAssistant, condition: Condition, entity_id: str | None
) -> bool:
    """Return whether the condition is true right now.

    Only an entity that is on and a template that renders the boolean true are
    true. Everything else is false, also an unavailable entity and a template
    that fails.
    """
    return _evidence(hass, condition, entity_id) is True


def evaluate_actively_charging(
    hass: HomeAssistant, condition: Condition, entity_id: str | None
) -> bool:
    """Return whether a charger counts as actively charging right now.

    Only evidence that it does not charge counts as not charging: an entity
    that is off, a template that renders the boolean false, or a valid power of
    at most 100 W. An unavailable entity or sensor and a template that fails
    count as charging, so a charger that may charge is never taken for idle.
    """
    return _evidence(hass, condition, entity_id) is not False


def _evidence(
    hass: HomeAssistant, condition: Condition, entity_id: str | None
) -> bool | None:
    """Return what the condition shows, or None when it shows nothing valid."""
    if condition.type is ConditionType.TEMPLATE:
        try:
            result = Template(condition.value, hass).async_render(
                context_variables(hass, entity_id)
            )
        except TemplateError as err:
            _LOGGER.debug("Template %s gives no value: %s", condition.value, err)
            return None
        return result if isinstance(result, bool) else None
    state = hass.states.get(condition.value)
    if state is None:
        return None
    if condition.type is ConditionType.POWER_SENSOR:
        power = power_w(state.state, state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
        return None if power is None else power > ACTIVELY_CHARGING_ABOVE_W
    return {STATE_ON: True, STATE_OFF: False}.get(state.state)
