---
name: kraftvakt-simulator
description: The Kraftvakt simulator in simulator/custom_components/kraftvakt_simulator - a simulated HAN, heating devices with a duty cycle and 400 V three-phase EV chargers, set up as config entries in a local Home Assistant to test Kraftvakt by hand. Where it lives and why, the decisions settled with the owner, the modules, entities and config flow, and how to extend it. Use before changing or adding anything in simulator/ or tests/simulator/.
---

# Kraftvakt simulator

The simulator lets Kraftvakt regulate something that behaves like a house,
without real appliances or a HAN port. It is only for development: it runs in
a local Home Assistant next to Kraftvakt and is never shipped to users.

## Where it lives

- The integration is `simulator/custom_components/kraftvakt_simulator/`,
  domain `kraftvakt_simulator`. It must stay outside the top-level
  `custom_components/`: HACS installs from there, and the hassfest action
  validates exactly `custom_components/*/manifest.json` and a manifest in the
  repository root. Nothing in `simulator/` reaches users or CI validation.
- `pyproject.toml` puts `simulator` on pytest's `pythonpath`. `custom_components`
  is a namespace package (no `__init__.py`), so both folders join into one
  package and Home Assistant's loader finds both integrations in the tests.
  The tests are part of the normal `uv run pytest`.
- In a local Home Assistant, `config/custom_components/` is a real folder with
  two symlinks: `kraftvakt -> ../../custom_components/kraftvakt` and
  `kraftvakt_simulator -> ../../simulator/custom_components/kraftvakt_simulator`.
- Code follows the same rules as Kraftvakt (`CLAUDE.md`): English code, HA
  standards, translations in `translations/en.json` and `nb.json`. There is no
  `strings.json`, because hassfest never reads the simulator.

## Decisions settled with the owner

- One integration. «Add device» shows a menu: HAN, heating device or EV
  charger. Each device is its own config entry and device.
- Only one HAN (`single_han`). It reports the background power plus the power
  of every simulated device, also devices set up after it.
- Heating device types: heating cable (`mdi:heating-coil`), water heater
  (`mdi:water-boiler`), panel heater (`mdi:radiator`). They behave the same; the
  type only gives the switch its icon (an icon translation keyed by the type).
- A heating device has power (W), duty cycle (0–100 %) and period (whole
  minutes). It heats in a fixed cycle, the off part first: 750 W, 25 %, 60 min
  is off 45 min, on 15 min, and so on. Its switch cuts the power: off consumes
  nothing. **The cycle restarts in its off part every time the switch is
  turned on**, and so also after a restart with a restored switch.
- An EV charger is 400 V three-phase with power factor 1:
  `P = √3 · 400 V · I` (6 A → 4.16 kW). It has a minimum and maximum current
  (whole amperes, `max_below_min` otherwise). It draws power only while
  charging is allowed, a car is connected and the car is not fully charged.
- Heating devices and chargers have an «Unplugged» / «Frakoblet» switch
  (`unplugged`, `mdi:power-plug-off`). While it is on the device uses no power
  whatever its other switches say, so a simulation can control which devices
  consume. A heater's cycle runs on while unplugged. The HAN has no such
  switch: set its background power instead. `PluggedInDevice` in `devices.py`
  gives the power as 0 while unplugged, and the devices implement `demand_w`.
- Entity names (en / nb): charger switches «Charging allowed» / «Lading
  tillatt», «Car connected» / «Bil tilkoblet», «Car fully charged» / «Bil
  fulladet»; number «Charging current» / «Ladestrøm» (A); sensor «Charging
  power» / «Ladeeffekt» (W). Heating device: the switch has the device's name
  and the sensor is «Power» / «Effekt». HAN: sensor «Power» / «Effekt» and
  number «Background power» / «Bakgrunnsforbruk» (W). A HAN named «HAN» gives
  `sensor.han_power`.
- After a restart every entity gets its state back. The switches use
  `RestoreEntity` and the charging current `RestoreNumber` (clamped to the
  current range). The background power is kept in the config entry data
  instead, so that reconfiguring the HAN changes it.
- Every kind has a reconfigure flow with the same form as when it was added.
  It reloads the entry.

## Modules

| Module | Responsibility |
|---|---|
| `model.py` | Pure Python, no HA: `DutyCycle` (heating and the time to the next change), `three_phase_power_w`, `ChargerState`. Unit tested. |
| `devices.py` | `PowerBoard` (power per consumer, summed for the HAN, shared in `hass.data`), `SimulatedDevice` and the three devices. Devices own the state and timers, report their power to the board and notify listeners. |
| `__init__.py` | Creates the device of an entry by its `kind` and forwards only the platforms of that kind. |
| `config_flow.py` | Menu, one form per kind (`SCHEMAS`), validation, reconfigure. |
| `entity.py` | `SimulatorEntity`: device info, unique ID `<entry_id>_<key>`, writes its state when what it observes changes. |
| `sensor.py`, `switch.py`, `number.py` | The entities. Switches are described by `SimulatorSwitchDescription` with `is_on_fn` and `set_fn`. |

## How to write code for the simulator

- Keep behaviour in `model.py` as pure functions or frozen dataclasses with
  time passed in; keep HA (timers, clock, registry) in `devices.py`; keep
  entities thin: they read and set the device and nothing else.
- A new device kind: add it to `DeviceKind`, a schema in `SCHEMAS`, a device
  class in `devices.py`, its platforms in `PLATFORMS`, `create_device()`, the
  entities and both translation files. Report power through the `PowerBoard`
  so the HAN counts it. A new heating type only needs `HeaterType`, an icon in
  `icons.json` and the selector translations.
- Settings in the config entry data, runtime state in entities that restore
  themselves.
- Tests: unit tests for `model.py` in `tests/unit/simulator/`, black box tests
  in `tests/simulator/` with the `add_device` fixture from its `conftest.py`.
  Entity IDs follow the device names (English in the test harness).
  `test_kraftvakt_with_simulator.py` runs Kraftvakt against the simulator end
  to end. Keep the simulator at 100 % line coverage.
