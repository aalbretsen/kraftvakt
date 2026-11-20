"""The fixtures the panel's tests read, made from the backend.

The panel mirrors parts of the backend, and its tests use these files, so the two are tested against the same values.
After a change in the backend, write them again with `python -m tests.unit.test_panel_fixtures`, format them with `npm run format` and run the panel's tests.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

from custom_components.kraftvakt.config_model import regulation_window_options
from custom_components.kraftvakt.regulation.charging import ChargerState
from custom_components.kraftvakt.regulation.waiting import RepeatedTurnOnGrowth, WaitingCurve, repeated_turn_on_waiting_time
from custom_components.kraftvakt.sensor import CHARGER_STATE_ICONS
from custom_components.kraftvakt.websocket_api import capabilities

FIXTURES = Path(__file__).parents[2] / "frontend" / "test" / "fixtures"


def waiting() -> dict[str, Any]:
    utilizations = [0, 0.5, 0.55, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1, 1.2]
    wait_at_limit_s, increment_factor, increments = 300, 0.5, 4
    growth = RepeatedTurnOnGrowth.from_waiting_at_limit(wait_at_limit_s, increment_factor, increments)
    return {
        "curves": [
            {
                "steepness": steepness,
                "pivot": pivot,
                "shares": [[utilization, WaitingCurve.from_settings(steepness, pivot).share(utilization)] for utilization in utilizations],
            }
            for steepness, pivot in [(1.5, 50), (6.0, 80), (9.0, 99), (1.5, 99)]
        ],
        "repeated_turn_on": {
            "wait_at_limit_s": wait_at_limit_s,
            "increment_factor": increment_factor,
            "increments": increments,
            "waiting_s": [[repeat + 1, repeated_turn_on_waiting_time(repeat, timedelta(seconds=wait_at_limit_s), growth).total_seconds()] for repeat in range(2, 9)],
        },
    }


def regulation_window() -> dict[str, Any]:
    return {"options": [[interval_s, regulation_window_options(interval_s)] for interval_s in [1, 2, 2.5, 3, 3.3, 10, 15, 60, 130]]}


def charger_states() -> dict[str, Any]:
    return {state.value: CHARGER_STATE_ICONS[state]._asdict() for state in ChargerState}


def panel_fixtures() -> dict[str, Any]:
    return {
        "capabilities.json": capabilities(),
        "waiting.json": waiting(),
        "regulation_window.json": regulation_window(),
        "charger_states.json": charger_states(),
    }


@pytest.mark.parametrize("name", panel_fixtures())
def test_panel_fixture_matches_backend(name: str) -> None:
    assert json.loads((FIXTURES / name).read_text()) == panel_fixtures()[name]


if __name__ == "__main__":
    for name, content in panel_fixtures().items():
        (FIXTURES / name).write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n")
