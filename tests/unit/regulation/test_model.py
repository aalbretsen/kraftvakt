"""Tests of the commands the engine returns."""

from custom_components.kraftvakt.regulation.model import (
    ActivateCharger,
    DeactivateCharger,
    SetChargingCurrent,
    TurnOffAppliance,
    TurnOnAppliance,
    without_superseded,
)

from .scenario import activate, current, deactivate


def test_appliance_keeps_its_last_command() -> None:
    commands = [TurnOffAppliance("a"), TurnOnAppliance("b"), TurnOnAppliance("a", "eco")]

    assert without_superseded(commands) == [TurnOnAppliance("b"), TurnOnAppliance("a", "eco")]


def test_charger_keeps_only_its_last_current_without_activation_change() -> None:
    assert without_superseded(current("c", 7) + current("c", 8) + current("c", 7)) == current("c", 7)


def test_charger_keeps_its_last_activation_change_with_the_currents_around_it() -> None:
    commands = deactivate("c") + activate("c") + current("c", 7) + current("c", 8)

    assert without_superseded(commands) == activate("c") + current("c", 8)


def test_charger_activated_and_deactivated_is_only_deactivated() -> None:
    assert without_superseded(activate("c") + current("c", 7) + deactivate("c")) == deactivate("c")


def test_order_between_appliances_and_chargers_is_kept() -> None:
    commands = [
        SetChargingCurrent("b", 6),
        DeactivateCharger("b"),
        SetChargingCurrent("a", 6),
        ActivateCharger("a"),
        TurnOffAppliance("x"),
    ]

    assert without_superseded(commands) == commands
