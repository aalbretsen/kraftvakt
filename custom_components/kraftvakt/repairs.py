"""Repair issues for problems the user fixes in Kraftvakt's configuration.

Only problems in the configuration are reported: an entity that is merely
unavailable, for example while a cloud service is down, is not.
"""

from __future__ import annotations

from typing import Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .config_model import KraftvaktConfig
from .const import DOMAIN

REGULATION_NOT_STARTED: Final = "regulation_not_started"
MISSING_ENTITY: Final = "missing_entity"


@callback
def async_report_not_started(hass: HomeAssistant) -> None:
    """Report that the regulation could not start for an incomplete configuration."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        REGULATION_NOT_STARTED,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key=REGULATION_NOT_STARTED,
    )


@callback
def async_clear_not_started(hass: HomeAssistant) -> None:
    """Remove the report that the regulation could not start."""
    ir.async_delete_issue(hass, DOMAIN, REGULATION_NOT_STARTED)


@callback
def async_check_entities(hass: HomeAssistant, config: KraftvaktConfig) -> None:
    """Report each entity of an appliance or charger that no longer exists.

    The reports of entities that exist again, or are no longer used, are
    removed.
    """
    registry = er.async_get(hass)
    missing = {
        entity_id
        for _, item in config.items()
        if (entity_id := item.entity_id) is not None
        and hass.states.get(entity_id) is None
        and registry.async_get(entity_id) is None
    }
    prefix = f"{MISSING_ENTITY}_"
    for domain, issue_id in list(ir.async_get(hass).issues):
        if (
            domain == DOMAIN
            and issue_id.startswith(prefix)
            and issue_id.removeprefix(prefix) not in missing
        ):
            ir.async_delete_issue(hass, DOMAIN, issue_id)
    for entity_id in missing:
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"{prefix}{entity_id}",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=MISSING_ENTITY,
            translation_placeholders={"entity_id": entity_id},
        )
