---
name: kraftvakt-simulator
description: The Kraftvakt simulator in simulator/custom_components/kraftvakt_simulator - a simulated HAN, heating devices and thermostats with a duty cycle,
  and 400 V three-phase EV chargers, set up as config entries in a local Home Assistant to test Kraftvakt by hand. Where it lives and why, how the devices behave, the modules,
  entities and config flow, and how to extend it. Use before changing or adding anything in simulator/ or tests/simulator/.
---

# Kraftvakt simulator

The simulator lets Kraftvakt regulate something that behaves like a house, without real appliances or a HAN port.
It is only for development: it runs in a local Home Assistant next to Kraftvakt and is never shipped to users.

## Where it lives

- The integration is `simulator/custom_components/kraftvakt_simulator/`, domain `kraftvakt_simulator`. It must stay outside the top-level `custom_components/`:
  HACS installs from there, and the hassfest action validates exactly `custom_components/*/manifest.json` and a manifest in the repository root.
  Nothing in `simulator/` reaches users or CI validation.
- `pyproject.toml` puts `simulator` on pytest's `pythonpath`. `custom_components` is a namespace package (no `__init__.py`),
  so both folders join into one package and Home Assistant's loader finds both integrations in the tests. The tests are part of the normal test run.
- In a local Home Assistant, `config/custom_components/` is a real folder with one symlink to each integration.
- `SIMULATOR.md` in the repository root describes the simulator for developers, as `README.md` does for Kraftvakt. Keep it up to date with the code; the README only links to it.
- Code follows the same rules as Kraftvakt (`CLAUDE.md`): English code, HA standards, translations in `translations/en.json` and `nb.json`.
  There is no `strings.json`, because hassfest never reads the simulator.

## How the devices behave

- One integration. Adding a device shows a menu: HAN, heating device, thermostat or EV charger. Each device is its own config entry and device.
- Only one HAN. It reports the background power plus the power of every simulated device, also devices set up after it,
  only at its report interval, 2 or 10 s, a setting in the config entry data: also an unchanged value, and the power at that moment.
  Why: a real HAN reader reports what the meter measured at the meter's fixed interval, and Kraftvakt closes its regulation windows at the reports,
  so a report on every change would close windows right after each command. Reporting an unchanged value keeps Kraftvakt's power sensor timeout from running out.
- Heating device types (heating cable, water heater, panel heater) behave the same; the type only gives the switch its icon.
- A heating device has power (W), duty cycle (0–100 %) and period (whole minutes). It heats in a fixed cycle, the on part first. Its switch cuts the power: off consumes nothing.
  **The cycle restarts in its on part every time the switch is turned on**, and so also after a restart with a restored switch.
  Why: a device that Kraftvakt turns on must draw power at once, as a real one does.
- A thermostat is a heating device whose climate entity takes the place of the switch, with the HVAC modes chosen in its settings (at least one of the heating modes heat,
  heat/cool and auto) and a target temperature. It runs the cycle in a heating mode while the target temperature is above the room temperature,
  a setting that never changes by itself. With the default room temperature (5 °C) it heats at any normal target, so the regulation sees the same power as from a heating device.
  Turning it on returns to the last heating mode (the first supported heating mode at first), as `climate.turn_on` does on real thermostats.
  Why: Kraftvakt's default climate actions and its thermostat actions (HVAC mode, temperature, or both, and the fallbacks when a thermostat lacks heat or off) can be tested.
  Turning off is offered only when off is one of its modes. It starts in off, or in its first mode when off is not one of them.
- A heating device has a temperature, of the water or the floor, that changes only when it is set: a temperature sensor and a number in the configuration category.
  A thermostat names them floor temperature, since its climate entity already has a current temperature, the room temperature.
  Why: Kraftvakt's display temperature can be tested from a sensor and from a thermostat on the same device.
- Power, duty cycle and period are also number entities, changeable while HA runs.
  A change while the switch is on restarts the cycle in its on part; an unchanged value does nothing.
- An EV charger is 400 V three-phase with power factor 1: `P = √3 · 400 V · I`. It has a minimum and maximum current in whole amperes.
  Its charging current goes from 0 A to the maximum; a current below the minimum is 0 A, where it does not charge.
  Why: a charger switched by its current is stopped with 0 A.
  It draws power only while charging is allowed, a car is connected, the car is not fully charged and its fault switch is off.
  The fault switch is meant as a fault flag of Kraftvakt's deactivate on fault, so it has no binary sensor of its own.
  Its charging binary sensor is on while it draws power, so Kraftvakt's actively charging can be tested from an entity.
  With a start delay, a setting in the config entry data, a car that starts to want power draws none until the delay has passed, as through a cloud service.
  A change of current while it charges does not delay it.
- Heating devices, thermostats and chargers have an unplugged switch. While it is on, the device uses no power whatever its other switches say.
  A heater's cycle runs on while unplugged. The HAN has no such switch: set its background power instead.
- Entities that control the simulation and are not part of a real device have `EntityCategory.CONFIG`, so HA shows them under Configuration on the device page: background power,
  heating power, duty cycle, period, room temperature, temperature, car connected, car fully charged, fault and unplugged.
  Charging allowed, the charging current, the heater switch and the sensors are the device's own and stay main entities.
- A heating device's switch and a thermostat's climate entity have the device's name. The other entities are named by their translation key.
- After a restart every entity gets its state back. The switches,
  the charging current (clamped to the current range) and a thermostat's mode and target temperature restore themselves. The settings that are numbers (background power,
  heating power, duty cycle, period, room temperature, temperature) are kept in the config entry data instead, so reconfiguring the device changes them.
- Every kind has a reconfigure flow with the same form as when it was added. It reloads the entry.

## Modules

| Module | Responsibility |
|---|---|
| `model.py` | Pure Python, no HA: the duty cycle (heating and the time to the next change), three-phase power, the charger state. Unit tested. |
| `devices.py` | The power board (power per consumer, summed for the HAN, shared in `hass.data`) and the devices. Devices own the state and timers, report their power to the board and notify listeners. |
| `__init__.py` | Creates the device of an entry by its kind and forwards only the platforms of that kind. |
| `config_flow.py` | Menu, one form per kind, validation, reconfigure. |
| `entity.py` | The base entity: device info, a unique ID from the entry and a key, writes its state when what it observes changes. |
| `sensor.py`, `switch.py`, `number.py`, `binary_sensor.py`, `climate.py` | The entities, as entity descriptions with functions that read and set the device. |

## How to write code for the simulator

- Keep behaviour in `model.py` as pure functions or frozen dataclasses with time passed in; keep HA (timers, clock, registry) in `devices.py`; keep entities thin:
  they read and set the device and nothing else.
- A new device kind needs a kind, a form, a device class, its platforms, the entities and both translation files. Report power through the power board so the HAN counts it.
  A new heating type only needs the type, an icon and the selector translations.
- Settings go in the config entry data, runtime state in entities that restore themselves.
- Tests: unit tests for `model.py` in `tests/unit/simulator/`, black box tests in `tests/simulator/` with the fixture for adding a device from its `conftest.py`.
  Entity IDs follow the device names (English in the test harness).
  A change shows on the HAN only at its next report, so a test reads what the house draws from the power board, or lets the report interval pass first.
  Kraftvakt runs against the simulator end to end in `test_kraftvakt_with_simulator.py`,
  and in `test_use_cases.py`, where each test is a use case of a household. Keep the simulator at 100 % line coverage.
