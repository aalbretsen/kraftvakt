"""The Python source of a drafted profile module and its test, written as the profiles and their tests in the repository are."""

from __future__ import annotations

from typing import Any, Final

from homeassistant.util import slugify

from custom_components.kraftvakt.charger_profiles.profile import DEFAULT_ACTION, DEFAULT_CHARGER, DeviceMatch, ProfileAction, ProfileCondition, ProfileEntity
from custom_components.kraftvakt.charger_profiles.recognition import DeviceEntities
from custom_components.kraftvakt.config_model import ActionMode, ConditionType

from .draft import DescribedEntity, ProfileDraft

# The name the device gets in the drafted test, which gives the entity IDs there.
TEST_DEVICE_NAME: Final = "Garage"

CONDITION_HELPERS: Final = {ConditionType.ENTITY: "entity_condition", ConditionType.POWER_SENSOR: "power_sensor_condition"}


def profile_source(draft: ProfileDraft) -> str:
    profile = draft.profile
    writer = _ProfileWriter()
    fields = {
        "name": repr(profile.name),
        "device": writer.device_match(profile.device),
        "entity": writer.entity(profile.entity),
    }
    if profile.switched_by_current:
        fields["switched_by_current"] = "True"
    if profile.activate is not None:
        fields["activate"] = writer.action(profile.activate)
    if profile.deactivate is not None:
        fields["deactivate"] = writer.action(profile.deactivate)
    fields["set_current"] = writer.action(profile.set_current)
    fields["car_connected"] = writer.condition(profile.car_connected)
    if profile.actively_charging is not None:
        fields["actively_charging"] = writer.condition(profile.actively_charging)
    if profile.charging_power is not None:
        fields["charging_power"] = writer.condition(profile.charging_power)
    if profile.done_flag is not None:
        fields["done_flag"] = writer.condition(profile.done_flag)
    if profile.grace_period_s != DEFAULT_CHARGER.grace_period_s:
        fields["grace_period_s"] = str(profile.grace_period_s)
    if profile.cloud_controlled:
        fields["cloud_controlled"] = "True"
    if profile.start_delay_s != DEFAULT_CHARGER.start_delay_s:
        fields["start_delay_s"] = str(profile.start_delay_s)
    if profile.deactivate_on_fault:
        fields["deactivate_on_fault"] = "True"
    if profile.fault_flag is not None:
        fields["fault_flag"] = writer.condition(profile.fault_flag)
    imports = [f"from ..profile import {', '.join(sorted(writer.profile_names, key=_import_order))}"]
    if writer.uses_condition_type:
        imports.insert(0, "from ...config_model import ConditionType")
    arguments = "".join(f"    {name}={value},\n" for name, value in fields.items())
    return (
        f'"""{profile.name} with the {profile.device.integration} integration."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Final\n\n"
        f"{'\n'.join(imports)}\n\n"
        f"PROFILE: Final = ChargerProfile(\n{arguments})\n"
    )


def profile_test_source(draft: ProfileDraft) -> str:
    entities = harness_entities(draft.entities)
    expected = {"profile": draft.profile.name, "fields": DeviceEntities([entity for entity in entities if not entity.disabled]).fields(draft.profile)}
    device = {"integration": draft.profile.device.integration, "name": TEST_DEVICE_NAME, "manufacturer": draft.manufacturer, "model_id": draft.model_id}
    device_arguments = "".join(f"    {name}={value!r},\n" for name, value in device.items())
    entity_lines = "".join(f"        {_device_entity(entity)},\n" for entity in draft.entities)
    return (
        f'"""{draft.profile.name} with the {draft.profile.device.integration} integration, the device and its entities as the integration registers them."""\n\n'
        "from homeassistant.core import HomeAssistant\n\n"
        "from ..conftest import Command, Device, DeviceEntity, charger_profile, register, save_charger\n\n"
        f"DEVICE = Device(\n{device_arguments}    entities=[\n{entity_lines}    ],\n)\n\n\n"
        f"async def test_{draft.module}_fills_the_fields_of_a_charger(hass: HomeAssistant, command: Command) -> None:\n"
        "    device_id = register(hass, DEVICE)\n\n"
        "    result = await charger_profile(command, device_id)\n\n"
        f"    assert result == {expected!r}\n"
        '    saved = await save_charger(command, device_id, result["fields"])\n'
        '    assert saved["saved"]\n'
        '    assert [issue for issue in saved["missing"] if issue["section"] == "chargers"] == []\n'
    )


def harness_entities(entities: tuple[DescribedEntity, ...]) -> list[DescribedEntity]:
    """Return the entities with the entity IDs the test harness gives them, from the device name and the entity names, as `register` in the tests does."""
    taken: set[str] = set()
    renamed = []
    for entity in entities:
        base = f"{entity.domain}.{slugify(' '.join(filter(None, (TEST_DEVICE_NAME, entity.original_name))))}"
        entity_id, number = base, 2
        while entity_id in taken:
            entity_id, number = f"{base}_{number}", number + 1
        taken.add(entity_id)
        renamed.append(DescribedEntity(entity_id, entity.translation_key, entity.original_name, entity.has_entity_name, entity.disabled))
    return renamed


def _device_entity(entity: DescribedEntity) -> str:
    arguments = [repr(entity.domain), repr(entity.original_name)]
    if entity.translation_key is not None:
        arguments.append(repr(entity.translation_key))
    if entity.disabled:
        arguments.append("disabled=True")
    return f"DeviceEntity({', '.join(arguments)})"


def _import_order(name: str) -> tuple[int, str]:
    """Constants, then classes, then functions, as ruff sorts them."""
    return (0 if name.isupper() else 1 if name[0].isupper() else 2), name


class _ProfileWriter:
    """Writes the parts of a profile with the helpers of `profile.py`, and remembers which of them it used."""

    def __init__(self) -> None:
        self.profile_names = {"ChargerProfile"}
        self.uses_condition_type = False

    def _call(self, function: str, *arguments: str, **keywords: Any) -> str:
        self.profile_names.add(function)
        return f"{function}({', '.join([*arguments, *(f'{key}={value!r}' for key, value in keywords.items() if value is not None)])})"

    def device_match(self, match: DeviceMatch) -> str:
        return self._call("DeviceMatch", integration=match.integration, manufacturer=match.manufacturer, model_id=match.model_id)

    def entity(self, entity: ProfileEntity) -> str:
        return self._call("ProfileEntity", repr(entity.domain), translation_key=entity.translation_key, name=entity.name)

    def action(self, action: ProfileAction) -> str:
        if action == DEFAULT_ACTION:
            self.profile_names.add("DEFAULT_ACTION")
            return "DEFAULT_ACTION"
        if action.mode is ActionMode.ENTITY and action.entity is not None:
            return self._call("entity_action", self.entity(action.entity))
        return self._call("custom_action", *(repr(step) for step in action.steps))

    def condition(self, condition: ProfileCondition) -> str:
        if condition.type is ConditionType.TEMPLATE and condition.template is not None:
            entities = [f"{name}={self.entity(entity)}" for name, entity in condition.entities.items()]
            return self._call("template_condition", repr(condition.template), *entities)
        if condition.entity is not None and condition.type is ConditionType.STATE:
            states_are_true = [] if condition.states_are_true else ["states_are_true=False"]
            return self._call("state_condition", self.entity(condition.entity), repr(condition.states), *states_are_true)
        if condition.entity is not None:
            return self._call(CONDITION_HELPERS[condition.type], self.entity(condition.entity))
        self.uses_condition_type = True
        return self._call("ProfileCondition", f"ConditionType.{condition.type.name}")
