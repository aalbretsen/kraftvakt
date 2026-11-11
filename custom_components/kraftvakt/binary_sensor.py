"""Binary sensors for the safe state, the penalty period and the charging windows."""

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
from .regulation.charging import window_allows_charging
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime


@dataclass(frozen=True, kw_only=True)
class RegulationBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a binary sensor that shows a state of the regulation."""

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
    """Add the binary sensors of the regulation and of the configured chargers."""
    async_add_entities(
        RegulationBinarySensor(entry, entry.runtime_data, description)
        for description in BINARY_SENSORS
    )
    async_setup_item_entities(
        hass, entry, async_add_entities, "binary_sensor", (ChargerWindowBinarySensor,)
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
        """Create the sensor described by `description`."""
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
        """Return whether the regulation is in the state."""
        return self.entity_description.is_on_fn(self._runtime)


class ChargerWindowBinarySensor(ChargerEntity, BinarySensorEntity):
    """Is on while the charging window, or its override, allows the charger to charge.

    It follows the clock, not the decisions, so it is also right while the
    regulation is stopped. A charging window is in whole minutes, so it is
    updated at every whole minute.
    """

    settings = ("window_allowed",)
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_added_to_hass(self) -> None:
        """Follow the board and the clock."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_change(self.hass, self._async_minute_started, second=0)
        )

    @callback
    def _async_minute_started(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return whether the charging window or its override allows charging."""
        charger = self._charger()
        return window_allows_charging(
            None if charger is None else charger.charging_window,
            self._board.charger_switches(self._item_id).window_override,
            dt_util.now().time(),
        )
