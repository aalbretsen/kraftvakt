"""The profile of a device, and the fields of a charger it fills."""

from __future__ import annotations

from collections.abc import Sequence
from string import Template
from typing import Any, Protocol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from ..config_model import ActionConfig, ActionMode, Condition, ConditionType
from .profile import ChargerProfile, DeviceMatch, ProfileAction, ProfileCondition, ProfileEntity
from .profiles import PROFILES


def charger_profile_fields(hass: HomeAssistant, device_id: str) -> tuple[ChargerProfile | None, dict[str, Any]]:
    """Return the profile of the device and the fields of a charger it fills, as stored.

    A field whose entity is not on the device, or is disabled, is left out.
    """
    device = dr.async_get(hass).async_get(device_id)
    profile = _profile_of(hass, device) if isinstance(device, dr.DeviceEntry) else None
    if profile is None:
        return None, {}
    return profile, DeviceEntities(er.async_entries_for_device(er.async_get(hass), device_id)).fields(profile)


def device_integrations(hass: HomeAssistant, device: dr.DeviceEntry) -> set[str]:
    return {entry.domain for entry_id in device.config_entries if (entry := hass.config_entries.async_get_entry(entry_id)) is not None}


def _profile_of(hass: HomeAssistant, device: dr.DeviceEntry) -> ChargerProfile | None:
    integrations = device_integrations(hass, device)
    return next((profile for profile in PROFILES if _is_for(profile.device, device, integrations)), None)


def _is_for(match: DeviceMatch, device: dr.DeviceEntry, integrations: set[str]) -> bool:
    return match.integration in integrations and match.manufacturer in (None, device.manufacturer) and match.model_id in (None, device.model_id)


class RegisteredEntity(Protocol):
    """What a profile finds an entity by: the registry entry, or a description of it, as the diagnostics tools read it."""

    @property
    def entity_id(self) -> str: ...

    @property
    def domain(self) -> str: ...

    @property
    def translation_key(self) -> str | None: ...

    @property
    def original_name(self) -> str | None: ...


class DeviceEntities:
    """The enabled entities of a device, and the stored fields made from them."""

    def __init__(self, entries: Sequence[RegisteredEntity]) -> None:
        self._entries = entries

    def fields(self, profile: ChargerProfile) -> dict[str, Any]:
        """Return the fields of a charger the profile fills, as stored, leaving out those it cannot fill."""
        fields = {
            "entity_id": self.find(profile.entity),
            "activate": self.action(profile.activate),
            "deactivate": self.action(profile.deactivate),
            "set_current": self.action(profile.set_current),
            "car_connected": self.condition(profile.car_connected),
            "actively_charging": self.condition(profile.actively_charging),
            "quiet_without_car": profile.quiet_without_car,
        }
        return {name: value for name, value in fields.items() if value is not None}

    def find(self, wanted: ProfileEntity) -> str | None:
        """Return the entity ID of the only entity that fits, if there is one."""
        found = [entry.entity_id for entry in self._entries if _fits(entry, wanted)]
        return found[0] if len(found) == 1 else None

    def action(self, action: ProfileAction) -> dict[str, Any] | None:
        if action.entity is None:
            return ActionConfig(action.mode, steps=action.steps).to_dict()
        entity_id = self.find(action.entity)
        return None if entity_id is None else ActionConfig(ActionMode.ENTITY, entity_id=entity_id).to_dict()

    def condition(self, condition: ProfileCondition) -> dict[str, Any] | None:
        if condition.type is ConditionType.TEMPLATE and condition.template is not None:
            entity_ids = {name: self.find(entity) for name, entity in condition.entities.items()}
            if None in entity_ids.values():
                return None
            return Condition(condition.type, Template(condition.template).substitute(entity_ids)).to_dict()
        entity_id = None if condition.entity is None else self.find(condition.entity)
        return None if entity_id is None else Condition(condition.type, entity_id).to_dict()


def _fits(entry: RegisteredEntity, wanted: ProfileEntity) -> bool:
    if entry.domain != wanted.domain:
        return False
    if wanted.translation_key is not None:
        return entry.translation_key == wanted.translation_key
    if wanted.name is not None:
        return entry.original_name == wanted.name
    return entry.translation_key is None and entry.original_name is None
