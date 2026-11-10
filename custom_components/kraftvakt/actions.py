"""Actions that turn appliances and chargers on and off.

The default actions for each entity domain are kept in one table, and
custom actions run as Home Assistant scripts.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from homeassistant.core import Context, HomeAssistant, split_entity_id
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script, async_validate_actions_config

from .conditions import context_variables
from .config_model import (
    ActionConfig,
    ActionMode,
    Appliance,
    Charger,
    Issue,
    KraftvaktConfig,
)
from .const import DOMAIN
from .regulation.model import (
    ActivateCharger,
    Command,
    DeactivateCharger,
    SetChargingCurrent,
    TurnOffAppliance,
    TurnOnAppliance,
)

_LOGGER = logging.getLogger(__name__)


class ActionKind(StrEnum):
    """What an action does."""

    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_CURRENT = "set_current"


@dataclass(frozen=True, slots=True)
class DefaultAction:
    """The action used for the entity domains that have an obvious one."""

    domains: tuple[str, ...]
    service: str
    data: Mapping[str, str] = field(default_factory=dict)


_ON_OFF_DOMAINS: Final = (
    "switch",
    "input_boolean",
    "light",
    "fan",
    "climate",
    "water_heater",
)

DEFAULT_ACTIONS: Final[Mapping[ActionKind, DefaultAction]] = {
    ActionKind.TURN_ON: DefaultAction(_ON_OFF_DOMAINS, "turn_on"),
    ActionKind.TURN_OFF: DefaultAction(_ON_OFF_DOMAINS, "turn_off"),
    ActionKind.SET_CURRENT: DefaultAction(
        ("number", "input_number"), "set_value", {"value": "{{ current }}"}
    ),
}

APPLIANCE_ACTIONS: Final[Mapping[str, ActionKind]] = {
    "turn_on": ActionKind.TURN_ON,
    "turn_off": ActionKind.TURN_OFF,
}

CHARGER_ACTIONS: Final[Mapping[str, ActionKind]] = {
    "activate": ActionKind.TURN_ON,
    "deactivate": ActionKind.TURN_OFF,
    "set_current": ActionKind.SET_CURRENT,
}


def default_action_steps(kind: ActionKind, entity_id: str) -> list[dict[str, Any]]:
    """Return the script steps of the default action for the entity.

    Raises ValueError when the domain of the entity has no default action.
    """
    domain = split_entity_id(entity_id)[0]
    default = DEFAULT_ACTIONS[kind]
    if domain not in default.domains:
        raise ValueError(f"{domain} has no default action to {kind}")
    step: dict[str, Any] = {
        "action": f"{domain}.{default.service}",
        "target": {"entity_id": entity_id},
    }
    if default.data:
        step["data"] = dict(default.data)
    return [step]


def default_action_issues(config: KraftvaktConfig) -> list[Issue]:
    """Return the default actions chosen for entities whose domain has none.

    That is the item's own entity for a default action, and the chosen entity
    when the action is given as another entity.
    """
    return [
        Issue(code, section, item.id, field_name)
        for section, item, fields in _items_with_actions(config)
        for field_name, kind in fields.items()
        if (
            code := _unavailable_default(
                item.entity_id, getattr(item, field_name), kind
            )
        )
    ]


def default_action_domains() -> dict[str, dict[str, list[str]]]:
    """Return the domains that have a default action, by section and field.

    The panel offers the default action only for these domains.
    """
    return {
        section: {
            field_name: list(DEFAULT_ACTIONS[kind].domains)
            for field_name, kind in fields.items()
        }
        for section, fields in (
            ("appliances", APPLIANCE_ACTIONS),
            ("chargers", CHARGER_ACTIONS),
        )
    }


def set_current_variables(charger: Charger, current: int) -> dict[str, int]:
    """Return the variables of the action that sets the charging current.

    The current is kept between the minimum and the maximum.
    """
    return {
        "current": min(max(current, charger.min_current_a), charger.max_current_a),
        "min_current": charger.min_current_a,
        "max_current": charger.max_current_a,
    }


class ActionRunner:
    """Carries out the commands from the regulation engine.

    The commands run one at a time in the order they are given, also across
    decisions. A failed action is logged and not retried, and the rest of the
    commands still run. Commands that are not actions, such as
    resetting the window override, are left to the caller.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: KraftvaktConfig,
        lock: asyncio.Lock | None = None,
    ) -> None:
        """Create the runner for the appliances and chargers in the configuration.

        Runners that share `lock` run their commands one at a time, so a runner
        for a new configuration waits for the commands of the previous one.
        """
        self._hass = hass
        self._appliances = {appliance.id: appliance for appliance in config.appliances}
        self._chargers = {charger.id: charger for charger in config.charging.chargers}
        self._lock = lock or asyncio.Lock()
        self._scripts: dict[tuple[str, ActionKind], Script] = {}

    async def async_execute(self, commands: Sequence[Command]) -> None:
        """Run the actions for the commands, in order, after any earlier ones."""
        async with self._lock:
            for command in commands:
                await self._async_execute_command(command)

    async def _async_execute_command(self, command: Command) -> None:
        match command:
            case TurnOnAppliance(appliance_id):
                appliance = self._appliances[appliance_id]
                await self._async_run(appliance, appliance.turn_on, ActionKind.TURN_ON)
            case TurnOffAppliance(appliance_id):
                appliance = self._appliances[appliance_id]
                await self._async_run(
                    appliance, appliance.turn_off, ActionKind.TURN_OFF
                )
            case ActivateCharger(charger_id):
                charger = self._chargers[charger_id]
                await self._async_run(charger, charger.activate, ActionKind.TURN_ON)
            case DeactivateCharger(charger_id):
                charger = self._chargers[charger_id]
                await self._async_run(charger, charger.deactivate, ActionKind.TURN_OFF)
            case SetChargingCurrent(charger_id, current):
                charger = self._chargers[charger_id]
                await self._async_run(
                    charger,
                    charger.set_current,
                    ActionKind.SET_CURRENT,
                    set_current_variables(charger, current),
                )

    async def _async_run(
        self,
        item: Appliance | Charger,
        action: ActionConfig | None,
        kind: ActionKind,
        variables: Mapping[str, Any] | None = None,
    ) -> None:
        """Run the action with `entity_id`, `entity` and `variables`, and log errors."""
        try:
            script = await self._async_script(item.entity_id, action, kind)
            await script.async_run(
                {**context_variables(self._hass, item.entity_id), **(variables or {})},
                Context(),
            )
        except Exception as err:  # The regulation goes on regardless.
            _LOGGER.error("Could not %s %s: %s", kind, item.entity_id, err)

    async def _async_script(
        self, entity_id: str | None, action: ActionConfig | None, kind: ActionKind
    ) -> Script:
        if entity_id is None or action is None:
            raise ValueError("the action is not configured")
        key = (entity_id, kind)
        if key not in self._scripts:
            steps = _action_steps(entity_id, action, kind)
            sequence = await async_validate_actions_config(
                self._hass, cv.SCRIPT_SCHEMA(steps)
            )
            self._scripts[key] = Script(
                self._hass,
                sequence,
                f"{kind} {entity_id}",
                DOMAIN,
                logger=_LOGGER,
                log_exceptions=False,
            )
        return self._scripts[key]


