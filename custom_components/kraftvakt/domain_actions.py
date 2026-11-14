"""Actions that belong to the domain of an entity, with values the user chooses.

A domain action calls one service of the entity's domain. Its parameters are
checked against the attributes of the entity, for example the HVAC modes a
thermostat supports, when the entity has them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from homeassistant.core import State, split_entity_id

from .config_model import ActionConfig, ActionKind


class ParameterType(StrEnum):
    """What kind of value a parameter takes, and how the panel shows it."""

    OPTION = "option"
    TEMPERATURE = "temperature"


@dataclass(frozen=True, slots=True)
class ActionParameter:
    """A value in the data of a domain action.

    The options and the range come from attributes of the entity. The default
    option is the first preferred option for the action kind that the entity
    supports.
    """

    name: str
    type: ParameterType
    options_attribute: str | None = None
    preferred_options: Mapping[ActionKind, tuple[str, ...]] = field(default_factory=dict)
    min_attribute: str | None = None
    max_attribute: str | None = None
    step_attribute: str | None = None
    default: float | None = None

    def to_dict(self, kind: ActionKind) -> dict[str, Any]:
        """Return the parameter for an action of the kind, for the panel."""
        return {
            "name": self.name,
            "type": self.type.value,
            "options_attribute": self.options_attribute,
            "preferred_options": list(self.preferred_options.get(kind, ())),
            "min_attribute": self.min_attribute,
            "max_attribute": self.max_attribute,
            "step_attribute": self.step_attribute,
            "default": self.default,
        }

    def issue(self, value: Any, state: State | None) -> str | None:
        """Return the code of what is wrong with the value, or None.

        A value that is not chosen yet is not wrong, only missing.
        """
        if value is None:
            return None
        attributes = state.attributes if state is not None else {}

        def attribute(name: str | None) -> Any:
            return None if name is None else attributes.get(name)

        if self.type is ParameterType.OPTION:
            if not isinstance(value, str):
                return "invalid_type"
            options = attribute(self.options_attribute)
            if isinstance(options, list) and value not in options:
                return "unsupported_option"
            return None
        if not _is_number(value):
            return "invalid_type"
        low = attribute(self.min_attribute)
        high = attribute(self.max_attribute)
        if (_is_number(low) and value < low) or (_is_number(high) and value > high):
            return "outside_entity_range"
        return None


@dataclass(frozen=True, slots=True)
class DomainAction:
    """A service of an entity domain, called for the entity with the chosen data."""

    domain: str
    service: str
    parameters: tuple[ActionParameter, ...]
    kinds: tuple[ActionKind, ...] = (ActionKind.TURN_ON, ActionKind.TURN_OFF)

    def to_dict(self, kind: ActionKind) -> dict[str, Any]:
        """Return the domain action for an action of the kind, for the panel."""
        return {
            "domain": self.domain,
            "service": self.service,
            "parameters": [parameter.to_dict(kind) for parameter in self.parameters],
        }

    def steps(self, entity_id: str, data: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "action": f"{self.domain}.{self.service}",
                "target": {"entity_id": entity_id},
                "data": {parameter.name: data[parameter.name] for parameter in self.parameters},
            }
        ]


HVAC_MODE: Final = ActionParameter(
    "hvac_mode",
    ParameterType.OPTION,
    options_attribute="hvac_modes",
    preferred_options={
        ActionKind.TURN_ON: ("heat", "auto"),
        ActionKind.TURN_OFF: ("off", "auto"),
    },
)

# The default is outside every thermostat's range, so the user must choose it.
TARGET_TEMPERATURE: Final = ActionParameter(
    "temperature",
    ParameterType.TEMPERATURE,
    min_attribute="min_temp",
    max_attribute="max_temp",
    step_attribute="target_temp_step",
    default=0,
)

DOMAIN_ACTIONS: Final[Mapping[str, DomainAction]] = {
    "climate_hvac_mode": DomainAction("climate", "set_hvac_mode", (HVAC_MODE,)),
    "climate_temperature": DomainAction("climate", "set_temperature", (TARGET_TEMPERATURE,)),
    "climate_hvac_mode_and_temperature": DomainAction("climate", "set_temperature", (HVAC_MODE, TARGET_TEMPERATURE)),
}


def domain_actions_for(kind: ActionKind) -> dict[str, dict[str, Any]]:
    """Return the domain actions an action of the kind may be, for the panel."""
    return {key: action.to_dict(kind) for key, action in DOMAIN_ACTIONS.items() if kind in action.kinds}


def domain_action_steps(kind: ActionKind, entity_id: str, action: ActionConfig) -> list[dict[str, Any]]:
    """Return the script steps of the domain action for the entity.

    Raises ValueError when the action is not available for the entity or
    a value is not chosen.
    """
    domain_action = _available(kind, entity_id, action.domain_action)
    if domain_action is None:
        raise ValueError(f"{action.domain_action} is not available for {entity_id}")
    if action.is_missing or any(parameter.name not in action.data for parameter in domain_action.parameters):
        raise ValueError(f"a value of {action.domain_action} is not chosen")
    return domain_action.steps(entity_id, action.data)


def domain_action_issues(kind: ActionKind, entity_id: str, action: ActionConfig, state: State | None) -> list[tuple[str | None, str]]:
    """Return what is wrong with the domain action, as parameter and code.

    The parameter is None when the action itself is wrong. The values are
    checked against the attributes in `state`, when it is known.
    """
    domain_action = _available(kind, entity_id, action.domain_action)
    if domain_action is None:
        return [(None, "domain_action_unavailable")]
    issues: list[tuple[str | None, str]] = []
    for parameter in domain_action.parameters:
        if parameter.name not in action.data:
            issues.append((parameter.name, "required"))
        elif code := parameter.issue(action.data[parameter.name], state):
            issues.append((parameter.name, code))
    return issues


def _available(kind: ActionKind, entity_id: str, key: str | None) -> DomainAction | None:
    domain_action = DOMAIN_ACTIONS.get(key or "")
    if domain_action is None or kind not in domain_action.kinds or "." not in entity_id or split_entity_id(entity_id)[0] != domain_action.domain:
        return None
    return domain_action


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
