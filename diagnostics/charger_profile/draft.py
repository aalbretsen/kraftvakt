"""Draft charger profiles from the chargers a user has filled in by hand, and notes on what could not be carried over."""

from __future__ import annotations

import keyword
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.util import slugify

from custom_components.kraftvakt.charger_profiles.profile import (
    DEFAULT_ACTION,
    ChargerProfile,
    DeviceMatch,
    ProfileAction,
    ProfileCondition,
    ProfileEntity,
    custom_action,
    entity_action,
    entity_condition,
    power_sensor_condition,
    state_condition,
    template_condition,
)
from custom_components.kraftvakt.charger_profiles.recognition import DeviceEntities
from custom_components.kraftvakt.config_model import (
    CHARGER_ACTION_KINDS,
    CHARGER_CONDITION_TYPES,
    POWER_TYPES,
    ActionConfig,
    ActionMode,
    Charger,
    Condition,
    ConditionType,
    ConfigValidationError,
)
from custom_components.kraftvakt.config_reader import read_config
from custom_components.kraftvakt.domain_actions import domain_action_steps

from ..diagnostics_file import DiagnosticsFile, NotADiagnosticsFileError

# Integrations that serve devices of many makers, so a profile for one of them also names the manufacturer and model.
SHARED_INTEGRATIONS: Final = frozenset({"esphome", "homekit_controller", "matter", "modbus", "mqtt", "ocpp", "tuya", "zha", "zwave_js"})

QUOTED_ENTITY_ID: Final = re.compile(r"""(?<=['"])[a-z0-9_]+\.[a-z0-9_]+(?=['"])""")
DEVICE_ID: Final = re.compile(r"[0-9a-f]{32}")


@dataclass(frozen=True, slots=True)
class DescribedEntity:
    """An entity of a charger's device as the diagnostics describe it."""

    entity_id: str
    translation_key: str | None
    original_name: str | None
    has_entity_name: bool = True
    disabled: bool = False

    @property
    def domain(self) -> str:
        return self.entity_id.partition(".")[0]

    @classmethod
    def from_description(cls, description: Mapping[str, Any]) -> DescribedEntity:
        return cls(
            entity_id=description["entity_id"],
            translation_key=description.get("translation_key"),
            original_name=description.get("original_name"),
            has_entity_name=bool(description.get("has_entity_name", True)),
            disabled=description.get("disabled_by") is not None,
        )


@dataclass(frozen=True, slots=True)
class ProfileDraft:
    """A profile drafted from one charger, with the device and entities its test registers."""

    module: str
    profile: ChargerProfile
    manufacturer: str | None
    model_id: str | None
    entities: tuple[DescribedEntity, ...]
    charger_id: str
    notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Drafts:
    profiles: tuple[ProfileDraft, ...]
    skipped: tuple[str, ...]


def draft_profiles(diagnostics: DiagnosticsFile) -> Drafts:
    """Draft one profile for each kind of device among the chargers filled in by hand. A device with a profile already is skipped."""
    config_data = diagnostics.data.get("config")
    if not isinstance(config_data, Mapping):
        raise NotADiagnosticsFileError("The diagnostics have no Kraftvakt configuration")
    try:
        chargers = read_config(config_data).chargers
    except ConfigValidationError as error:
        raise NotADiagnosticsFileError(f"The Kraftvakt configuration in the diagnostics cannot be read: {error}") from error
    devices = diagnostics.data.get("charger_devices")
    if not isinstance(devices, Mapping):
        raise NotADiagnosticsFileError("The diagnostics describe no devices of the chargers")
    profiles: dict[DeviceMatch, ProfileDraft] = {}
    skipped = []
    for charger in chargers:
        device = devices.get(charger.id)
        if charger.device_id is None:
            skipped.append(f"Charger {charger.id} has no device.")
        elif device is None:
            skipped.append(f"Charger {charger.id}: its device is no longer in Home Assistant.")
        elif device.get("profile") is not None:
            skipped.append(f"Charger {charger.id} has the profile {device['profile']}.")
        else:
            draft = ProfileDrafting(charger, device).draft()
            if (same := profiles.get(draft.profile.device)) is not None:
                skipped.append(f"Charger {charger.id} has the same kind of device as charger {same.charger_id}.")
            else:
                profiles[draft.profile.device] = draft
    return Drafts(tuple(profiles.values()), tuple(skipped))


