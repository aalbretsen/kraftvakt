"""True/false values from a boolean entity or a template."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template

from .config_model import Condition, ConditionType

_LOGGER = logging.getLogger(__name__)


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
    if condition.type is ConditionType.ENTITY:
        state = hass.states.get(condition.value)
        return state is not None and state.state == STATE_ON
    try:
        result = Template(condition.value, hass).async_render(
            context_variables(hass, entity_id)
        )
    except TemplateError as err:
        _LOGGER.debug("Template %s counts as false: %s", condition.value, err)
        return False
    return result is True
