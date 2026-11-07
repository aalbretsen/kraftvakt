"""A small language for scenario tests of the regulation engine.

A scenario starts the engine and lets the test make decisions one regulation
interval apart::

    scenario = Scenario(make_config("a", "b"))
    assert scenario.decide(5.0) == on("a")
"""

from datetime import UTC, datetime, timedelta

from custom_components.kraftvakt.config_model import KraftvaktConfig
from custom_components.kraftvakt.regulation.engine import RegulationEngine
from custom_components.kraftvakt.regulation.model import (
    Command,
    DecisionInput,
    TurnOffAppliance,
    TurnOnAppliance,
)

START = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
DECISION_INTERVAL = timedelta(minutes=1)


def on(*appliance_ids: str) -> list[Command]:
    """Return the commands that turn the appliances on, in the given order."""
    return [TurnOnAppliance(appliance_id) for appliance_id in appliance_ids]


def off(*appliance_ids: str) -> list[Command]:
    """Return the commands that turn the appliances off, in the given order."""
    return [TurnOffAppliance(appliance_id) for appliance_id in appliance_ids]


class Scenario:
    """Drives a started engine through decisions."""

    def __init__(self, config: KraftvaktConfig) -> None:
        """Create the engine and start it at START."""
        self.engine = RegulationEngine(config)
        self.now = START
        self.start_commands = self.engine.start(self.now)

    def decide(
        self,
        average_kw: float | None,
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
        default only `average_kw`. `true` lists the variants whose conditions
        are true.
        """
        self.now += after
        if averages is None:
            averages = () if average_kw is None else (average_kw,)
        return self.engine.decide(
            DecisionInput(
                now=self.now,
                regulation_average_kw=average_kw,
                capacity_average_kw=None if average_kw is None else capacity,
                regulation_averages_kw=averages,
                power_sensor_valid=sensor_valid,
                power_sensor_lost=sensor_lost,
                variant_conditions=dict.fromkeys(true, True),
            )
        )

    def decide_many(
        self,
        average_kw: float,
        count: int,
        *,
        capacity: float = 0.0,
        true: tuple[str, ...] = (),
    ) -> list[list[Command]]:
        """Make `count` decisions with the same averages and return their commands."""
        return [
            self.decide(average_kw, capacity=capacity, true=true) for _ in range(count)
        ]

    def turn_on(self, *appliance_ids: str, true: tuple[str, ...] = ()) -> None:
        """Turn on the appliances with a low average, in priority order.

        Waits as long as needed, so it also works with waiting times.
        """
        expected = list(appliance_ids)
        for _ in range(100):
            if not expected:
                return
            commands = self.decide(0.0, true=true)
            if commands:
                assert commands == on(expected.pop(0))
        raise AssertionError(f"{expected} were never turned on")
