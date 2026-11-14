"""Amina S with Zigbee2MQTT (the definition "amina S" in zigbee-herdsman-converters) and its Home Assistant discovery.

Zigbee2MQTT names the entities in English in every language. The on/off switch is the main entity of the device, without a name of its own.
"""

from homeassistant.core import HomeAssistant

from ..conftest import Command, Device, DeviceEntity, charger_profile, register, save_charger

AMINA_S = Device(
    integration="mqtt",
    name="Amina",
    manufacturer="Amina Distribution AS",
    model_id="amina S",
    entities=[
        DeviceEntity("switch", None),
        DeviceEntity("number", "Charge limit"),
        DeviceEntity("number", "Charge limit with on off"),
        DeviceEntity("number", "Time to offline"),
        DeviceEntity("number", "Offline current"),
        DeviceEntity("switch", "Single phase"),
        DeviceEntity("switch", "Enable offline"),
        DeviceEntity("switch", "Offline single phase"),
        DeviceEntity("binary_sensor", "Ev connected"),
        DeviceEntity("binary_sensor", "Charging"),
        DeviceEntity("binary_sensor", "Derated"),
        DeviceEntity("binary_sensor", "Alarm active"),
        DeviceEntity("sensor", "Ev status"),
        DeviceEntity("sensor", "Alarms"),
        DeviceEntity("sensor", "Hardware current limit"),
        DeviceEntity("sensor", "Total active power"),
        DeviceEntity("sensor", "Total active energy"),
        DeviceEntity("sensor", "Power"),
        DeviceEntity("sensor", "Current"),
        DeviceEntity("sensor", "Voltage"),
        DeviceEntity("sensor", "Linkquality", disabled=True),
        DeviceEntity("update", None),
    ],
)


async def test_amina_s_has_entities_for_every_field(hass: HomeAssistant, command: Command) -> None:
    device_id = register(hass, AMINA_S)

    result = await charger_profile(command, device_id)

    assert result == {
        "profile": "Amina S (Zigbee2MQTT)",
        "fields": {
            "entity_id": "switch.amina",
            "activate": {"mode": "default"},
            "deactivate": {"mode": "default"},
            "set_current": {"mode": "entity", "entity_id": "number.amina_charge_limit"},
            "car_connected": {"type": "entity", "value": "binary_sensor.amina_ev_connected"},
            "actively_charging": {"type": "entity", "value": "binary_sensor.amina_charging"},
        },
    }
    saved = await save_charger(command, device_id, result["fields"])
    assert saved["saved"]
    assert [issue for issue in saved["missing"] if issue["section"] == "chargers"] == []
