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
    OverrideChanges,
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
    return [SetChargingCurrent(charger_id, min_a), ActivateCharger(charger_id)]


def deactivate(charger_id: str, min_a: int = 6) -> list[Command]:
    return [SetChargingCurrent(charger_id, min_a), DeactivateCharger(charger_id)]


def current(charger_id: str, current_a: int) -> list[Command]:
    return [SetChargingCurrent(charger_id, current_a)]


class Scenario:
    """Drives a started engine through decisions.

    Every charger reads as idle with a car connected until the test changes it
    with `set_charger` or `draw`, and only the appliances in `excluded` are
    excluded until the test changes it with `exclude`.
    """

    def __init__(
        self,
        config: KraftvaktConfig,
        start: datetime = START,
        time_zone: tzinfo = UTC,
        excluded: tuple[str, ...] = (),
    ) -> None:
        self.engine = RegulationEngine(config)
        self.configured_chargers = {charger.id: charger for charger in config.chargers}
        self.drawing: set[str] = set()
        self.now = start
        self.time_zone = time_zone
        self.chargers = {charger.id: ChargerReading(car_connected=True) for charger in config.chargers}
        self.excluded_appliances = frozenset(excluded)
        self.overrides = OverrideChanges()
        self.start_commands = self.engine.start(self.now, self.excluded_appliances)

    def set_charger(self, charger_id: str, **reading: Any) -> None:
        """Change what is read for the charger from now on."""
        self.chargers[charger_id] = replace(self.chargers[charger_id], **reading)

    def draw(self, charger_id: str, drawing: bool = True) -> None:
        """Let the car draw what the current of its charger allows from now on, or stop drawing.

        While it draws, the charger reads as actively charging with a charging
        power of its current times its power reserve divided by its minimum
        current, and as not charging with 0 W while it is deactivated.
        """
        if drawing:
            self.drawing.add(charger_id)
        else:
            self.drawing.discard(charger_id)
            self.set_charger(charger_id, actively_charging=False, charging_power_w=0.0)

    def _readings(self) -> dict[str, ChargerReading]:
        readings = dict(self.chargers)
        for charger_id in self.drawing:
            charger = self.configured_chargers[charger_id]
            current_a = self.engine.chargers[charger_id].current_a
            power_w = 0.0 if current_a is None else current_a * charger.min_current_power_w / charger.min_current_a
            readings[charger_id] = replace(readings[charger_id], actively_charging=current_a is not None, charging_power_w=power_w)
        return readings

    def exclude(self, *appliance_ids: str) -> None:
        """Exclude exactly these appliances from now on."""
        self.excluded_appliances = frozenset(appliance_ids)

    def decide(
        self,
        average_w: float | None,
        *,
        tariff: float = 0.0,
        averages: tuple[float, ...] | None = None,
        after: timedelta = DECISION_INTERVAL,
        true: tuple[str, ...] = (),
        sensor_valid: bool = True,
        sensor_lost: bool = False,
    ) -> list[Command]:
        """Make a decision `after` the previous one.

        `sensor_valid` and `sensor_lost` tell how the power sensor was when the
        last windows closed, by default valid.
        `tariff` is the tariff average, well under the limit unless given.
        `averages` are the regulation averages since the previous decision, by
        default only `average_w`. `true` lists the variants whose conditions
        are true.
        """
        self.now += after
        if averages is None:
            averages = () if average_w is None else (average_w,)
        result = self.engine.decide(
            DecisionInput(
                now=self.now,
                regulation_average_w=average_w,
                tariff_average_w=None if average_w is None else tariff,
                regulation_averages_w=averages,
                power_sensor_valid=sensor_valid,
                power_sensor_lost=sensor_lost,
                variant_conditions=dict.fromkeys(true, True),
                chargers=self._readings(),
                excluded_appliances=self.excluded_appliances,
                time_zone=self.time_zone,
            )
        )
        self.overrides = result.overrides
        return result.commands

    def repeat(self, after: timedelta) -> list[Command]:
        """Repeat the commands that are due `after` the previous decision or repeat.

        The appliances excluded with `exclude` and the chargers read as excluded
        are left out, and the chargers read as without a car are passed as such.
        """
        self.now += after
        return self.engine.repeat_commands(
            self.now,
            self.excluded_appliances,
            frozenset(charger_id for charger_id, reading in self.chargers.items() if reading.excluded),
            frozenset(charger_id for charger_id, reading in self.chargers.items() if reading.car_disconnected),
        )

    def decide_many(
        self,
        average_w: float,
        count: int,
        *,
        tariff: float = 0.0,
        true: tuple[str, ...] = (),
    ) -> list[list[Command]]:
        """Make `count` decisions with the same averages and return their commands."""
        return [self.decide(average_w, tariff=tariff, true=true) for _ in range(count)]

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
