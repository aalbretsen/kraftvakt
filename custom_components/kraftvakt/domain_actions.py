"""Actions that belong to the domain of an entity, with values the user chooses.

A domain action calls one service of the entity's domain. Its parameters are
checked against the attributes of the entity, for example the HVAC modes a
thermostat supports, when the entity has them.

A temperature is a number, a template, or a temperature source: a source of
the same form as a display temperature, but without a template, that names
an entity whose value is read when the action runs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from homeassistant.core import HomeAssistant, State, split_entity_id, valid_entity_id
from homeassistant.util.unit_conversion import TemperatureConverter

from .conditions import temperature_value
from .config_model import ActionConfig, ActionKind, Condition, ConditionType


class ParameterType(StrEnum):
    """What kind of value a parameter takes, and how the panel shows it.

    A temperature may also be a template, rendered when the action runs, or
    a temperature source, read when the action runs.
    """

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

    def within_range(self, value: float, state: State | None) -> float:
        """Return the value moved inside the range of the entity, when it tells it."""
        low, high = self._range(state)
        if _is_number(low):
            value = max(value, low)
        if _is_number(high):
            value = min(value, high)
        return value

    def _range(self, state: State | None) -> tuple[Any, Any]:
        attributes = state.attributes if state is not None else {}
        return (
            None if self.min_attribute is None else attributes.get(self.min_attribute),
            None if self.max_attribute is None else attributes.get(self.max_attribute),
        )

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
        if isinstance(value, str):
            return None
        if isinstance(value, Mapping):
            return _source_issue(value)
        if not _is_number(value):
            return "invalid_type"
        low, high = self._range(state)
        if (_is_number(low) and value < low) or (_is_number(high) and value > high):
            return "outside_entity_range"
        return None


@dataclass(frozen=True, slots=True)
class DomainAction:
    """A service of an entity domain, called for the entity with the chosen data.

    A suggested domain action is the one the panel chooses for a new entity of its domain, before the default action.
    """

    domain: str
    service: str
    parameters: tuple[ActionParameter, ...]
    kinds: tuple[ActionKind, ...] = (ActionKind.TURN_ON, ActionKind.TURN_OFF)
    suggested: bool = False

    def to_dict(self, kind: ActionKind) -> dict[str, Any]:
        """Return the domain action for an action of the kind, for the panel."""
        return {
            "domain": self.domain,
            "service": self.service,
            "parameters": [parameter.to_dict(kind) for parameter in self.parameters],
            "suggested": self.suggested,
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

TEMPERATURE_SOURCE_DOMAINS: Final[Mapping[str, tuple[str, ...]]] = {
    ConditionType.TEMPERATURE_SENSOR: ("sensor", "input_number", "number"),
    ConditionType.CURRENT_TEMPERATURE: ("climate",),
    ConditionType.TARGET_TEMPERATURE: ("climate",),
}

# The default is outside every thermostat's range, so the user must choose it.
TARGET_TEMPERATURE: Final = ActionParameter(
    "temperature",
    ParameterType.TEMPERATURE,
    min_attribute="min_temp",
    max_attribute="max_temp",
    step_attribute="target_temp_step",
    default=0,
)

# Most thermostats are better controlled by their HVAC mode than turned on and off.
DOMAIN_ACTIONS: Final[Mapping[str, DomainAction]] = {
    "climate_hvac_mode": DomainAction("climate", "set_hvac_mode", (HVAC_MODE,), suggested=True),
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


def domain_action_templates(action: ActionConfig) -> dict[str, str]:
    """Return the values of the domain action given as templates, by parameter."""
    domain_action = DOMAIN_ACTIONS.get(action.domain_action or "")
    if domain_action is None:
        return {}
    return {
        parameter.name: value for parameter in domain_action.parameters if parameter.type is ParameterType.TEMPERATURE and isinstance(value := action.data.get(parameter.name), str)
    }


def has_temperature_sources(action: ActionConfig) -> bool:
    return any(isinstance(value, Mapping) for value in action.data.values())


def resolved_domain_action(hass: HomeAssistant, entity_id: str, action: ActionConfig) -> ActionConfig:
    """Return the action with the value of each temperature source now.

    The value is in Home Assistant's unit and within the range of the entity,
    so the thermostat accepts it. A source that is not chosen is left for the
    action to report as missing.
    Raises ValueError when a source gives no value.
    """
    domain_action = DOMAIN_ACTIONS.get(action.domain_action or "")
    if domain_action is None:
        return action
    state = hass.states.get(entity_id)
    data = dict(action.data)
    for parameter in domain_action.parameters:
        source = data.get(parameter.name)
        if isinstance(source, Mapping) and source.get("value"):
            data[parameter.name] = parameter.within_range(_source_value(hass, source), state)
    return ActionConfig(action.mode, domain_action=action.domain_action, data=data)


def _source_value(hass: HomeAssistant, source: Mapping[str, Any]) -> float:
    condition = Condition(ConditionType(source["type"]), source["value"])
    reading = temperature_value(hass, condition, {})
    if reading is None:
        raise ValueError(f"{condition.value} gives no temperature")
    value, unit = reading
    target_unit = hass.config.units.temperature_unit
    if unit != target_unit and unit in TemperatureConverter.VALID_UNITS:
        return TemperatureConverter.convert(value, unit, target_unit)
    return value


def _source_issue(source: Mapping[str, Any]) -> str | None:
    """Return the code of what is wrong with a temperature source; one without an entity is missing."""
    source_type, entity_id = source.get("type"), source.get("value")
    if not isinstance(source_type, str) or source_type not in TEMPERATURE_SOURCE_DOMAINS or not isinstance(entity_id, str | None):
        return "invalid_type"
    if not entity_id:
        return None
    if not valid_entity_id(entity_id):
        return "invalid_type"
    if split_entity_id(entity_id)[0] in TEMPERATURE_SOURCE_DOMAINS[source_type]:
        return None
    return "unsupported_entity_domain" if source_type == ConditionType.TEMPERATURE_SENSOR else "not_a_thermostat"


def _available(kind: ActionKind, entity_id: str, key: str | None) -> DomainAction | None:
    domain_action = DOMAIN_ACTIONS.get(key or "")
    if domain_action is None or kind not in domain_action.kinds or "." not in entity_id or split_entity_id(entity_id)[0] != domain_action.domain:
        return None
    return domain_action


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
