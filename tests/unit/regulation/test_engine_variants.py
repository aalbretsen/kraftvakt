"""Scenario tests for variants of appliances (APP-007, APP-009)."""

from .configs import appliance, make_config
from .scenario import Scenario, on


def morning_heater_config(**settings):
    """The heater has priority over b in the morning, and is last otherwise."""
    return make_config(
        appliance("heater", variants=("morning",)),
        "b",
        priority=("heater:morning", "b", "heater"),
        **settings,
    )


def test_current_variant_decides_the_place() -> None:
    """APP-007: only the entry of the current variant takes part."""
    in_the_morning = Scenario(morning_heater_config(wait_at_limit_min=0))
    otherwise = Scenario(morning_heater_config(wait_at_limit_min=0))

    assert in_the_morning.decide_many(1.0, 2, true=("morning",)) == [
        on("heater"),
        on("b"),
    ]
    assert otherwise.decide_many(1.0, 2) == [on("b"), on("heater")]


def test_current_variant_is_found_at_each_decision() -> None:
    """APP-007, REG-009: no current variant before the first decision."""
    scenario = Scenario(morning_heater_config())
    assert scenario.engine.current_variants == {}

    scenario.decide(None, true=("morning",))
    assert scenario.engine.current_variants == {}

    scenario.decide(1.0)
    assert scenario.engine.current_variants == {"heater": None, "b": None}

    scenario.decide(1.0, true=("morning",))
    assert scenario.engine.current_variants == {"heater": "morning", "b": None}


def test_restart_forgets_the_current_variant() -> None:
    """REG-009: the current variant is found again at the first decision."""
    scenario = Scenario(morning_heater_config())
    scenario.decide(1.0, true=("morning",))

    scenario.engine.start(scenario.now)

    assert scenario.engine.current_variants == {}
