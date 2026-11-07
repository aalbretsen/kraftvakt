"""The regulation engine that makes each decision (4.2)."""

from __future__ import annotations

from collections.abc import Hashable, Iterator, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from itertools import islice
from typing import Final

from ..config_model import KraftvaktConfig
from .model import (
    ApplianceSlotKey,
    Command,
    DecisionInput,
    RegulationState,
    Slot,
    TurnOffAppliance,
    TurnOnAppliance,
    Waiting,
)
from .penalty import PenaltyLimits, PenaltyOutcome, PenaltyState
from .priority import build_slots, current_variant
from .waiting import waiting_time

# Kept apart so it can change without changing the rest of the regulation (REG-004).
SLOTS_PER_DECISION: Final = 1


class RegulationEngine:
    """Decides which appliances are on, in priority order (REG, STR, APP-007, APP-009).

    The engine only knows what it has told the appliances to do (GEN-006) and
    keeps its state only while it runs (GEN-007). The configuration cannot
    change while the regulation runs (REG-010), so it is given once.
    """

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create a stopped engine for the configuration."""
        self._config = config
        self._running = False
        self._state = RegulationState()

    @property
    def running(self) -> bool:
        """Return whether the regulation runs."""
        return self._running

    @property
    def started_at(self) -> datetime | None:
        """Return when the regulation last started, or None while stopped."""
        return self._state.started_at

    @property
    def appliances_on(self) -> frozenset[str]:
        """Return the ids of the appliances the regulation has turned on."""
        return frozenset(self._state.appliances_on)

    @property
    def current_variants(self) -> Mapping[str, str | None]:
        """Return the current variant of each appliance, None for the appliance."""
        return dict(self._state.current_variants)

    @property
    def waiting(self) -> Waiting | None:
        """Return the waiting time that runs for the next slot, if any."""
        return self._state.waiting

    @property
    def safe_state(self) -> bool:
        """Return whether the regulation is in the safe state (REG-011)."""
        return self._state.safe_state

    @property
    def penalty(self) -> PenaltyState:
        """Return a copy of the overconsumption state and the penalty period."""
        return replace(self._state.penalty)

    def start(self, now: datetime) -> list[Command]:
        """Start the regulation with a new state and everything off (REG-009)."""
        self._running = True
        self._state = RegulationState(started_at=now)
        return self._turn_off_everything()

    def stop(self) -> list[Command]:
        """Stop the regulation and turn everything off (REG-016)."""
        self._running = False
        self._state = RegulationState()
        return self._turn_off_everything()

    def decide(self, decision: DecisionInput) -> list[Command]:
        """Make one decision and return the commands to carry out (REG-003).

        The steps follow 4.2. The charging window override and the chargers
        (steps 2, 5 and 6) belong to phase 6. The regulation starts again when
        the power sensor is back after the safe state (REG-011) and when a
        penalty ends (STR-008). While a penalty lasts, the current variants are
        still found (APP-007), but nothing is turned on (STR-003).
        """
        if not self._running:
            return []
        if self._state.safe_state:
            return self.start(decision.now) if decision.power_sensor_valid else []
        if decision.power_sensor_lost:
            self._state.safe_state = True
            return self._hold_everything_off()
        average = decision.regulation_average_kw
        if average is None:
            return []
        penalty = self._decide_penalty(decision)
        if penalty is PenaltyOutcome.ENDED:
            return self.start(decision.now)
        commands = (
            self._hold_everything_off() if penalty is PenaltyOutcome.STARTED else []
        )
        commands += self._switch_variants(decision.variant_conditions)
        if self._state.penalty.active:
            return commands
        if average > self._config.general.power_limit_kw:
            return commands + self._switch_off_above_limit()
        return commands + self._turn_on_next(decision.now, average)

    def _turn_off_everything(self) -> list[Command]:
        return [TurnOffAppliance(appliance.id) for appliance in self._config.appliances]

    def _decide_penalty(self, decision: DecisionInput) -> PenaltyOutcome:
        """Count the overconsumption and decide on the penalty (STR-001 to STR-009)."""
        if decision.capacity_average_kw is None:
            return PenaltyOutcome.NONE
        general = self._config.general
        limits = PenaltyLimits(
            power_limit_kw=general.power_limit_kw,
            threshold_kw=general.penalty_threshold_kw,
            window=timedelta(seconds=general.regulation_window_s),
        )
        return self._state.penalty.decide(
            limits, decision.capacity_average_kw, decision.regulation_averages_kw
        )

    def _hold_everything_off(self) -> list[Command]:
        """Turn everything off at once in a penalty or the safe state.

        This is an exception from one slot per decision (REG-004, STR-003,
        REG-011).
        """
        self._state.appliances_on.clear()
        self._state.waiting = None
        return self._turn_off_everything()

    def _switch_variants(self, variant_conditions: Mapping[str, bool]) -> list[Command]:
        """Find the current variants and handle the appliances that switch (APP-009).

        An appliance that switches is off afterwards, in the place of its new
        variant. If it was off and its new place is above the lowest slot that
        is on, that slot is switched off to make room. Several appliances that
        switch at once are handled one by one from the highest new place (T22).
        These switch-offs are exceptions from one slot per decision (REG-004).
        """
        previous = self._state.current_variants
        self._state.current_variants = {
            appliance.id: current_variant(appliance, variant_conditions)
            for appliance in self._config.appliances
        }
        switching = [
            appliance_id
            for appliance_id, variant in self._state.current_variants.items()
            if appliance_id in previous and previous[appliance_id] != variant
        ]
        was_on = self._state.appliances_on & set(switching)
        places = {slot.key: place for place, slot in enumerate(self._slots())}
        commands: list[Command] = []
        for key in sorted(
            map(ApplianceSlotKey, switching), key=lambda key: places[key]
        ):
            if key.appliance_id in was_on:
                if key.appliance_id in self._state.appliances_on:
                    commands += self._switch(key, turn_on=False)
            else:
                lowest_on = next(self._slots_on_lowest_first(), None)
                if lowest_on is not None and places[key] < places[lowest_on.key]:
                    commands += self._switch(lowest_on.key, turn_on=False)
            self._forget_waiting(key)
            self._state.cycling.reset(key)
        return commands

    def _slots(self) -> list[Slot]:
        return build_slots(
            self._config, self._state.current_variants, self._state.appliances_on
        )

    def _slots_on_lowest_first(self) -> Iterator[Slot]:
        """Return the slots the regulation may switch off, lowest priority first."""
        return (
            slot for slot in reversed(self._slots()) if slot.is_on and slot.can_turn_off
        )

    def _switch_off_above_limit(self) -> list[Command]:
        """Switch off the lowest priority slots that are on (REG-008)."""
        self._state.waiting = None
        commands: list[Command] = []
        for slot in list(islice(self._slots_on_lowest_first(), SLOTS_PER_DECISION)):
            commands += self._switch(slot.key, turn_on=False)
        return commands

    def _turn_on_next(self, now: datetime, average_kw: float) -> list[Command]:
        """Turn on the next slots in fixed priority order after waiting.

        Only the first slot that is off can be turned on (REG-007), and only
        when there is room for it (REG-006) and its waiting time has passed
        (REG-012). A waiting time for any other slot is cancelled.
        """
        commands: list[Command] = []
        for _ in range(SLOTS_PER_DECISION):
            candidate = next(
                (slot for slot in self._slots() if not slot.is_on and slot.can_turn_on),
                None,
            )
            if candidate is None or not self._may_turn_on(candidate, average_kw):
                self._state.waiting = None
                break
            if not self._has_waited(candidate, now, average_kw):
                break
            commands += self._switch(candidate.key, turn_on=True)
        return commands

    def _may_turn_on(self, slot: Slot, average_kw: float) -> bool:
        """Return whether there is room to turn the slot on (REG-006)."""
        limit_kw = self._config.general.power_limit_kw
        if average_kw >= limit_kw:
            return False
        reserve_kw = slot.power_reserve_kw
        return reserve_kw is None or average_kw + reserve_kw <= limit_kw

    def _has_waited(self, slot: Slot, now: datetime, average_kw: float) -> bool:
        """Start or continue the waiting time for the slot (REG-012 to REG-015).

        The waiting time is calculated again at each decision from the
        average at that decision, unless the slot cycles persistently.
        """
        waiting = self._state.waiting
        if waiting is None or waiting.key != slot.key:
            waiting = self._state.waiting = Waiting(slot.key, now)
        general = self._config.general
        required = waiting_time(
            average_kw,
            general.power_limit_kw,
            timedelta(minutes=general.wait_at_limit_min),
            self._state.cycling.upcoming_reon_number(slot.key),
            slot.cycling,
        )
        return now - waiting.started_at >= required

    def _forget_waiting(self, key: Hashable) -> None:
        if self._state.waiting is not None and self._state.waiting.key == key:
            self._state.waiting = None

    def _switch(self, key: Hashable, turn_on: bool) -> list[Command]:
        """Return the commands that switch the slot and record it as switched."""
        self._forget_waiting(key)
        self._state.cycling.record(key, turn_on)
        if not isinstance(key, ApplianceSlotKey):
            raise TypeError(f"Unknown slot {key!r}")
        if turn_on:
            self._state.appliances_on.add(key.appliance_id)
            return [TurnOnAppliance(key.appliance_id)]
        self._state.appliances_on.discard(key.appliance_id)
        return [TurnOffAppliance(key.appliance_id)]
