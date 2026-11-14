"""What a charger profile is made of."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..config_model import ActionMode, ConditionType


@dataclass(frozen=True, slots=True)
class DeviceMatch:
    """The devices a profile is for: those of an integration, and of a manufacturer and model where one integration serves many."""

    integration: str
    manufacturer: str | None = None
    model_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProfileEntity:
    """An entity of the device, found by what does not change with the language.

    With neither a translation key nor a name, it is the main entity of the device, which has no name of its own.
    The name is the one the integration gives, before the user renames the entity.
    """

    domain: str
    translation_key: str | None = None
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ProfileAction:
    """An action: the default action of the charger's entity, script steps, or the default action of another entity of the device."""

    mode: ActionMode
    steps: tuple[dict[str, Any], ...] = ()
    entity: ProfileEntity | None = None


@dataclass(frozen=True, slots=True)
class ProfileCondition:
    """A condition from an entity or a power sensor of the device, or a template.

    `$name` in a template is replaced by the entity ID of the entity `name` in `entities`.
    """

    type: ConditionType
    entity: ProfileEntity | None = None
    template: str | None = None
    entities: Mapping[str, ProfileEntity] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChargerProfile:
    """How Kraftvakt controls the chargers of a known integration. The name is shown to the user."""

    name: str
    device: DeviceMatch
    entity: ProfileEntity
    activate: ProfileAction
    deactivate: ProfileAction
    set_current: ProfileAction
    car_connected: ProfileCondition
    actively_charging: ProfileCondition


DEFAULT_ACTION = ProfileAction(ActionMode.DEFAULT)


def custom_action(*steps: dict[str, Any]) -> ProfileAction:
    return ProfileAction(ActionMode.CUSTOM, steps=steps)


def entity_action(entity: ProfileEntity) -> ProfileAction:
    return ProfileAction(ActionMode.ENTITY, entity=entity)


def entity_condition(entity: ProfileEntity) -> ProfileCondition:
    return ProfileCondition(ConditionType.ENTITY, entity=entity)


def power_sensor_condition(entity: ProfileEntity) -> ProfileCondition:
    return ProfileCondition(ConditionType.POWER_SENSOR, entity=entity)


def template_condition(template: str, **entities: ProfileEntity) -> ProfileCondition:
    return ProfileCondition(ConditionType.TEMPLATE, template=template, entities=entities)
