"""Data passed in and out of the regulation engine."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from .penalty import PenaltyState
from .waiting import CyclingCounter, CyclingSteps


@dataclass(frozen=True, slots=True)
class DecisionInput:
    """Snapshot of what a decision is based on (REG-003).

    The averages are None until the first regulation window has closed (T2).
    `power_sensor_valid` tells whether the power sensor had a valid measurement
    when the last regulation window closed, and `power_sensor_lost` whether it
    had none when each of the last two windows closed (MAL-006, REG-011, T3).
    `regulation_averages_kw` holds every regulation average computed since the
    previous decision, oldest first (STR-005). `variant_conditions` holds the
    evaluated condition of each variant, keyed by variant id (GEN-009). A
    variant that is missing counts as false.
    """

    now: datetime
    regulation_average_kw: float | None
    capacity_average_kw: float | None
    regulation_averages_kw: Sequence[float]
    power_sensor_valid: bool
    power_sensor_lost: bool
    variant_conditions: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TurnOnAppliance:
    """Run the action that turns the appliance on (APP-002)."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class TurnOffAppliance:
    """Run the action that turns the appliance off (APP-003)."""

    appliance_id: str


type Command = TurnOnAppliance | TurnOffAppliance


@dataclass(frozen=True, slots=True)
class ApplianceSlotKey:
    """Identifies the slot of an appliance, whichever variant is current."""

    appliance_id: str


@dataclass(frozen=True, slots=True)
class Slot:
    """A place in the order the regulation turns things on and off (4.1).

    A slot that cannot be turned on is skipped when looking for the next one to
    turn on (REG-007). A slot that cannot be turned off is skipped when the
    regulation switches off above the limit (REG-008).
    """

    key: Hashable
    is_on: bool
    power_reserve_kw: float | None
    cycling: CyclingSteps
    can_turn_on: bool = True
    can_turn_off: bool = True


@dataclass(frozen=True, slots=True)
class Waiting:
    """A waiting time that runs before the slot may be turned on (REG-012)."""

    key: Hashable
    started_at: datetime


@dataclass(slots=True)
class RegulationState:
    """What the regulation keeps track of while it runs (3.5, GEN-007).

    A new state with default values is created at each start (REG-009).
    `current_variants` is empty until the first decision.
    """

    started_at: datetime | None = None
    appliances_on: set[str] = field(default_factory=set)
    current_variants: dict[str, str | None] = field(default_factory=dict)
    waiting: Waiting | None = None
    cycling: CyclingCounter = field(default_factory=CyclingCounter)
    penalty: PenaltyState = field(default_factory=PenaltyState)
    safe_state: bool = False