def _items_with_actions(
    config: KraftvaktConfig,
) -> Iterable[tuple[str, Appliance | Charger, Mapping[str, ActionKind]]]:
    for appliance in config.appliances:
        yield "appliances", appliance, APPLIANCE_ACTIONS
    for charger in config.charging.chargers:
        yield "chargers", charger, CHARGER_ACTIONS


def _action_steps(
    entity_id: str, action: ActionConfig, kind: ActionKind
) -> list[dict[str, Any]]:
    match action.mode:
        case ActionMode.DEFAULT:
            return default_action_steps(kind, entity_id)
        case ActionMode.ENTITY if action.entity_id is not None:
            return default_action_steps(kind, action.entity_id)
        case ActionMode.ENTITY:
            raise ValueError("the entity of the action is not chosen")
    return copy.deepcopy(list(action.steps))


def _unavailable_default(
    entity_id: str | None, action: ActionConfig | None, kind: ActionKind
) -> str | None:
    """Return the issue when a default action is chosen for a domain without one."""
    if action is None:
        return None
    match action.mode:
        case ActionMode.DEFAULT if entity_id is not None:
            code, target = "default_action_unavailable", entity_id
        case ActionMode.ENTITY if action.entity_id is not None:
            code, target = "unsupported_entity_domain", action.entity_id
        case _:
            return None
    domain = split_entity_id(target)[0] if "." in target else None
    return None if domain in DEFAULT_ACTIONS[kind].domains else code
