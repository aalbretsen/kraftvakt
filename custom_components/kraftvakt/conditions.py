"""True/false values from a boolean entity or a template (GEN-009, GEN-010)."""

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
    """Return the variables every template and action gets (GEN-013, T14).

    `entity` is the state object of the entity as it is now, or None when the
    entity is not in the state machine.
    """
    return {
        "entity_id": entity_id,
        "entity": None if entity_id is None else hass.states.get(entity_id),
    }


def evaluate_condition(
    hass: HomeAssistant, condition: Condition, entity_id: str | None
) -> bool:
    """Return whether the condition is true right now (GEN-009).

    An entity is true only when it is on, and a template only when it renders
    the boolean value true. Everything else, also an unavailable entity and a
    template that fails, is false (GEN-010). `entity_id` is the entity of the
    appliance or charger the condition belongs to (GEN-013).
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
