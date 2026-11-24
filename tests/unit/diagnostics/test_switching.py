"""The changes of the recorded history and their report, with diagnostics built as dictionaries."""

from datetime import datetime, timedelta
from typing import Any

import pytest

from diagnostics.diagnostics_file import DiagnosticsFile, NotADiagnosticsFileError
from diagnostics.switching.changes import entity_changes, history_changes
from diagnostics.switching.report import report_text

START = datetime.fromisoformat("2026-11-23T10:00:00+01:00")


def states(*values: str | None, minutes: list[int] | None = None, attributes: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Return a state a minute, or at the given minutes after the start, with the attributes if given."""
    return [
        {"time": (START + timedelta(minutes=minute)).isoformat(), "state": value, **({} if attributes is None else {"attributes": attributes[index]})}
        for index, (minute, value) in enumerate(zip(minutes or range(len(values)), values, strict=True))
    ]


def test_a_number_counts_increases_decreases_and_reversals() -> None:
    changes = entity_changes("number.current", ("set_current",), states("6", "7", "7", "8", "7", "8.0", "9"))

    assert (changes.changes, changes.increases, changes.decreases, changes.reversals) == (5, 4, 1, 2)
    assert changes.changes_to is None


def test_other_states_count_the_changes_to_each_state() -> None:
    changes = entity_changes("switch.charger", ("controlled_entity",), states("off", "on", "off", "on", "on"))

    assert changes.changes == 3
    assert changes.changes_to == {"on": 2, "off": 1}
    assert (changes.increases, changes.decreases, changes.reversals) == (None, None, None)


def test_lost_values_are_counted_once_and_left_out_of_the_changes() -> None:
    changes = entity_changes("switch.charger", (), states("on", "unavailable", "unknown", "on", None, "off"))

    assert changes.lost_values == 2
    assert changes.changes == 1


def test_the_shortest_hold_is_between_two_changes() -> None:
    changes = entity_changes("switch.charger", (), states("off", "on", "off", "on", minutes=[0, 30, 32, 50]))

    assert changes.shortest_hold == timedelta(minutes=2)


def test_the_busiest_hour_has_the_most_changes_and_is_the_first_on_a_tie() -> None:
    busiest = entity_changes("switch.charger", (), states("off", "on", "off", "on", "off", minutes=[0, 10, 70, 80, 130]))
    tie = entity_changes("switch.charger", (), states("off", "on", "off", minutes=[0, 10, 70]))

    assert busiest.busiest_hour == (START + timedelta(hours=1), 2)
    assert tie.busiest_hour == (START, 1)


def test_the_attributes_count_each_attribute_that_changed() -> None:
    attributes = [{"temperature": 22, "current_temperature": 20}, {"temperature": 8, "current_temperature": 20}, {"temperature": 8}, {"temperature": 8}]

    changes = entity_changes("climate.floor", (), states("heat", "heat", "heat", "unavailable", attributes=attributes))

    assert changes.changes == 0
    assert changes.attribute_changes == {"temperature": 1, "current_temperature": 1}


def test_an_entity_without_states_has_no_changes() -> None:
    changes = entity_changes("sensor.power", (), [])

    assert (changes.recorded, changes.changes, changes.increases, changes.changes_to, changes.shortest_hold, changes.busiest_hour) == (False, 0, None, {}, None, None)


def diagnostics(entities: dict[str, Any]) -> DiagnosticsFile:
    config = {
        "appliances": [{"id": "a", "entity_id": "switch.heater"}, {"id": "b"}],
        "charger_groups": [{"id": "g", "name": "Garage", "chargers": [{"id": "c", "switched_by": "current"}]}],
    }
    history = {"start": START.isoformat(), "end": (START + timedelta(hours=24)).isoformat(), "entities": entities}
    return DiagnosticsFile({"data": {"config": config, "history": history}})


def test_each_entity_is_under_each_item_that_uses_it() -> None:
    shared = {"uses": [{"item": "a", "field": "variants.v.condition"}, {"item": "c", "field": "car_connected"}, {"item": "c", "field": "fault_flag"}], "states": []}
    removed = {"uses": [{"item": "gone", "field": "controlled_entity"}], "states": []}

    history = history_changes(diagnostics({"binary_sensor.shared": shared, "switch.old": removed}))

    assert [item.label for item in history.items] == [
        "Power sensor and regulation",
        "Appliance switch.heater",
        "Appliance b",
        "EV charger c in Garage",
        "Removed item gone",
    ]
    assert [entity.fields for item in history.items for entity in item.entities] == [("variants.v.condition",), ("car_connected", "fault_flag"), ("controlled_entity",)]
    assert history.start == START


def test_a_file_without_history_or_configuration_is_refused() -> None:
    with pytest.raises(NotADiagnosticsFileError, match="no recorded history"):
        history_changes(DiagnosticsFile({"data": {"config": {}}}))
    with pytest.raises(NotADiagnosticsFileError, match="no Kraftvakt configuration"):
        history_changes(DiagnosticsFile({"data": {}}))
    with pytest.raises(NotADiagnosticsFileError, match="cannot be read"):
        history_changes(DiagnosticsFile({"data": {"config": {"appliances": "not a list"}}}))


def test_the_report_has_a_table_per_item_with_the_states_and_attributes_under_their_entity() -> None:
    climate = {
        "uses": [{"item": "a", "field": "controlled_entity"}],
        "states": states("heat", "off", "heat", attributes=[{"temperature": 22}, {"temperature": 8}, {"temperature": 8}]),
    }

    report = report_text(history_changes(diagnostics({"climate.floor": climate, "binary_sensor.car": {"uses": [{"item": "c", "field": "car_connected"}], "states": []}})))

    assert report.splitlines()[:6] == [
        "Recorded history from 2026-11-23 10:00 to 2026-11-24 10:00",
        "",
        "Power sensor and regulation",
        "  entity  fields  changes  up  down  reversals  shortest hold  busiest hour  lost values",
        "",
        "Appliance switch.heater",
    ]
    assert report.splitlines()[6:10] == [
        "  entity         fields             changes  up  down  reversals  shortest hold  busiest hour          lost values",
        "  climate.floor  controlled_entity  2        -   -     -          60 s           2026-11-23 10:00 (2)  0",
        "    changes to: off 1, heat 1",
        "    attributes changed: temperature 1",
    ]
    assert report.splitlines()[-1] == "    no recorded states: the recorder leaves it out, or it did not exist"
