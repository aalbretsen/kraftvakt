"""Easee with the Easee integration from HACS (nordicopen/easee_hass), the charger's device with every entity enabled.

The entities are named by translation keys, so the names follow the language; the test harness is in English.
The status sensor maps the charger's operating mode; the integration has no entity for its error codes, so a fault is read from the status.
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from ..conftest import Command, Device, DeviceEntity, charger_profile, register, save_charger

EASEE = Device(
    integration="easee",
    name="Garage",
    manufacturer="Easee",
    entities=[
        DeviceEntity("sensor", "Status", "easee_status"),
        DeviceEntity("sensor", "Power", "power"),
        DeviceEntity("sensor", "Session Energy", "session_energy"),
        DeviceEntity("sensor", "Lifetime energy", "lifetime_energy"),
        DeviceEntity("sensor", "Output limit", "output_limit"),
        DeviceEntity("sensor", "Current", "current"),
        DeviceEntity("sensor", "Dynamic charger limit", "dynamic_charger_limit"),
        DeviceEntity("sensor", "Max charger limit", "max_charger_limit"),
        DeviceEntity("sensor", "Voltage", "voltage"),
        DeviceEntity("sensor", "Reason for no current", "easee_reason_no_current"),
        DeviceEntity("binary_sensor", "Cable lock", "cable_locked"),
        DeviceEntity("binary_sensor", "Online", "online"),
        DeviceEntity("switch", "Smart charging", "smart_charging"),
        DeviceEntity("switch", "Touch button enabled", "smart_button"),
        DeviceEntity("switch", "Cable locked permanently", "cable_locked_permanently"),
        DeviceEntity("switch", "Charger enabled", "is_enabled"),
        DeviceEntity("switch", "Idle current", "idle_current"),
        DeviceEntity("light", "LED strip", "led_strip"),
        DeviceEntity("button", "Override schedule", "override_schedule"),
    ],
)


def service(name: str, **data: str) -> dict:
    return {"action": f"easee.{name}", "data": {"device_id": "{{ device_id(entity_id) }}", **data}}


async def test_easee_is_switched_by_its_access_level_charges_by_its_power_sensor_and_is_done_or_has_a_fault_by_its_status(hass: HomeAssistant, command: Command) -> None:
    device_id = register(hass, EASEE)

    result = await charger_profile(command, device_id)

    assert result["profile"] == "Easee"
    fields = dict(result["fields"])
    car_connected = fields.pop("car_connected")
    done_flag = fields.pop("done_flag")
    fault_flag = fields.pop("fault_flag")
    assert fields == {
        "entity_id": "switch.garage_charger_enabled",
        "activate": {"mode": "custom", "action": [service("set_charger_access", access_level="open_for_all")]},
        "deactivate": {"mode": "custom", "action": [service("set_charger_access", access_level="whitelist")]},
        "set_current": {"mode": "custom", "action": [service("set_charger_dynamic_limit", current="{{ current }}")]},
        "charging_power": {"type": "power_sensor", "value": "sensor.garage_power"},
        "cloud_controlled": True,
        "deactivate_on_fault": True,
    }
    assert car_connected["type"] == "template"
    assert "sensor.garage_status" in car_connected["value"]
    assert done_flag["type"] == fault_flag["type"] == "template"
    assert "sensor.garage_status" in done_flag["value"]
    assert "sensor.garage_status" in fault_flag["value"]
    saved = await save_charger(command, device_id, result["fields"])
    assert saved["saved"]
    assert [issue for issue in saved["missing"] if issue["section"] == "chargers"] == []


async def test_easee_car_is_connected_by_its_status(hass: HomeAssistant, command: Command) -> None:
    """An unknown status gives no value, so an override that ends when the car leaves is not ended by a cloud service that is down."""
    device_id = register(hass, EASEE)
    template = Template((await charger_profile(command, device_id))["fields"]["car_connected"]["value"], hass)

    for status, connected in [("charging", True), ("awaiting_authorization", True), ("completed", True), ("disconnected", False), ("offline", None)]:
        hass.states.async_set("sensor.garage_status", status)
        assert template.async_render(parse_result=True) == connected, status


async def test_easee_is_done_by_its_status(hass: HomeAssistant, command: Command) -> None:
    """A status that is not known gives no value, so a cloud service that is down does not make a car that is not full done."""
    device_id = register(hass, EASEE)
    template = Template((await charger_profile(command, device_id))["fields"]["done_flag"]["value"], hass)

    for status, done in [("completed", True), ("charging", False), ("awaiting_start", False), ("disconnected", False), ("offline", None), ("unavailable", None)]:
        hass.states.async_set("sensor.garage_status", status)
        assert template.async_render(parse_result=True) == done, status


async def test_easee_has_a_fault_by_its_status(hass: HomeAssistant, command: Command) -> None:
    """The error states of the charger, and an erratic car, so the user sees why it does not charge. A status that is not known is no fault."""
    device_id = register(hass, EASEE)
    fault_flag = (await charger_profile(command, device_id))["fields"]["fault_flag"]
    template = Template(fault_flag["value"], hass)

    faults = ["error", "error_temperature_too_high", "error_dead_powerboard", "error_overcurrent", "error_pen_fault", "erratic_ev"]
    for status in [*faults, "charging", "disconnected", "awaiting_authorization", "offline", "unknown 162", "unavailable"]:
        hass.states.async_set("sensor.garage_status", status)
        assert template.async_render(parse_result=True) is (status in faults), status
