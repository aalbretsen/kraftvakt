"""Binary sensors for the safe state, the penalty and whether chargers may charge."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util import dt as dt_util

from .entity import KraftvaktEntity
from .item_entity import ChargerEntity, async_setup_item_entities
from .regulation.charging import charging_allowed_now
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RegulationBinarySensorDescription(BinarySensorEntityDescription):
    is_on_fn: Callable[[KraftvaktRuntime], bool]
    device_class: BinarySensorDeviceClass = BinarySensorDeviceClass.PROBLEM


BINARY_SENSORS: tuple[RegulationBinarySensorDescription, ...] = (
    RegulationBinarySensorDescription(
        key="regulation_safe_state",
        is_on_fn=lambda runtime: runtime.safe_state,
    ),
    RegulationBinarySensorDescription(
        key="penalty_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda runtime: runtime.penalty.active,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        RegulationBinarySensor(entry, entry.runtime_data, description)
        for description in BINARY_SENSORS
    )
    async_setup_item_entities(
        hass, entry, async_add_entities, "binary_sensor", (ChargerAllowedBinarySensor,)
    )


class RegulationBinarySensor(KraftvaktEntity, BinarySensorEntity):
    """Is on while the regulation is in the described state."""

    entity_description: RegulationBinarySensorDescription

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        runtime: KraftvaktRuntime,
        description: RegulationBinarySensorDescription,
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Update the sensor each time the status of the regulation may change."""
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        return self.entity_description.is_on_fn(self._runtime)


class ChargerAllowedBinarySensor(ChargerEntity, BinarySensorEntity):
    """Is on while the charger may charge.

    The charging window and the switches follow the clock and the settings,
    so it is also right while the regulation is stopped. A charging window is
    in whole minutes, so it is updated at every whole minute, and finishing
    is updated at the decisions.
    """

    settings = ("allowed_to_charge",)
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_added_to_hass(self) -> None:
        """Follow the settings, the decisions and the clock."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._runtime.async_add_status_listener(self.async_write_ha_state)
        )
        self.async_on_remove(
            async_track_time_change(self.hass, self._async_minute_started, second=0)
        )

    @callback
    def _async_minute_started(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        charger = self._charger()
        if charger is None:
            return False
        switches = self._settings.charger_switches(self._item_id)
        return charging_allowed_now(
            charger,
            self._runtime.chargers.get(self._item_id),
            switches.excluded,
            switches.window_override,
            dt_util.now().time(),
        )
