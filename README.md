<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/kraftvakt/brand/dark_logo@2x.png">
    <img src="custom_components/kraftvakt/brand/logo@2x.png" alt="Kraftvakt" height="128">
  </picture>
</p>

# Kraftvakt: prioritized power management for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/aalbretsen/kraftvakt/actions/workflows/validate.yml/badge.svg)](https://github.com/aalbretsen/kraftvakt/actions/workflows/validate.yml)
[![CI](https://github.com/aalbretsen/kraftvakt/actions/workflows/ci.yml/badge.svg)](https://github.com/aalbretsen/kraftvakt/actions/workflows/ci.yml)

Kraftvakt decides which power-hungry appliances may use power, in priority order, for example a water heater, heating cables and EV chargers.
It is made for the Norwegian electricity market and keeps the average consumption over the last hour just below a chosen power limit,
so you avoid a more expensive step in the capacity part of the grid tariff. Everything is set up in a panel in the sidebar. Kraftvakt runs entirely locally, without cloud services.

> **Status:** Currently in beta with preview releases for testing

## Requirements

- Home Assistant 2026.10 or newer
- A sensor from another integration that measures the total power of the house, typically from the HAN port of the electricity meter, with the device class power.
  It may report W or kW. A sensor without a unit is read as W.

## Installation

### HACS (recommended)

1. Open HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/aalbretsen/kraftvakt` with the type **Integration**.
3. Install **Kraftvakt** and restart Home Assistant.

### Manual

Copy `custom_components/kraftvakt` to `config/custom_components/` in Home Assistant and restart.

## Setup

1. Go to **Settings → Devices & services → Add integration**, search for **Kraftvakt** and finish the setup. It has no settings.
2. Open **Kraftvakt** in the sidebar, or press the cogwheel of the integration, and set the power sensor, the power limit, the appliances and any EV chargers.
3. Press **Save**, go to **Status** and press **Start regulation**.

## How it works

- **Power limit:** the highest allowed tariff average, for example 10,000 W. It matches the step of the capacity tariff you want to stay below.
- **Tariff average:** the average of the power sensor over the tariff window, the last hour, sliding. The grid company measures the energy of each clock hour,
  and every clock hour is also one of the sliding hours, so keeping the tariff average below the power limit keeps every clock hour below it too.
  The sliding hour also finds overconsumption early: a budget for each clock hour could be used up in the middle of the hour,
  and leave the household without power for the rest of it.
- **Regulation average:** the average of the power sensor over a short regulation window, 10 seconds by default. It drives the decisions.
- **Decisions:** at every regulation interval, the regulation decides whether to turn an appliance on or off. When the regulation average is above the power limit,
  the lowest-priority appliance that is on is turned off. When power is free, the next appliance in the priority list is turned on, one at a time and after a waiting time.
  When the next appliance cannot be turned on for lack of free power while appliances below it are on, for example after a variant has moved it up,
  the lowest of them is turned off, one at each decision, until it fits.
- **Turn-on margin:** how far below the power limit the regulation average must be before an appliance is turned on, 100 W by default.
  The window right after a decision still holds some of the consumption from before it,
  and the margin keeps an appliance from being turned on only to be turned off again at the next decision.
- **Power reserve:** optional free power that must be available before an appliance is turned on, for example 4000 W for a pool heater that draws a lot as soon as it is turned on.
- **Waiting time:** follows the waiting time curve. With the regulation average below half the power limit there is no waiting,
  and close to the power limit the appliance waits nearly the whole waiting time at the power limit, 300 seconds by default.
- **Repeated turn-on:** when the regulation turns the same appliance on over and over again with nothing else switched in between, the first two turn-ons follow the curve.
  From the third, the waiting time is the waiting time at the power limit, and it grows by one increment each time until the chosen number of increments is reached.
  The increment is a share of the waiting time at the power limit. The defaults are × 0.5 and 4 increments for appliances (150 s increments, at most 900 s),
  and × 1 and 5 increments for EV chargers (300 s increments, at most 1800 s), where each ampere counts on its own.
  With no waiting time at the power limit, the waiting time does not grow.
- **Variants:** an appliance can have variants with another place in the priority list, for example a higher priority in the morning.
  A variant uses the actions of the appliance, or overrides the action to turn on, to turn off or both, for example with another HVAC mode for a thermostat in summer.
  When the variant changes, the appliance is turned off with the turn-off action of the new variant, and comes on again the normal way.
  If it comes on again at the same decision, it only gets the turn-on action, so it is not switched off and on at once.
- **Excluded appliance:** the switch **‹appliance› excluded from regulation** takes an appliance out of the regulation.
  It keeps its place in the priority list, but is passed as if it was not there, and is turned off at the next decision if it is on.
  When it is included again while appliances below it are on, the lowest of them is turned off to make room for it.
- **Penalty:** when the tariff average goes above the power limit plus the penalty threshold, every appliance is kept off until the overconsumption is recovered,
  and the regulation then starts again. The penalty is a safety valve and should normally never happen.
- **Safe state:** when the power sensor has had no valid value as two regulation windows in a row closed, every appliance is kept off. A single missing value is tolerated.
  A power sensor that has not reported for the power sensor timeout, 300 seconds by default, has no valid value, also when its value has not changed.
  When the sensor gives a valid value again, the regulation starts again.
- **Command repeat:** an appliance or EV charger that has had no command for the command repeat interval, 30 minutes by default,
  gets the command for the state Kraftvakt has set again: on or off for an appliance, the charging current for an activated EV charger, and deactivate for one that is deactivated.
  It is checked every time a regulation window closes while the regulation runs, also in the safe state and during a penalty.
  Excluded appliances and EV chargers get no repeated commands.
  An activated EV charger is not activated again, since that may start a new charging session in the charger.
- **Failed action:** an action that fails, or has not finished within the action timeout, 60 seconds by default, is logged, and the regulation goes on as if it worked.
  The command repeat sends the command for the state again later, except the activation of an EV charger.

Kraftvakt does not know what an appliance uses, and does not read whether it is on.
It assumes each appliance is as Kraftvakt last set it, and repeats that command now and then, see **Command repeat**. Do not turn regulated appliances on or off outside Kraftvakt.
It can disturb the regulation, affect appliances with higher priority and trigger a penalty, and the command repeat sets the appliance back.
Exclude the appliance from the regulation instead. EV chargers are the exception: Kraftvakt reads whether they are actively charging and whether a car is connected.

## Starting and stopping

The regulation starts by itself when Home Assistant or the integration starts, provided the configuration is complete:

- a power sensor is chosen,
- every appliance has an entity and actions to turn it on and off, and every variant an expression and the actions it overrides,
- every EV charger has a device, an entity, actions to activate, deactivate and set the charging current, and **Actively charging**,
  and also **Car connected** when only one EV charger in its group may charge at a time,
  or when it has a charging window and **End the override** is **When the car is disconnected**.

When Home Assistant starts, the regulation waits until Home Assistant has finished starting, so the integrations of the appliances are loaded.
When the configuration is not complete then, it is reported under **Settings → Repairs**.
If the stored configuration (`.storage/kraftvakt.config`) cannot be read, Kraftvakt does not start, the integration shows an error, and the file is left unchanged.

Every start turns all appliances off at once, and deactivates all EV chargers. The regulation then turns them on one by one in priority order,
with the first decision one full regulation interval after the start. The regulation also starts again with everything off when a penalty or the safe state ends.

The **Regulation** switch, and the button on the status page, stop and start the regulation. Stopping turns all appliances off, and nothing is turned on until it starts again.
If the configuration is not complete, turning the switch on gives an error and it stays off. The switch has no stored state, so the regulation runs again after a restart.

## Appliances are not handed back

Kraftvakt never hands an appliance back to you. When an appliance or EV charger is removed from the configuration or excluded from the regulation, when the regulation is stopped,
and when the integration is removed, it stays as Kraftvakt last set it, often off. Set it yourself as you want it: for example, turn the water heater on again, or it stays cold.

## Cloud-controlled devices

Kraftvakt runs locally, but an appliance or EV charger controlled through a cloud service depends on that service and on the internet connection.
A command may be delayed, or lost while the service is down. Kraftvakt logs the failure, goes on as if the command worked, and sends it again with the command repeat,
so an appliance may stay on longer than the regulation wants and the power limit may be exceeded. Prefer devices with local control for appliances that draw a lot of power.
An action that does not finish is stopped by the action timeout, so it does not hold back the commands after it.
The commands that wait for it are merged, so only the newest command for each appliance and EV charger is sent when it finishes.

An entity of an appliance or EV charger that no longer exists in Home Assistant is reported under **Settings → Repairs**.
An entity that is only unavailable, for example while its cloud service is down, is not.

## EV charging

EV chargers are put in groups, for example one for the chargers in the garage and one for the chargers at the cabin.
A group has a name, a place of its own in the priority list, and its own setting for one EV charger at a time. An EV charger is in one group.
Without groups, Kraftvakt does not control EV chargers. To keep an EV charger from charging for a while, turn on its switch **‹charger› excluded from regulation**.
The rules below apply within each group, so two groups with one EV charger at a time can each have an EV charger charging.

An EV charger is a device in Home Assistant, and gets its name from it. Every entity Kraftvakt uses for it belongs to that device: the entity that is activated,
the entity for the charging current, and the entities for car connected and actively charging.
A value from another device, for example whether the car is connected from the car's own integration, is given as a template.

Kraftvakt sets the charging current of each EV charger one ampere at a time, by how much power is free.
The place of the group in the priority list decides where its EV chargers are in the order. An EV charger charges only when Kraftvakt has activated it,
so a car that is connected does not start charging by itself. The charging current is set to the minimum before the EV charger is activated or deactivated.

- **Actively charging** is read at every decision, from one of:
  - a sensor for charging power: above 100 W counts as charging. It may report W or kW,
  - a boolean entity: on counts as charging,
  - a template: the boolean value true counts as charging.

  Anything else counts as not charging, also an unavailable sensor or entity and a template that fails or gives something else than true or false.
  An EV charger that has lost power or its connection reports unavailable, and does not charge.
- An EV charger gets more than the minimum current only when it is actively charging. While it is being tried, the appliances below its group can be turned on.
  When it charges, or is tried again, they are turned off one at a time while it needs room, see **Decisions**.
- An EV charger that is not charging, because no car is connected or because it is not actively charging two regulation windows after it was activated, is bypassed.
  It gets no more than the minimum current, stays activated if it is, and does not stand in the way of other EV chargers in the group.
- An EV charger that is not charging rests before it is tried again: 15 minutes the first time, then 30, and then 60 minutes each time the car still does not charge.
  It stays bypassed while it rests. If the car is disconnected and connected again, or starts charging, it is tried at once,
  and a car connected again gets two regulation windows to start charging.
- When only one EV charger in a group may charge at a time, an EV charger that is actively charging may continue until it is done, and the others in the group wait.
  **Car connected** is then required for every EV charger in the group.
  Without it, Kraftvakt could only find a connected car by activating the EV charger, and EV chargers without a car would be activated in turn.
- Outside its charging window, an EV charger does not charge. The charging window can span midnight and follows the time zone of Home Assistant.
- With **Finish ongoing charging after the charging window**, off by default, an EV charger that is charging when its charging window ends may go on charging, regulated as before,
  until it stops. Charging has stopped at the first decision where it is not actively charging, or when it is deactivated for any reason, for example above the power limit,
  a disconnected car, an excluded EV charger or a stopped regulation. It is then not turned on again before the charging window starts.
  An EV charger that is activated but not yet actively charging when the window ends is deactivated.
  The setting is also the switch **‹charger› finish charging after charging window**.
- The switch **‹charger› override charging window** lets the EV charger charge outside the charging window. A charging window that starts does not end it.
  **End the override** chooses when it turns itself off:
  - **When I turn it off**, the default: it stays on until you turn it off.
  - **When the car no longer charges**: at the first decision where the EV charger has been activated for two regulation windows and is not actively charging,
    once it has been actively charging since the switch was turned on. A full car ends it, so the car heating in the morning does not charge.
    An EV charger that Kraftvakt has deactivated, for example above the power limit, does not end it, and the car gets time to start again when it is activated again.
    A car that never starts charging, for example one that is already full, does not end it.
  - **When the car is disconnected**: at the first decision where the car is not connected, once a car has been connected since the switch was turned on.
    It lasts through a full car and the car heating in the morning. **Car connected** is then required.

  The last two can be turned on before the car arrives, since they wait for the car. Only a known value ends the override: a car sensor that is unavailable,
  or a template that fails, does not, so a cloud service that is down for a moment does not stop the charging you asked for.
  A car that stops charging or leaves while the regulation is stopped is noticed at the first decision after it starts;
  one that stops charging or leaves while Home Assistant restarts is not, and the override stays on until you turn it off.

## The panel

The panel has a menu at the top with the status page and four configuration pages. Only administrators have access.

Changes are collected in a draft. **Save** stores everything at once, and **Discard** goes back to what is stored. Errors are shown at the field,
and nothing is saved until they are fixed. The panel asks before unsaved changes are discarded. The configuration can only be changed while the regulation is stopped;
while it runs, the configuration pages are locked. A saved configuration is used the next time the regulation starts.

### Configuration pages

- **General:** power sensor, power limit, turn-on margin, regulation window, regulation interval, waiting time at the power limit and penalty threshold.
  The helper text under each field shows the valid range and the default.
- **Appliances:** the priority list, with the most important appliance at the top; drag to change the order. An appliance has an entity, actions to turn it on and off,
  an optional power reserve, and its variants. A variant is a separate entry in the priority list with an expression, a boolean entity or a template,
  and can override the action to turn on, to turn off or both. The variants are evaluated in the order of the appliance's list, and the top true expression applies.
  The power reserve applies to every variant. Each group of EV chargers is in the list under its name, and is moved like an appliance.
- **EV charging:** one card per group of EV chargers, with the name, one EV charger at a time, and the EV chargers in charging priority.
  Drag an EV charger to another group to move it there. An EV charger starts with its device in Home Assistant;
  choosing the device fills in the entities the device most likely has, guessed from their names and types, so check what was filled in.
  Then come the actions, the charging current, the power reserve, car connected, actively charging and the charging window.
- **Advanced:** the waiting time curve, the waiting time on repeated turn-on, the command repeat interval, and the timeouts for actions and for the power sensor.
  The tables show the actual waiting time, rounded up to the regulation interval, since an appliance is turned on at the first decision after its waiting time.

### Actions

Actions adapt to the domain of the entity. A standard action is offered when the domain has one, and some device types have actions of their own,
such as the HVAC mode and temperature of a thermostat. Every action can also be a custom action, made with the action editor of Home Assistant,
see [Template and action examples](#template-and-action-examples). An entity used by another appliance or EV charger cannot be chosen.

### Status page

The status page shows whether the regulation runs, with the button to start and stop it. If the configuration is not complete, it lists what is missing,
with a link to the page where it is fixed. While the regulation runs, it shows the consumption now and the averages against the power limit, the next decision,
the safe state and the penalty when they occur, and the priority list as it stands: each appliance at the place of its current variant,
and each group with its EV chargers in the current charging priority and their charging current. Each row has a label telling how it stands; hover over it for the explanation.
A dashed line goes under the last entry that is on, with the free power, and a bar shows the time left until the next appliance, or one more ampere, is turned on.

## Entities

All entities belong to the service device **Kraftvakt**.

| Entity | Description |
|---|---|
| **Regulation** | |
| `switch.kraftvakt_regulation` (Regulation) | On while the regulation runs. Turn off to stop the regulation, and on to start it again. |
| `binary_sensor.kraftvakt_regulation_safe_state` (Regulation safe state) | On while the regulation is in safe state. Can trigger an automation that notifies you. |
| `sensor.kraftvakt_regulation_steps_on` (Regulation steps on) | Diagnostic. The number of steps that are on: each appliance is one step, and each ampere of an EV charger, from the minimum current up, is one step. |
| **Power** | |
| `number.kraftvakt_power_limit` (Power limit) | The power limit in W, the same as in the panel. Can also be set while the regulation runs. |
| `sensor.kraftvakt_power_regulation_average` (Power regulation average) | The regulation average in W. |
| `sensor.kraftvakt_power_tariff_average` (Power tariff average) | The tariff average in W. |
| `sensor.kraftvakt_power_free` (Power free) | Diagnostic. The power limit minus the regulation average, in W. Negative above the power limit. |
| **Waiting time** | |
| `sensor.kraftvakt_waiting_time_remaining` (Waiting time remaining) | Diagnostic. Seconds until the decision where the waiting appliance or ampere is turned on, 0 when nothing waits. |
| `sensor.kraftvakt_waiting_time_next_turn_on` (Waiting time next turn-on (calculated)) | Diagnostic. The waiting time in seconds the next turn-on gets from the last regulation average and the waiting time curve, without the growth on repeated turn-on. |
| **Penalty** | |
| `binary_sensor.kraftvakt_penalty_active` (Penalty active) | Diagnostic. On during a penalty period. |
| `sensor.kraftvakt_penalty_overconsumption` (Penalty overconsumption) | Diagnostic. The overconsumption in Wh at the last decision: the net energy above the power limit since the tariff average went above it. 0 when there is none. |
| **Appliance** | |
| `switch.kraftvakt_appliance_<appliance>_excluded` (‹appliance› excluded from regulation) | One per appliance. Turn on to take the appliance out of the regulation, so it is never turned on and gets no repeated commands. |
| **EV charger** | |
| `switch.kraftvakt_charger_<charger>_excluded` (‹charger› excluded from regulation) | One per EV charger. Turn on to take the EV charger out of the regulation, so the car never charges and the EV charger gets no repeated commands. |
| `switch.kraftvakt_charger_<charger>_window_override` (‹charger› override charging window) | One per EV charger. Turn on to let the EV charger charge outside the charging window. Turns itself off as chosen in **End the override**. |
| `switch.kraftvakt_charger_<charger>_finish_after_window` (‹charger› finish charging after charging window) | One per EV charger. The same setting as **Finish ongoing charging after the charging window** in the panel. Can be changed while the regulation runs. |
| `binary_sensor.kraftvakt_charger_<charger>_allowed_to_charge` (‹charger› allowed to charge) | Diagnostic. One per EV charger. On while the EV charger may charge: it is not excluded, and it has no charging window, is inside it, has **‹charger› override charging window** on, or is finishing the charging after the charging window. It follows the clock, also while the regulation is stopped, and stays on without a break when the charging window ends with an EV charger that goes on finishing. |

The sensors are updated every time a regulation window closes. The sensors that depend on the averages are unavailable until the first regulation window has closed,
and after two regulation windows in a row closed without a valid value from the power sensor, also while the regulation is stopped.
When the power sensor gives a valid value again, the measurements from before are kept, and the time without a valid value is counted with the last valid value before it.

When Kraftvakt starts, the hour before is read from the history of the power sensor in the Home Assistant recorder, so the tariff average is right also just after a restart.
The time Home Assistant was down is counted with the last value before it stopped. Without history, the first measurement is used back in time.

A new value in **Power limit** is stored at once and used from the next decision, also while the regulation runs, without starting it again.
Above a lower limit, appliances are turned off one at each decision as usual.

The appliance and EV charger switches can be used while the regulation runs and apply from the next decision, without restarting it.
An excluded appliance or EV charger gets no repeated commands from the next regulation window. Their state is stored at once and kept over a restart.
The entities of an EV charger do not depend on its group, and are kept when it is moved to another group.

The entity IDs are the same in every language and are grouped by what they concern: `regulation`, `power`, `waiting_time`, `penalty`, `appliance` and `charger`.
The names shown follow the language of Home Assistant. ‹appliance› is the name of the entity of the appliance. ‹charger› is the name of the device of the EV charger.
The entity ID keeps the name from when the appliance or EV charger was added.

**Waiting time next turn-on (calculated)** is disabled by default; enable it under the entity's settings when you want it.

## Diagnostics

**Download diagnostics** on the integration's page gives the configuration, the status, and the last decisions and failed actions, for a bug report.

## Template and action examples

Templates use the template language of Home Assistant (Jinja2), and actions are the same as in automations and scripts.
In the action editor you can switch to YAML from the ⋮ menu and paste the examples.
Every template and action gets the variables `entity_id` (the entity of the appliance or EV charger) and `entity` (its state object,
for example `entity.state` and `entity.attributes`), so the templates keep working when the entity is replaced.
The action for the charging current also gets `current`, `min_current` and `max_current`. `current` is always between the minimum and maximum charging current.

A template is true only when it gives the boolean value true. Anything else, including an error in the template, counts as false. An entity is true only when it is `on`.

**Variant «Morning»** that gives the water heater a higher priority between 05 and 08:

```jinja
{{ 5 <= now().hour < 8 }}
```

**Variant «Cold»** for a heat pump when it is below 18 degrees indoors:

```jinja
{{ entity.attributes.current_temperature | float(99) < 18 }}
```

**Car connected** from the status sensor of the charger:

```jinja
{{ states('sensor.garage_charger_status') in ['connected', 'charging', 'awaiting_start'] }}
```

**Actively charging** from a sensor with the charging current the charger reports:

```jinja
{{ states('sensor.garage_charger_current') | float(0) > 1 }}
```

When the sensor is unavailable, `float(0)` gives 0 and the template gives false, so the EV charger counts as not charging,
and as stopped for **End the override**. Leave out the default, `| float`, to let an unavailable sensor give no value instead:
the EV charger still counts as not charging, but the override does not end.

**Turn on** an appliance by setting a temperature instead of turning it on:

```yaml
- action: climate.set_temperature
  target:
    entity_id: "{{ entity_id }}"
  data:
    temperature: 22
```

**Turn off** the same appliance by setting it to frost protection:

```yaml
- action: climate.set_temperature
  target:
    entity_id: "{{ entity_id }}"
  data:
    temperature: 8
```

**Set charging current** with a service from the charger's integration that takes the current per phase.
`my_charger.set_current` is an example; use the service and fields of your charger's integration:

```yaml
- action: my_charger.set_current
  data:
    charger_id: garage
    phase1: "{{ current }}"
    phase2: "{{ current }}"
    phase3: "{{ current }}"
```

## Development

Requires Python in the version in `pyproject.toml`, the same as the Home Assistant version in `requirements_dev.txt` requires, and [uv](https://docs.astral.sh/uv/).
The development dependencies are in `requirements_dev.txt`.

```bash
uv venv --python 3.14
uv pip install -r requirements_dev.txt
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

The code is in `custom_components/kraftvakt/`. The regulation is plain Python without Home Assistant in `regulation/`, and `runtime.py` connects it to Home Assistant.
The tests are in `tests/`, with unit tests in `tests/unit/`. The simulator is in `simulator/`, see [SIMULATOR.md](SIMULATOR.md).

### Panel

The panel is written in Lit and TypeScript in `frontend/` and built with Node.js, in the version in `.nvmrc`, the same as the Home Assistant frontend uses.
Install and activate it with [nvm](https://github.com/nvm-sh/nvm) or [nvm.fish](https://github.com/jorgebucaran/nvm.fish):

```bash
nvm install
```

```bash
nvm use
```

The built bundle, `custom_components/kraftvakt/frontend/kraftvakt-panel.js`, is committed, because HACS installs straight from the repository.
Build it again after every change in `frontend/`, and commit the source and the bundle together. CI fails if the committed bundle does not match the source.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

`npm run watch` builds again on every change. The bundle is loaded with the version from `manifest.json` in the URL, so the browser may use an old bundle after a new build.
Reload the page without cache then. The texts of the panel are in `frontend/src/translations/` (English and Norwegian) and follow the language of the user in Home Assistant.

### Dependencies

Every dependency is pinned, and most follow Home Assistant: `pytest-homeassistant-custom-component` decides the version of Home Assistant and pytest,
Home Assistant decides the frontend, ruff, mypy and Python, and the Home Assistant frontend decides Node, Lit, TypeScript and `@mdi/js`.
The other build tools of the panel and the GitHub actions get their newest release. Update them all with Node active:

```bash
uv run scripts/update_dependencies.py
```

The script prints what changed. Then install again, activate the new Node, and run the checks and the panel build:

```bash
uv pip install -r requirements_dev.txt
nvm install
```

### Releasing

Versions follow [SemVer](https://semver.org/). A release is made from an up-to-date `main` with a clean working tree and Node active:

```bash
uv run scripts/release.py 0.2.0
```

The script runs the checks, sets the version in `manifest.json`, `pyproject.toml` and the panel's `package.json` and lock file, commits, tags `v0.2.0`,
and asks before it pushes `main` and the tag. The tag starts the release workflow, which checks the versions and creates a draft release on GitHub.
Write the release notes there and publish it; HACS offers only published releases.
A version with a pre-release part, like `0.2.0-beta.1`, becomes a GitHub pre-release, which HACS offers only to users who turn on pre-releases for Kraftvakt.

### Local Home Assistant

Run a local Home Assistant against the repository. `config/custom_components/` is a plain folder with one link to Kraftvakt and one to the simulator:

```bash
mkdir -p config/custom_components
ln -s ../../custom_components/kraftvakt config/custom_components/kraftvakt
ln -s ../../simulator/custom_components/kraftvakt_simulator config/custom_components/kraftvakt_simulator
uv run hass -c config
```

The simulator, for testing without a HAN port and real appliances, is described in [SIMULATOR.md](SIMULATOR.md).

From the same machine you log in without a password at http://127.0.0.1:8123 (`trusted_networks` for `127.0.0.1` and `::1` in `config/configuration.yaml`).
Other machines require a password.

### WebSocket API

The panel talks to the integration over its own WebSocket commands. All of them require an administrator.

| Command | Does |
|---|---|
| `kraftvakt/capabilities` | Gives the standard actions per field, the limits and the defaults. |
| `kraftvakt/config/get` | Gives the configuration, the names of the entities and what is missing. |
| `kraftvakt/config/save` | Stores the whole configuration. Refused while the regulation runs. An invalid configuration is not stored, and the response gives the errors per field. |
| `kraftvakt/regulation/set_running` | Starts or stops the regulation, as the **Regulation** switch. |
| `kraftvakt/status/subscribe` | Sends the status at once and then for every regulation window, every decision, and on start, stop and save. |

### Logo and icon

The sources are in `assets/brand/`. The PNG files in `custom_components/kraftvakt/brand/` (loaded directly by Home Assistant from 2026.3) are built with:

```bash
uv run --with cairosvg --with pillow scripts/build_brand.py
```

## License

[MIT](LICENSE)
