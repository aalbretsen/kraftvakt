"""Data passed in and out of the regulation engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, tzinfo

from .charging import ChargerReading, ChargingState
from .penalty import PenaltyState
from .waiting import RepeatedTurnOnCounter, RepeatedTurnOnGrowth


@dataclass(frozen=True, slots=True)
class DecisionInput:
    """Snapshot of what a decision is based on.

    `power_sensor_lost` tells whether the power sensor was invalid when each of
    the last two windows closed. A variant missing from `variant_conditions`
    counts as false.
    """

    now: datetime
    regulation_average_w: float | None
    tariff_average_w: float | None
    regulation_averages_w: Sequence[float]
    power_sensor_valid: bool
    power_sensor_lost: bool
    variant_conditions: Mapping[str, bool] = field(default_factory=dict)
    chargers: Mapping[str, ChargerReading] = field(default_factory=dict)
    excluded_appliances: frozenset[str] = frozenset()
    time_zone: tzinfo = UTC


@dataclass(frozen=True, slots=True)
class TurnOnAppliance:
    """Run the action that turns the appliance on, as its variant does it."""

    appliance_id: str
    variant_id: str | None = None


@dataclass(frozen=True, slots=True)
class TurnOffAppliance:
    """Run the action that turns the appliance off, as its variant does it."""

    appliance_id: str
    variant_id: str | None = None


@dataclass(frozen=True, slots=True)
class ActivateCharger:
    charger_id: str


@dataclass(frozen=True, slots=True)
class DeactivateCharger:
    charger_id: str


@dataclass(frozen=True, slots=True)
class SetChargingCurrent:
    charger_id: str
    current_a: int


type Command = (
    TurnOnAppliance
    | TurnOffAppliance
    | ActivateCharger
    | DeactivateCharger
    | SetChargingCurrent
)


@dataclass(frozen=True, slots=True)
class ApplianceStepKey:
    """Identifies the step of an appliance, whichever variant is current."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class AmpereStepKey:
    """Identifies an ampere step of a charger, counted from 0."""

    charger_id: str
    index: int


type StepKey = ApplianceStepKey | AmpereStepKey


@dataclass(frozen=True, slots=True)
class Step:
    """A place in the order the regulation turns things on and off."""

    key: StepKey
    is_on: bool
    power_reserve_w: float | None
    growth: RepeatedTurnOnGrowth
    can_turn_on: bool = True
    can_turn_off: bool = True


@dataclass(frozen=True, slots=True)
class Waiting:
    """A waiting time that runs before the step may be turned on.

    The step is turned on at the first decision at or after `until`.
    """

    key: StepKey
    started_at: datetime
    until: datetime


@dataclass(slots=True)
class RegulationState:
    """What the regulation keeps track of while it runs.

    `appliances_commanded_at` and `chargers_commanded_at` hold when each
    appliance and charger was last sent a command.
    """

    started_at: datetime | None = None
    appliances_on: set[str] = field(default_factory=set)
    current_variants: dict[str, str | None] = field(default_factory=dict)
    excluded_appliances: frozenset[str] = frozenset()
    waiting: Waiting | None = None
    repeats: RepeatedTurnOnCounter = field(default_factory=RepeatedTurnOnCounter)
    penalty: PenaltyState = field(default_factory=PenaltyState)
    safe_state: bool = False
    charging_groups: dict[str, ChargingState] = field(default_factory=dict)
    appliances_commanded_at: dict[str, datetime] = field(default_factory=dict)
    chargers_commanded_at: dict[str, datetime] = field(default_factory=dict)


@dataclass(slots=True)
class OverrideChanges:
    """The chargers whose window override arms or ends at a decision."""

    armed: list[str] = field(default_factory=list)
    ended: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DecisionResult:
    """The commands of a decision, and the window overrides that arm or end."""

    commands: list[Command]
    overrides: OverrideChanges = field(default_factory=OverrideChanges)
