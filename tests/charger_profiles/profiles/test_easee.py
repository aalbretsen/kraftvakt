"""Easee with the Easee integration from HACS (nordicopen/easee_hass), the charger's device with every entity enabled.

The entities are named by translation keys, so the names follow the language; the test harness is in English.
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


async def test_easee_is_switched_by_its_access_level_and_charges_by_its_power_sensor(hass: HomeAssistant, command: Command) -> None:
    device_id = register(hass, EASEE)

    result = await charger_profile(command, device_id)

    assert result["profile"] == "Easee"
    fields = dict(result["fields"])
    car_connected = fields.pop("car_connected")
    assert fields == {
        "entity_id": "switch.garage_charger_enabled",
        "activate": {"mode": "custom", "action": [service("set_charger_access", access_level="open_for_all")]},
        "deactivate": {"mode": "custom", "action": [service("set_charger_access", access_level="whitelist")]},
        "set_current": {"mode": "custom", "action": [service("set_charger_dynamic_limit", current="{{ current }}")]},
        "actively_charging": {"type": "power_sensor", "value": "sensor.garage_power"},
        "cloud_controlled": True,
    }
    assert car_connected["type"] == "template"
    assert "sensor.garage_status" in car_connected["value"]
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
