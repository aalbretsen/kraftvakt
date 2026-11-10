"""Data passed in and out of the regulation engine."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, tzinfo

from .charging import ChargerReading, ChargingState
from .penalty import PenaltyState
from .waiting import CyclingCounter, CyclingSteps


@dataclass(frozen=True, slots=True)
class DecisionInput:
    """Snapshot of what a decision is based on.

    `power_sensor_lost` tells whether the power sensor was invalid when each of
    the last two windows closed. A variant missing from `variant_conditions`
    counts as false.
    """

    now: datetime
    regulation_average_w: float | None
    capacity_average_w: float | None
    regulation_averages_w: Sequence[float]
    power_sensor_valid: bool
    power_sensor_lost: bool
    variant_conditions: Mapping[str, bool] = field(default_factory=dict)
    chargers: Mapping[str, ChargerReading] = field(default_factory=dict)
    time_zone: tzinfo = UTC


@dataclass(frozen=True, slots=True)
class TurnOnAppliance:
    """Run the action that turns the appliance on."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class TurnOffAppliance:
    """Run the action that turns the appliance off."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class ActivateCharger:
    """Run the action that allows the charger to charge."""

    charger_id: str


@dataclass(frozen=True, slots=True)
class DeactivateCharger:
    """Run the action that does not allow the charger to charge."""

    charger_id: str


@dataclass(frozen=True, slots=True)
class SetChargingCurrent:
    """Run the action that sets the charging current in amperes."""

    charger_id: str
    current_a: int


@dataclass(frozen=True, slots=True)
class ResetWindowOverride:
    """Switch off the override of the charging window."""

    charger_id: str


type Command = (
    TurnOnAppliance
    | TurnOffAppliance
    | ActivateCharger
    | DeactivateCharger
    | SetChargingCurrent
    | ResetWindowOverride
)


@dataclass(frozen=True, slots=True)
class ApplianceSlotKey:
    """Identifies the slot of an appliance, whichever variant is current."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class ChargerSlotKey:
    """Identifies a fictive appliance of a charger, counted from 0."""

    charger_id: str
    index: int


@dataclass(frozen=True, slots=True)
class Slot:
    """A place in the order the regulation turns things on and off."""

    key: Hashable
    is_on: bool
    power_reserve_w: float | None
    cycling: CyclingSteps
    can_turn_on: bool = True
    can_turn_off: bool = True


@dataclass(frozen=True, slots=True)
class Waiting:
    """A waiting time that runs before the slot may be turned on.

    The slot is turned on at the first decision at or after `until`.
    """

    key: Hashable
    started_at: datetime
    until: datetime


@dataclass(slots=True)
class RegulationState:
    """What the regulation keeps track of while it runs."""

    started_at: datetime | None = None
    appliances_on: set[str] = field(default_factory=set)
    current_variants: dict[str, str | None] = field(default_factory=dict)
    waiting: Waiting | None = None
    cycling: CyclingCounter = field(default_factory=CyclingCounter)
    penalty: PenaltyState = field(default_factory=PenaltyState)
    safe_state: bool = False
    charging: ChargingState = field(default_factory=ChargingState)
