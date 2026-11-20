"""Sensors for the averages, the diagnostics of the regulation and the state of each charger."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NamedTuple

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import KraftvaktEntity
from .item_entity import ChargerEntity, async_setup_item_entities
from .regulation.charging import ChargerState
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RegulationSensorDescription(SensorEntityDescription):
    value_fn: Callable[[KraftvaktRuntime], float | None]


@dataclass(frozen=True, kw_only=True)
class PowerSensorDescription(RegulationSensorDescription):
    device_class: SensorDeviceClass = SensorDeviceClass.POWER
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    native_unit_of_measurement: str = UnitOfPower.WATT
    suggested_display_precision: int = 0


def _regulation_average_w(runtime: KraftvaktRuntime) -> float | None:
    averages = runtime.latest_averages
    return None if averages is None else averages.regulation_average_w


def _tariff_average_w(runtime: KraftvaktRuntime) -> float | None:
    averages = runtime.latest_averages
    return None if averages is None else averages.tariff_average_w


def _power_free_w(runtime: KraftvaktRuntime) -> float | None:
    average_w = _regulation_average_w(runtime)
    return None if average_w is None else runtime.config.general.power_limit_w - average_w


def _overconsumption_wh(runtime: KraftvaktRuntime) -> float:
    penalty = runtime.penalty
    return penalty.overconsumption_wh if penalty.overconsuming else 0.0


def _waiting_time_remaining_s(runtime: KraftvaktRuntime) -> int:
    """Return the seconds until the decision that ends the waiting time, or 0.

    It counts to the decision, since the step is turned on at the first
    decision after the waiting time.
    """
    ends_at = runtime.waiting_ends_at
    if ends_at is None:
        return 0
    return max(0, round((ends_at - dt_util.utcnow()).total_seconds()))


def _waiting_time_next_turn_on_s(runtime: KraftvaktRuntime) -> float | None:
    waiting_time = runtime.curve_waiting_time
    return None if waiting_time is None else waiting_time.total_seconds()


@dataclass(frozen=True, kw_only=True)
class DurationSensorDescription(RegulationSensorDescription):
    """Describes a diagnostic sensor that shows a duration in seconds."""

    entity_category: EntityCategory = EntityCategory.DIAGNOSTIC
    device_class: SensorDeviceClass = SensorDeviceClass.DURATION
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT
    native_unit_of_measurement: str = UnitOfTime.SECONDS
    suggested_display_precision: int = 0


SENSORS: tuple[RegulationSensorDescription, ...] = (
    PowerSensorDescription(key="power_regulation_average", value_fn=_regulation_average_w),
    PowerSensorDescription(key="power_tariff_average", value_fn=_tariff_average_w),
    PowerSensorDescription(
        key="power_free",
        value_fn=_power_free_w,
    ),
    RegulationSensorDescription(
        key="penalty_overconsumption",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=0,
        value_fn=_overconsumption_wh,
    ),
    RegulationSensorDescription(
        key="regulation_steps_on",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda runtime: runtime.steps_on,
    ),
    DurationSensorDescription(key="waiting_time_remaining", value_fn=_waiting_time_remaining_s),
    DurationSensorDescription(
        key="waiting_time_next_turn_on",
        entity_registry_enabled_default=False,
        value_fn=_waiting_time_next_turn_on_s,
    ),
)


class StateIcon(NamedTuple):
    """An icon from Material Design Icons and a colour name of the Home Assistant theme."""

    icon: str
    color: str

    @property
    def badge_color(self) -> str:
        """The colour of a circle behind the icon in white, darker for grey and amber, since white on them is hard to read."""
        return {"grey": "dark-grey", "amber": "orange"}.get(self.color, self.color)


CHARGER_STATE_ICONS: dict[ChargerState, StateIcon] = {
    ChargerState.STOPPED: StateIcon("mdi:stop-circle-outline", "red"),
    ChargerState.FAULT: StateIcon("mdi:alert-circle-outline", "red"),
    ChargerState.FIRST_DECISION: StateIcon("mdi:timer-sand", "grey"),
    ChargerState.NO_CAR: StateIcon("mdi:car-off", "grey"),
    ChargerState.EXCLUDED: StateIcon("mdi:cancel", "grey"),
    ChargerState.OUTSIDE_WINDOW: StateIcon("mdi:clock-outline", "amber"),
    ChargerState.QUEUED: StateIcon("mdi:timer-sand", "amber"),
    ChargerState.STARTING: StateIcon("mdi:cloud-clock-outline", "light-blue"),
    ChargerState.FINISHING: StateIcon("mdi:clock-end", "light-blue"),
    ChargerState.CHARGING: StateIcon("mdi:lightning-bolt", "green"),
    ChargerState.ACTIVATED: StateIcon("mdi:power-plug", "green"),
    ChargerState.OVERRIDE: StateIcon("mdi:clock-fast", "light-blue"),
    ChargerState.DEACTIVATED: StateIcon("mdi:pause-circle-outline", "amber"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KraftvaktConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(RegulationSensor(entry, entry.runtime_data, description) for description in SENSORS)
    async_setup_item_entities(hass, entry, async_add_entities, "sensor", (ChargerStateSensor,))


class RegulationSensor(KraftvaktEntity, SensorEntity):
    entity_description: RegulationSensorDescription

    def __init__(
        self,
        entry: KraftvaktConfigEntry,
        runtime: KraftvaktRuntime,
        description: RegulationSensorDescription,
    ) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description
        self._runtime = runtime

    async def async_added_to_hass(self) -> None:
        """Update the sensor each time the status of the regulation may change."""
        self.async_on_remove(self._runtime.async_add_status_listener(self.async_write_ha_state))

    @property
    def native_value(self) -> float | None:
        return self.entity_description.value_fn(self._runtime)

    @property
    def available(self) -> bool:
        return self.native_value is not None


class ChargerStateSensor(ChargerEntity, SensorEntity):
    """The state of the charger after the last decision, as on the status page.

    The icon and the colours are attributes, not icon translations, so templates can read them.
    """

    settings = ("state",)
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"icon", "color", "badge_color"})

    async def async_added_to_hass(self) -> None:
        """Follow the settings and the decisions."""
        await super().async_added_to_hass()
        self.async_on_remove(self._runtime.async_add_status_listener(self.async_write_ha_state))

    def _charger_state(self) -> ChargerState | None:
        status = self._runtime.chargers.get(self._item_id)
        return None if status is None else status.state

    @property
    def options(self) -> list[str]:
        return [state.value for state in ChargerState]

    @property
    def native_value(self) -> ChargerState | None:
        return self._charger_state()

    @property
    def icon(self) -> str | None:
        state = self._charger_state()
        return None if state is None else CHARGER_STATE_ICONS[state].icon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        state = self._charger_state()
        if state is None:
            return None
        state_icon = CHARGER_STATE_ICONS[state]
        return {"color": state_icon.color, "badge_color": state_icon.badge_color}
