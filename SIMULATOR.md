# Kraftvakt simulator

The simulator makes it possible to test Kraftvakt without a HAN port and real
appliances. It is a separate integration, **Kraftvakt simulator**, in
`simulator/custom_components/kraftvakt_simulator/`, with its tests in
`tests/simulator/` and `tests/unit/simulator/`. It is outside
`custom_components/`, so HACS does not install it, and it is only used with a
local Home Assistant, see
[Local Home Assistant](README.md#local-home-assistant). It is not part of a
release.

Add the integration under **Settings → Devices & services**, and add one
device at a time with **Add device**:

- **HAN:** the power of the house, the background power plus the power of all
  the simulated devices (`sensor.han_power` when the device is named «HAN»).
  It reports every 10 seconds, also when the power has not changed, as a HAN
  reader does. There can be only one HAN.
- **Heating device:** heating cable, water heater or panel heater, with power
  (W), duty cycle (0–100 %) and period (minutes). It has a switch and a power
  sensor. While the switch is on, it heats in a fixed cycle that starts with
  the on part: 750 W, 25 % and 60 minutes give 15 minutes on and 45 minutes
  off, over and over. The cycle starts again every time the switch is turned
  on or the cycle is changed. With the switch off, it uses nothing.
- **Thermostat:** a heating device controlled by a thermostat, with the same
  power, duty cycle and period, the HVAC modes it supports (off, heat and auto
  by default, at least one heating mode) and a room temperature (5 °C by
  default). Its climate entity has the chosen modes and a target temperature.
  In heat, heat/cool and auto it heats in the cycle while the target
  temperature is above the room temperature; otherwise it uses nothing. The
  cycle starts again every time it starts heating. Turning it on returns it
  to the last heating mode, the first heating mode it supports at first. It
  can only be turned off when off is one of its modes. It starts in off, or
  in its first mode when off is not one of them.
- **EV charger:** three-phase 400 V with a minimum and maximum current. It has
  the switches **Charging allowed**, **Car connected** and **Car fully
  charged**, **Charging current** (A), the sensor **Charging power** and the
  binary sensor **Charging**, on while it draws power. It
  draws √3 × 400 V × the charging current (6 A gives 4.16 kW) when charging
  is allowed, a car is connected and the car is not fully charged.

Heating devices, thermostats and EV chargers also have the switch
**Unplugged**. While it is on, the device uses nothing, whatever the other
switches are set to. The cycle of a heating device runs on while it is
unplugged.

What controls the simulation and does not belong to a real device is under
**Configuration** on the device page, and can be changed while Home Assistant
runs: **Background power**, **Heating power**, **Duty cycle**, **Period**,
**Room temperature**, **Car connected**, **Car fully charged** and
**Unplugged**. The settings can
be changed with **Reconfigure**. The switches, the charging current, and the
mode and target temperature of a thermostat keep their state over a restart.

Then set up Kraftvakt against the simulator: the power sensor of the HAN as
the power sensor, the switches of the heating devices and the thermostats as
appliances, and for each EV charger (the entity IDs follow the language of
Home Assistant when the device is added):

| Field in Kraftvakt | Value |
|---|---|
| Device | The EV charger device; choosing it fills in the fields below |
| Entity for allowed charging | `switch.<charger>_charging_allowed` |
| Activate and Deactivate | Standard |
| Set charging current | Entity: `number.<charger>_charging_current` |
| Actively charging | Entity: `binary_sensor.<charger>_charging`, or Charging power: `sensor.<charger>_charging_power` |
| Car connected | `switch.<charger>_car_connected` |

Change the background power and the switches for the car, and watch the
regulation on the status page.
