"""A small language for scenario tests of the regulation engine.

A scenario starts the engine and lets the test make decisions one regulation
interval apart::

    scenario = Scenario(make_config("a", "b"))
    assert scenario.decide(5.0) == on("a")
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any

from custom_components.kraftvakt.config_model import KraftvaktConfig
from custom_components.kraftvakt.regulation.charging import ChargerReading
from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import (
    ActivateCharger,
    Command,
    DeactivateCharger,
    DecisionInput,
    ResetWindowOverride,
    SetChargingCurrent,
    TurnOffAppliance,
    TurnOnAppliance,
)

START = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
DECISION_INTERVAL = timedelta(minutes=1)


def on(*appliances: str) -> list[Command]:
    """Return the commands that turn the appliances on, in the given order.

    ``"a"`` is appliance ``a`` as it turns itself on, ``"a:morning"`` as its
    variant ``morning`` does it.
    """
    return [TurnOnAppliance(*_appliance_and_variant(text)) for text in appliances]


def off(*appliances: str) -> list[Command]:
    """Return the commands that turn the appliances off, written as for `on`."""
    return [TurnOffAppliance(*_appliance_and_variant(text)) for text in appliances]


def _appliance_and_variant(text: str) -> tuple[str, str | None]:
    appliance_id, _, variant_id = text.partition(":")
    return appliance_id, variant_id or None


def activate(charger_id: str, min_a: int = 6) -> list[Command]:
    """Return the commands that activate the charger."""
    return [SetChargingCurrent(charger_id, min_a), ActivateCharger(charger_id)]


def deactivate(charger_id: str, min_a: int = 6) -> list[Command]:
    """Return the commands that deactivate the charger."""
    return [SetChargingCurrent(charger_id, min_a), DeactivateCharger(charger_id)]


def current(charger_id: str, current_a: int) -> list[Command]:
    """Return the command that sets the charging current."""
    return [SetChargingCurrent(charger_id, current_a)]


def reset_override(charger_id: str) -> list[Command]:
    """Return the command that switches off the window override."""
    return [ResetWindowOverride(charger_id)]


IDLE_CHARGER = ChargerReading(actively_charging=False)


class Scenario:
    """Drives a started engine through decisions.

    Every charger reads as idle with a valid charging power until the test
    changes it with `set_charger`, and no appliance is excluded until the test
    changes it with `exclude`.
    """

    def __init__(
        self,
        config: KraftvaktConfig,
        start: datetime = START,
        time_zone: tzinfo = UTC,
    ) -> None:
        """Create the engine and start it at `start`."""
        self.engine = RegulationEngine(config)
        self.now = start
        self.time_zone = time_zone
        self.chargers = {
            charger.id: IDLE_CHARGER for charger in config.charging.chargers
        }
        self.excluded_appliances: frozenset[str] = frozenset()
        self.start_commands = self.engine.start(self.now)

    def set_charger(self, charger_id: str, **reading: Any) -> None:
        """Change what is read for the charger from now on."""
        self.chargers[charger_id] = replace(self.chargers[charger_id], **reading)

    def exclude(self, *appliance_ids: str) -> None:
        """Exclude exactly these appliances from now on."""
        self.excluded_appliances = frozenset(appliance_ids)

    def decide(
        self,
        average_w: float | None,
        *,
        capacity: float = 0.0,
        averages: tuple[float, ...] | None = None,
        after: timedelta = DECISION_INTERVAL,
        true: tuple[str, ...] = (),
        sensor_valid: bool = True,
        sensor_lost: bool = False,
    ) -> list[Command]:
        """Make a decision `after` the previous one.

        `sensor_valid` and `sensor_lost` tell how the power sensor was when the
        last windows closed, by default valid.
        `capacity` is the capacity average, well under the limit unless given.
        `averages` are the regulation averages since the previous decision, by
        default only `average_w`. `true` lists the variants whose conditions
        are true.
        """
        self.now += after
        if averages is None:
            averages = () if average_w is None else (average_w,)
        return self.engine.decide(
            DecisionInput(
                now=self.now,
                regulation_average_w=average_w,
                capacity_average_w=None if average_w is None else capacity,
                regulation_averages_w=averages,
                power_sensor_valid=sensor_valid,
                power_sensor_lost=sensor_lost,
                variant_conditions=dict.fromkeys(true, True),
                chargers=dict(self.chargers),
                excluded_appliances=self.excluded_appliances,
                time_zone=self.time_zone,
            )
        )

    def decide_many(
        self,
        average_w: float,
        count: int,
        *,
        capacity: float = 0.0,
        true: tuple[str, ...] = (),
    ) -> list[list[Command]]:
        """Make `count` decisions with the same averages and return their commands."""
        return [
            self.decide(average_w, capacity=capacity, true=true) for _ in range(count)
        ]

    def turn_on(self, *appliance_ids: str, true: tuple[str, ...] = ()) -> None:
        """Turn on the appliances with a low average, in priority order.

        Waits as long as needed, so it also works with waiting times.
        """
        expected = list(appliance_ids)
        for _ in range(100):
            if not expected:
                return
            commands = self.decide(0, true=true)
            if commands:
                assert commands == on(expected.pop(0))
        raise AssertionError(f"{expected} were never turned on")

    def charge(self, charger_id: str, amperes: int, *, average_w: float = 0.0) -> None:
        """Decide until the charger has its current set to `amperes`.

        Waits as long as needed, so it also works with waiting times. Other
        commands are allowed on the way.
        """
        for _ in range(200):
            status = self.engine.chargers[charger_id]
            if status.current_a == amperes:
                return
            self.decide(average_w)
        raise AssertionError(f"{charger_id} never got {amperes} A")