class ProfileDrafting:
    """Turns the fields of one charger into a profile, so the profile finds the same entities on any device of its kind."""

    def __init__(self, charger: Charger, device: Mapping[str, Any]) -> None:
        self._charger = charger
        self._device = device
        self._entities = tuple(DescribedEntity.from_description(entity) for entity in device.get("entities", []))
        self._by_id = {entity.entity_id: entity for entity in self._entities}
        self._finder = DeviceEntities(self._entities)
        self._notes: list[str] = []

    def draft(self) -> ProfileDraft:
        match = self._device_match()
        name = " ".join(filter(None, (self._device.get("manufacturer"), self._device.get("model_id") or self._device.get("model")))) or match.integration
        if match.integration in SHARED_INTEGRATIONS:
            name = f"{name} ({match.integration})"
        charger = self._charger
        profile = ChargerProfile(
            name=name,
            device=match,
            entity=self._main_entity(),
            activate=None if charger.switched_by_current else self._action("activate", charger.activate),
            deactivate=None if charger.switched_by_current else self._action("deactivate", charger.deactivate),
            switched_by_current=charger.switched_by_current,
            set_current=self._action("set_current", charger.set_current),
            car_connected=self._condition("car_connected", charger.car_connected, required=True),
            charging_power=self._condition("charging_power", charger.charging_power, required=True, kinds=POWER_TYPES),
            actively_charging=None if charger.actively_charging is None else self._condition("actively_charging", charger.actively_charging),
            cloud_controlled=charger.cloud_controlled,
            start_delay_s=charger.start_delay_s,
            deactivate_on_fault=charger.deactivate_on_fault,
            fault_flag=None if charger.fault_flag is None else self._condition("fault_flag", charger.fault_flag),
        )
        return ProfileDraft(
            module=slugify(name) or "charger",
            profile=profile,
            manufacturer=self._device.get("manufacturer"),
            model_id=self._device.get("model_id"),
            entities=self._entities,
            charger_id=charger.id,
            notes=tuple(self._notes),
        )

    def _device_match(self) -> DeviceMatch:
        integration: str | None = self._device.get("integration")
        if integration is None:
            self._notes.append("device: it has no integration. Fill in the integration of the profile.")
            return DeviceMatch(integration="")
        if integration not in SHARED_INTEGRATIONS:
            return DeviceMatch(integration)
        model_id = self._device.get("model_id")
        if model_id is None:
            self._notes.append(f"device: {integration} serves devices of many makers, and the device has no model ID, so the profile fits every model of its manufacturer.")
        return DeviceMatch(integration, manufacturer=self._device.get("manufacturer"), model_id=model_id)

    def _main_entity(self) -> ProfileEntity:
        entity_id = self._charger.entity_id
        if entity_id is None:
            self._notes.append("entity_id: not set. Fill in the entity that is activated.")
            return ProfileEntity("switch")
        return self._profile_entity("entity_id", entity_id) or ProfileEntity(entity_id.partition(".")[0])

    def _profile_entity(self, field: str, entity_id: str) -> ProfileEntity | None:
        """Return how the profile finds the entity, or None when it is not on the device."""
        entity = self._by_id.get(entity_id)
        if entity is None:
            self._notes.append(f"{field}: {entity_id} is not an entity of the charger's device, so a profile cannot find it.")
            return None
        return self._found_by(field, entity)

    def _found_by(self, field: str, entity: DescribedEntity) -> ProfileEntity:
        """Return what does not change with the language that the entity is found by, as the profile finds it."""
        if entity.translation_key is not None:
            wanted = ProfileEntity(entity.domain, translation_key=entity.translation_key)
        elif entity.original_name is not None:
            wanted = ProfileEntity(entity.domain, name=entity.original_name)
            if not entity.has_entity_name:
                self._notes.append(f"{field}: {entity.entity_id} has no name of its own apart from the device, so its name {entity.original_name!r} may hold the device's name.")
        else:
            wanted = ProfileEntity(entity.domain)
        if self._finder.find(wanted) != entity.entity_id:
            self._notes.append(f"{field}: {entity.entity_id} is not the only entity of the device that fits {wanted}, so the profile leaves the field out.")
        if entity.disabled:
            self._notes.append(f"{field}: {entity.entity_id} is disabled on this device, and a profile only uses enabled entities.")
        return wanted

    def _action(self, field: str, action: ActionConfig | None) -> ProfileAction:
        missing = custom_action()
        if action is None or action.is_missing:
            self._notes.append(f"{field}: not set. Fill in the action.")
            return missing
        if action.mode is ActionMode.DEFAULT:
            return DEFAULT_ACTION
        if action.mode is ActionMode.ENTITY and action.entity_id is not None:
            entity = self._profile_entity(field, action.entity_id)
            return missing if entity is None else entity_action(entity)
        if action.mode is ActionMode.DOMAIN:
            return self._domain_action(field, action) or missing
        return custom_action(*(self._general_step(field, step) for step in action.steps))

    def _domain_action(self, field: str, action: ActionConfig) -> ProfileAction | None:
        entity_id = self._charger.entity_id
        try:
            steps = domain_action_steps(CHARGER_ACTION_KINDS[field], entity_id or "", action)
        except ValueError:
            self._notes.append(f"{field}: the domain action {action.domain_action} does not fit the entity {entity_id}. Fill in the action.")
            return None
        self._notes.append(f"{field}: the domain action {action.domain_action} is written as the script steps it runs.")
        return custom_action(*(self._general_step(field, step) for step in steps))

    def _general_step(self, field: str, step: dict[str, Any]) -> dict[str, Any]:
        """Return the step with the charger's own device and entity given by the variable `entity_id`, so it works for any charger of the kind."""

        def general(key: str | None, value: Any) -> Any:
            if isinstance(value, Mapping):
                return {name: general(name, item) for name, item in value.items()}
            if isinstance(value, list):
                return [general(key, item) for item in value]
            if not isinstance(value, str):
                return value
            if key == "device_id" and value == self._charger.device_id:
                return "{{ device_id(entity_id) }}"
            if key == "entity_id" and value == self._charger.entity_id:
                return "{{ entity_id }}"
            if key == "device_id" and DEVICE_ID.fullmatch(value):
                self._notes.append(f"{field}: the action names the device {value}, which is not the charger's device.")
            elif key == "entity_id" and "{" not in value and value in self._by_id:
                self._notes.append(f"{field}: the action names {value}, but script steps in a profile can only name the charger's own entity, by the variable entity_id.")
            elif key == "entity_id" and "{" not in value:
                self._notes.append(f"{field}: the action names {value}, which is not on the charger's device.")
            else:
                for entity_id in self._by_id:
                    if _names(value, entity_id):
                        self._notes.append(f"{field}: the action names {entity_id} in {value!r}. Give it by the variable entity_id, or leave it out.")
            return value

        result: dict[str, Any] = general(None, step)
        return result

    def _condition(
        self,
        field: str,
        condition: Condition | None,
        required: bool = False,
        kinds: tuple[ConditionType, ...] = CHARGER_CONDITION_TYPES,
    ) -> ProfileCondition:
        """Return the condition as a profile finds it, or an empty one of the first of the field's `kinds`, which fills nothing."""
        missing = ProfileCondition(kinds[0])
        if condition is None or not condition.value:
            leave_out = "" if required else ", or leave it out if the integration has nothing for it"
            self._notes.append(f"{field}: not set. Fill in the condition{leave_out}.")
            return missing
        if condition.type is ConditionType.TEMPLATE:
            return self._template_condition(field, condition.value)
        entity = self._profile_entity(field, condition.value)
        if entity is None:
            return missing
        if condition.type is ConditionType.STATE:
            return state_condition(entity, condition.states, states_are_true=condition.states_are_true)
        return power_sensor_condition(entity) if condition.type is ConditionType.POWER_SENSOR else entity_condition(entity)

    def _template_condition(self, field: str, template: str) -> ProfileCondition:
        """Return the template with each entity of the device as a `$name` placeholder, found as the profile finds it."""
        template = template.replace("$", "$$")
        placeholders: dict[str, ProfileEntity] = {}
        for entity_id in sorted(self._by_id, key=len, reverse=True):
            if not _names(template, entity_id):
                continue
            entity = self._found_by(field, self._by_id[entity_id])
            name = _placeholder(entity, placeholders)
            placeholders[name] = entity
            template = re.sub(_entity_pattern(entity_id), f"${name}", template)
        for entity_id in QUOTED_ENTITY_ID.findall(template):
            self._notes.append(f"{field}: the template names {entity_id}, which is not on the charger's device.")
        return template_condition(template, **placeholders)


def _entity_pattern(entity_id: str) -> str:
    return rf"(?<!\w){re.escape(entity_id)}(?!\w)"


def _names(text: str, entity_id: str) -> bool:
    return re.search(_entity_pattern(entity_id), text) is not None


def _placeholder(entity: ProfileEntity, taken: Mapping[str, ProfileEntity]) -> str:
    """Return a name for the entity in a template, unique among those taken, that is also a keyword argument in Python."""
    base = slugify(entity.translation_key or entity.name) or entity.domain
    if not base.isidentifier() or keyword.iskeyword(base):
        base = f"{entity.domain}_{base}"
    name, number = base, 2
    while name in taken:
        name, number = f"{base}_{number}", number + 1
    return name
