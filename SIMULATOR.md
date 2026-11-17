# Kraftvakt simulator

The simulator makes it possible to test Kraftvakt without a HAN port and real appliances. It is a separate integration, **Kraftvakt simulator**,
in `simulator/custom_components/kraftvakt_simulator/`, with its tests in `tests/simulator/` and `tests/unit/simulator/`. It is outside `custom_components/`,
so HACS does not install it, and it is only used with a local Home Assistant, see [Local Home Assistant](README.md#local-home-assistant). It is not part of a release.

Add the integration under **Settings → Devices & services**, and add one device at a time with **Add device**:

- **HAN:** the power of the house, the background power plus the power of all the simulated devices (`sensor.han_power` when the device is named «HAN»).
  It reports every 10 seconds, also when the power has not changed, as a HAN reader does. There can be only one HAN.
- **Heating device:** heating cable, water heater or panel heater, with power (W), duty cycle (0–100 %) and period (minutes). It has a switch and a power sensor.
  While the switch is on, it heats in a fixed cycle that starts with the on part: 750 W, 25 % and 60 minutes give 15 minutes on and 45 minutes off, over and over.
  The cycle starts again every time the switch is turned on or the cycle is changed. With the switch off, it uses nothing.
  It has the sensor **Temperature**, of the water or the floor, set with the number **Temperature** under Configuration (20 °C by default);
  it does not change by itself.
- **Thermostat:** a heating device controlled by a thermostat, with the same power, duty cycle and period, the HVAC modes it supports (off, heat and auto by default,
  at least one heating mode) and a room temperature (5 °C by default). Its climate entity has the chosen modes and a target temperature.
  In heat, heat/cool and auto it heats in the cycle while the target temperature is above the room temperature; otherwise it uses nothing.
  The cycle starts again every time it starts heating. Turning it on returns it to the last heating mode, the first heating mode it supports at first.
  It can only be turned off when off is one of its modes. It starts in off, or in its first mode when off is not one of them.
  It has the sensor **Floor temperature**, set with the number **Floor temperature** under Configuration (20 °C by default),
  so a thermostat's own temperatures and a floor sensor can be shown together.
- **EV charger:** three-phase 400 V with a minimum and maximum current. It has the switches **Charging allowed**, **Car connected**, **Car fully charged** and **Fault**,
  **Charging current** (A), the sensor **Charging power**, the binary sensor **Charging**, on while it draws power,
  and the sensor **Status**: disconnected, awaiting start, starting, charging, completed or error, and unavailable while it is unplugged.
  It draws √3 × 400 V × the charging current (6 A gives 4.16 kW) when charging is allowed, a car is connected, the car is not fully charged and it has no fault.
  The charging current goes from 0 A to the maximum, and below the minimum it is 0 A and the charger does not charge,
  so an EV charger whose charging is turned on and off by the charging current can be tested.
  Use **Fault** as a fault flag of an EV charger in Kraftvakt with **Deactivate on fault**.
  Use **Status** with the state completed as the done flag, and turn it unavailable with **Unplugged** to test a done flag that gives no answer.
  With a **Start delay** (0 s by default), the car waits that long before it draws power each time it may start charging,
  as with a charger controlled through a cloud service; set the same or a longer start delay on a cloud-controlled EV charger in Kraftvakt.

Heating devices, thermostats and EV chargers also have the switch **Unplugged**. While it is on, the device uses nothing, whatever the other switches are set to.
The cycle of a heating device runs on while it is unplugged.

What controls the simulation and does not belong to a real device is under **Configuration** on the device page, and can be changed while Home Assistant runs:
**Background power**, **Heating power**, **Duty cycle**, **Period**, **Room temperature**, **Temperature**, **Floor temperature**,
**Car connected**, **Car fully charged**, **Fault** and **Unplugged**.
The settings can be changed with **Reconfigure**.
The switches, the charging current, and the mode and target temperature of a thermostat keep their state over a restart.

Then set up Kraftvakt against the simulator: the power sensor of the HAN as the power sensor, the switches of the heating devices and the thermostats as appliances,
and for each EV charger, filled in by hand (the entity IDs follow the language of Home Assistant when the device is added):

| Field in Kraftvakt | Value |
|---|---|
| Device | The EV charger device |
| Charger entity | `switch.<charger>_charging_allowed` |
| Activate and Deactivate | Standard |
| Set charging current | Entity: `number.<charger>_charging_current` |
| Actively charging | Charging on/off: `binary_sensor.<charger>_charging`, or the state `charging` of `sensor.<charger>_status`; charging power: `sensor.<charger>_charging_power` |
| Car connected | `switch.<charger>_car_connected`, or every state but `disconnected` of `sensor.<charger>_status` |

Change the background power and the switches for the car, and watch the regulation on the status page.
