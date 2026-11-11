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

Kraftvakt decides which power-hungry appliances may use power, in priority order, for example a water heater, 
heating cables and EV chargers. It is made for the Norwegian electricity market and keeps the average consumption 
over the last hour just below a chosen power limit, so you avoid a more expensive step in the capacity part of the 
grid tariff. Everything is set up in a panel in the sidebar. Kraftvakt runs entirely locally, without cloud services.

> **Status:** Currently in beta with preview releases for testing

## Requirements

- Home Assistant 2026.10 or newer
- A sensor from another integration that measures the total power of the house, typically from the HAN port of the 
- electricity meter, with the device class power. It may report W or kW. A sensor without a unit is read as W.

## Installation

### HACS (recommended)

1. Open HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/aalbretsen/kraftvakt` with the type **Integration**.
3. Install **Kraftvakt** and restart Home Assistant.

### Manual

Copy `custom_components/kraftvakt` to `config/custom_components/` in Home Assistant and restart.

## Setup

1. Go to **Settings → Devices & services → Add integration**, search for **Kraftvakt** and finish the setup. 
   It has no settings.
2. Open **Kraftvakt** in the sidebar, or press the cogwheel of the integration, and set the power sensor, 
   the power limit, the appliances and any EV chargers.
3. Press **Save**, go to **Status** and press **Start regulation**.

## How it works

- **Power limit:** the highest allowed average consumption, for example
  10,000 W. It matches the step of the capacity tariff you want to stay below.
- **Average consumption:** the moving average of the power sensor over the
  last hour. This is what the grid company measures, and what is kept below
  the power limit.
- **Regulation average:** the average of the power sensor over a short
  regulation window, 10 seconds by default. It drives the decisions.
- **Decisions:** at every regulation interval, the regulation decides whether
  to turn an appliance on or off. When the regulation average is above the
  power limit, the lowest-priority appliance that is on is turned off. When
  power is free, the next appliance in the priority list is turned on, one at
  a time and after a waiting time.
- **Turn-on margin:** how far below the power limit the regulation average
  must be before an appliance is turned on, 100 W by default. The window right
  after a decision still holds some of the consumption from before it, and
  the margin keeps an appliance from being turned on only to be turned off
  again at the next decision.
- **Power reserve:** optional free power that must be available before an
  appliance is turned on, for example 4000 W for a pool heater that draws a
  lot as soon as it is turned on.
- **Waiting time:** follows the waiting time curve. With the regulation
  average below half the power limit there is no waiting, and close to the
  power limit the appliance waits nearly the whole waiting time at the power
  limit, 300 seconds by default.
- **Repeated turn-on:** when the regulation turns the same appliance on over
  and over again with nothing else switched in between, the first two
  turn-ons follow the curve. From the third, the waiting time is the waiting
  time at the power limit, and it grows by one step each time until the
  chosen number of steps is reached. The step is a share of the waiting time
  at the power limit. The defaults are × 0.5 and 4 steps for appliances
  (150 s steps, at most 900 s), and × 1 and 5 steps for EV chargers (300 s
  steps, at most 1800 s), where each ampere counts on its own. With no waiting
  time at the power limit, the waiting time does not grow.
- **Variants:** an appliance can have variants with another place in the
  priority list, for example a higher priority in the morning.
- **Excluded appliance:** the switch **‹appliance› excluded from regulation**
  takes an appliance out of the regulation. It keeps its place in the
  priority list, but is passed as if it was not there, and is turned off at
  the next decision if it is on. When it is included again while appliances
  below it are on, the lowest of them is turned off to make room for it.
- **Penalty:** when the average consumption goes above the power limit plus
  the penalty threshold, every appliance is kept off until the overconsumption
  is recovered, and the regulation then starts again. The penalty is a safety
  valve and should normally never happen.
- **Safe state:** when the power sensor has had no valid value as two
  regulation windows in a row closed, every appliance is kept off. A single
  missing value is tolerated. When the sensor gives a valid value again, the
  regulation starts again.

Kraftvakt does not know what an appliance actually uses, and does not read
whether it is on. It assumes the appliances are as Kraftvakt last set them. Do
not turn regulated appliances on or off outside Kraftvakt. It can disturb the
regulation, affect appliances with higher priority and trigger a penalty.
Exclude the appliance from the regulation instead. EV chargers are the
exception: Kraftvakt reads whether they are actively charging and whether a
car is connected.

## Starting and stopping

The regulation starts by itself when Home Assistant or the integration starts,
provided the configuration is complete:

- a power sensor is chosen,
- every appliance has an entity and actions to turn it on and off,
- when EV charging control is on, every EV charger has an entity, actions to
  activate, deactivate and set the charging current, and **Actively
  charging**, and also **Car connected** when only one EV charger may charge
  at a time.

When Home Assistant starts, the regulation waits until Home Assistant has
finished starting, so the integrations of the appliances are loaded. If the
stored configuration (`.storage/kraftvakt.config`) cannot be read, Kraftvakt
does not start, the integration shows an error, and the file is left
unchanged.

Every start turns all appliances off at once, and deactivates all EV chargers
when EV charging control is on. The regulation then turns them on one by one
in priority order, with the first decision one full regulation interval after
the start. The regulation also starts again with everything off when a penalty
or the safe state ends, and at the next decision after the power limit is
changed with the **Power limit** entity, see [Entities](#entities).

The **Regulation** switch, and the button on the status page, stop and start
the regulation. Stopping turns all appliances off, and nothing is turned on
until it starts again. If the configuration is not complete, the switch stays
off and the attempt is logged. The switch has no stored state, so the
regulation runs again after a restart.

## EV charging

When EV charging control is on, Kraftvakt sets the charging current of each EV
charger one ampere at a time, by how much power is free. The place of
**EV charging** in the priority list decides where the EV chargers are in the
order. An EV charger charges only when Kraftvakt has activated it, so a car
that is connected does not start charging by itself. The charging current is
set to the minimum before the EV charger is activated or deactivated.

- **Actively charging** is read at every decision, from one of:
  - a sensor for charging power: above 100 W counts as charging. It may
    report W or kW,
  - a boolean entity: off counts as not charging, on as charging,
  - a template: the boolean value false counts as not charging, true as
    charging.

  Only evidence that the EV charger is not charging counts as not charging.
  An unavailable sensor or entity, and a template that fails or gives
  something else than true or false, count as charging, so an EV charger that
  may be charging is never taken for idle.
- An EV charger gets more than the minimum current only when it is actively
  charging. While it is being tried, the appliances below **EV charging** can
  be turned on.
- An EV charger that is not charging, because no car is connected or because
  it is not actively charging two regulation windows after it was activated,
  is bypassed. It gets no more than the minimum current, stays activated if it
  is, and does not stand in the way of other EV chargers.
- An EV charger that is not charging rests before it is tried again: 15
  minutes the first time, then 30, and then 60 minutes each time the car still
  does not charge. It stays bypassed while it rests. If the car is
  disconnected and connected again, or starts charging, it is tried at once.
- When only one EV charger may charge at a time, an EV charger that is
  actively charging may continue until it is done, and the others wait.
  **Car connected** is then required for every EV charger. Without it,
  Kraftvakt could only find a connected car by activating the EV charger, and
  EV chargers without a car would be activated in turn.
- Outside its charging window, an EV charger does not charge. The charging
  window can span midnight and follows the time zone of Home Assistant.
- The switch **‹charger› override charging window** lets the EV charger
  charge outside the charging window until the next charging window has
  started, even if the regulation has been stopped or in safe state
  meanwhile. After a restart of Home Assistant, this is counted from the
  first start of the regulation.

## The panel

The panel has a menu at the top with the status page and four configuration
pages. Only administrators have access.

Changes are collected in a draft. **Save** stores everything at once, and
**Discard** goes back to what is stored. Errors are shown at the field, and
nothing is saved until they are fixed. The panel asks before unsaved changes
are discarded when you go to the status page, and the browser asks when the
page is closed. The configuration can only be changed while the regulation is
stopped. While it runs, the configuration pages are locked and show the
**Stop regulation** button. A saved configuration is used the next time the
regulation starts.

### Configuration pages

- **General:** power sensor, power limit, turn-on margin, regulation window,
  regulation interval, waiting time at the power limit and penalty threshold.
  The helper text under each field shows the valid range and the default.
- **Appliances:** the priority list, with the most important appliance at the
  top. Drag the handle to change the order. **Add appliance** and the pencil
  open a dialog with the entity, the actions to turn it on and off, an
  optional power reserve, and variants. A variant has a label and an
  expression, either a boolean entity or a template, and is a separate entry
  in the priority list. The top true expression applies. The current result
  of a template is shown under it. When EV charging control is on, **EV
  charging** is in the list and can be moved like an appliance.
- **EV charging:** EV charging control on or off, one EV charger at a time,
  and the EV chargers in charging priority. The dialog for an EV charger has
  the entity, the actions to activate, deactivate and set the charging
  current, the minimum and maximum charging current, the power reserve, car
  connected, actively charging, and the charging window. When EV
  charging control is off, the EV chargers are kept but can only be viewed.
- **Advanced:**
  - **Waiting time curve:** two sliders, steepness and pivot point, with a
    table and a curve showing how much of the waiting time an appliance waits
    by how much power is free (the power limit minus the regulation average).
    The pivot point is free power as a percentage of the power limit. The
    table also shows the actual waiting time, rounded up to the regulation
    interval, since the appliance is turned on at the first decision after
    the waiting time. The table is hidden on a narrow screen.
  - **Waiting time on repeated turn-on:** step (× 0.25, × 0.5, × 0.75 or × 1)
    and number of steps (1–9), for appliances and for EV chargers, each with a
    table of the waiting time for each turn-on in a row.

### Actions

For each action you can choose **Standard** when the domain of the entity has
a standard action (for example `switch.turn_on` and `switch.turn_off`), or
create a custom action with the action editor of Home Assistant, see
[Template and action examples](#template-and-action-examples). For **Set
charging current** you can also choose **Entity** and a `number` or
`input_number` entity, which then gets the charging current as its value. A
failed action is logged, and the regulation continues without retrying. An
entity used by another appliance or EV charger cannot be chosen.

### Status page

The status page shows whether the regulation runs and has the button to start
and stop it. If the configuration is not complete, it lists what is missing,
with a link to the page where it is fixed. While the regulation runs, it also
shows:

- the average consumption and the regulation average against the power limit,
  and the consumption now. The bar shows the consumption now, with a marker
  for each average and for the power limit,
- a ring that empties towards the next decision,
- safe state and penalty periods when they occur, with the overconsumption
  left and whether it has started to be recovered,
- the priority list with the current variant of each appliance. The icon of
  an appliance that is on is yellow, as in Home Assistant, and an excluded
  appliance is dimmed. Under **EV charging**, the EV chargers are listed in
  the current charging priority with the charging current and one mark per
  ampere from the minimum to the maximum current, filled up to the current
  one. **EV charging** shows how many EV
  chargers are charging, for example «2 / 5»,
- a label on each row: **Excluded**, **On** or **Off** for an appliance, and
  for an EV charger the most important of **First decision**, **Excluded**,
  the charging window (for example «22–06») when outside it, **No car
  connected**, **Not charging**, **Queued**, **Override**, **Charging**,
  **Activated** or **Deactivated**. Hover over a label or an icon for the full
  explanation,
- a dashed line under the last entry that is on. Here the power is used up,
  and what is below waits for free power. The line shows the free power and
  its share of the power limit, for example «5.00 kW (50 %) free». It is not
  shown when everything is off, or when everything that is not excluded is
  on. **EV charging** counts as on when an EV charger is activated and not
  bypassed,
- a bar that empties evenly until the decision where the next appliance, or
  one more ampere, is turned on.

On a narrow screen, the bar for the next turn-on and the charging current in
numbers are hidden.

## Entities

All entities belong to the service device **Kraftvakt**.

| Entity | Description |
|---|---|
| **Regulation** | |
| `switch.kraftvakt_regulation` (Regulation) | On while the regulation runs. Turn off to stop the regulation, and on to start it again. |
| `binary_sensor.kraftvakt_regulation_safe_state` (Regulation safe state) | On while the regulation is in safe state. Can trigger an automation that notifies you. |
| `sensor.kraftvakt_regulation_steps_on` (Regulation steps on) | Diagnostic. The number of steps that are on: each appliance is one step, and each ampere of an EV charger, from the minimum current up, is one step. |
| **Power** | |
| `number.kraftvakt_power_limit` (Power limit) | The power limit in W, the same as in the panel. Can also be set while the regulation runs, see below. |
| `sensor.kraftvakt_power_regulation_average` (Power regulation average) | The regulation average in kW. |
| `sensor.kraftvakt_power_hourly_average` (Power hourly average) | The average consumption over the last hour in kW. |
| `sensor.kraftvakt_power_free` (Power free) | Diagnostic. The power limit minus the regulation average, in kW. Negative above the power limit. |
| **Waiting time** | |
| `sensor.kraftvakt_waiting_time_remaining` (Waiting time remaining) | Diagnostic. Seconds until the decision where the waiting appliance or ampere is turned on, 0 when nothing waits. |
| `sensor.kraftvakt_waiting_time_next_turn_on` (Waiting time next turn-on (calculated)) | Diagnostic. The waiting time in seconds the next turn-on gets from the last regulation average and the waiting time curve, without the growth on repeated turn-on. |
| **Penalty** | |
| `binary_sensor.kraftvakt_penalty_active` (Penalty active) | Diagnostic. On during a penalty period. |
| `sensor.kraftvakt_penalty_overconsumption` (Penalty overconsumption) | Diagnostic. The overconsumption in Wh at the last decision: the net energy above the power limit since the average consumption went above it. 0 when there is none. |
| **Appliance** | |
| `switch.kraftvakt_appliance_<appliance>_excluded` (‹appliance› excluded from regulation) | One per appliance. Turn on to take the appliance out of the regulation, so it is never turned on. |
| **EV charger** | |
| `switch.kraftvakt_charger_<charger>_excluded` (‹charger› excluded from regulation) | One per EV charger. Turn on to take the EV charger out of the regulation, so the car never charges. |
| `switch.kraftvakt_charger_<charger>_window_override` (‹charger› override charging window) | One per EV charger. Turn on to let the EV charger charge outside the charging window. Turns itself off when the next charging window has started. |

The sensors are updated every time a regulation window closes. The sensors
that depend on the averages are unavailable until the first regulation window
has closed, and after two regulation windows in a row closed without a valid
value from the power sensor, also while the regulation is stopped. When the
power sensor gives a valid value again, the measurements from before are kept,
and the time without a valid value is counted with the last valid value before
it.

When Kraftvakt starts, the hour before is read from the history of the power
sensor in the Home Assistant recorder, so the average consumption is right
also just after a restart. The time Home Assistant was down is counted with
the last value before it stopped. Without history, the first measurement is
used back in time.

A new value in **Power limit** is stored at once. While the regulation runs,
it starts again with the new power limit at the next decision, and an ongoing
penalty ends. Several changes before the next decision give one restart, and a
value equal to the power limit in use does nothing. The status page shows the
power limit in use.

The appliance and EV charger switches can be used while the regulation runs
and apply from the next decision. Their state is stored at once and kept over
a restart. While EV charging control is off, the EV charger switches are
unavailable, but their state is kept.

The entity IDs are the same in every language and are grouped by what they
concern: `regulation`, `power`, `waiting_time`, `penalty`, `appliance` and
`charger`. The names shown follow the language of Home Assistant. ‹appliance›
is the name of the entity of the appliance. ‹charger› is the name of the
device the entity of the EV charger belongs to, or the name of the entity when
it has no device. The entity ID keeps the name from when the appliance or EV
charger was added.

## Template and action examples

Templates use the template language of Home Assistant (Jinja2), and actions
are the same as in automations and scripts. In the action editor you can
switch to YAML from the ⋮ menu and paste the examples. Every template and
action gets the variables `entity_id` (the entity of the appliance or EV
charger) and `entity` (its state object, for example `entity.state` and
`entity.attributes`), so the templates keep working when the entity is
replaced. The action for the charging current also gets `current`,
`min_current` and `max_current`. `current` is always between the minimum and
maximum charging current.

A template is true only when it gives the boolean value true. Anything else,
including an error in the template, counts as false. An entity is true only
when it is `on`.

**Variant «Morning»** that gives the water heater a higher priority between
05 and 08:

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

**Actively charging** from a sensor with the charging current the
charger reports:

```jinja
{{ states('sensor.garage_charger_current') | float(0) > 1 }}
```

When the sensor is unavailable, `float(0)` gives 0 and the template gives
false, so the EV charger counts as not charging. Leave out the default,
`| float`, to let an unavailable sensor count as charging instead.

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

**Set charging current** with a service from the charger's integration that
takes the current per phase. `my_charger.set_current` is an example; use the
service and fields of your charger's integration:

```yaml
- action: my_charger.set_current
  data:
    charger_id: garage
    phase1: "{{ current }}"
    phase2: "{{ current }}"
    phase3: "{{ current }}"
```

## Development

Requires Python in the version in `pyproject.toml`, the same as the Home
Assistant version in `requirements_dev.txt` requires, and
[uv](https://docs.astral.sh/uv/). The development dependencies are in
`requirements_dev.txt`.

```bash
uv venv --python 3.14
uv pip install -r requirements_dev.txt
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The code is in `custom_components/kraftvakt/`. The regulation is plain Python
without Home Assistant in `regulation/`, and `runtime.py` connects it to Home
Assistant. The tests are in `tests/`, with unit tests in `tests/unit/`. The
simulator is in `simulator/`, with its tests in `tests/simulator/` and
`tests/unit/simulator/`.

### Panel

The panel is written in Lit and TypeScript in `frontend/` and built with
Node.js, in the version in `.nvmrc`, the same as the Home Assistant frontend
uses. Install and activate it with [nvm](https://github.com/nvm-sh/nvm) or
[nvm.fish](https://github.com/jorgebucaran/nvm.fish):

```bash
nvm install
```

```bash
nvm use
```

The built bundle, `custom_components/kraftvakt/frontend/kraftvakt-panel.js`,
is committed, because HACS installs straight from the repository. Build it
again after every change in `frontend/`, and commit the source and the bundle
together. CI fails if the committed bundle does not match the source.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

`npm run watch` builds again on every change. The bundle is loaded with the
version from `manifest.json` in the URL, so the browser may use an old bundle
after a new build. Reload the page without cache then. The texts of the panel
are in `frontend/src/translations/` (English and Norwegian) and follow the
language of the user in Home Assistant.

### Dependencies

Every dependency is pinned, and most follow Home Assistant:
`pytest-homeassistant-custom-component` decides the version of Home Assistant
and pytest, Home Assistant decides the frontend, ruff and Python, and the
Home Assistant frontend decides Node, Lit, TypeScript and `@mdi/js`. The other
build tools of the panel and the GitHub actions get their newest release.
Update them all with Node active:

```bash
uv run scripts/update_dependencies.py
```

The script prints what changed. Then install again, activate the new Node,
and run the checks and the panel build:

```bash
uv pip install -r requirements_dev.txt
nvm install
```

### Releasing

Versions follow [SemVer](https://semver.org/). A release is made from an
up-to-date `main` with a clean working tree and Node active:

```bash
uv run scripts/release.py 0.2.0
```

The script runs the checks, sets the version in `manifest.json`,
`pyproject.toml` and the panel's `package.json` and lock file, commits, tags
`v0.2.0`, and asks before it pushes `main` and the tag. The tag starts the
release workflow, which checks the versions and creates a draft release on
GitHub. Write the release notes there and publish it; HACS offers only
published releases. A version with a pre-release part, like `0.2.0-beta.1`,
becomes a GitHub pre-release, which HACS offers only to users who turn on
pre-releases for Kraftvakt. The simulator is not part of a release.

### Local Home Assistant

Run a local Home Assistant against the repository. `config/custom_components/`
is a plain folder with one link to Kraftvakt and one to the simulator:

```bash
mkdir -p config/custom_components
ln -s ../../custom_components/kraftvakt config/custom_components/kraftvakt
ln -s ../../simulator/custom_components/kraftvakt_simulator config/custom_components/kraftvakt_simulator
uv run hass -c config
```

From the same machine you log in without a password at http://127.0.0.1:8123
(`trusted_networks` for `127.0.0.1` and `::1` in `config/configuration.yaml`).
Other machines require a password.

### Simulator

The simulator makes it possible to test Kraftvakt without a HAN port and real
appliances. It is a separate integration, **Kraftvakt simulator**, in
`simulator/custom_components/kraftvakt_simulator/`. It is outside
`custom_components/`, so HACS does not install it, and it is only used with a
local Home Assistant.

Add the integration under **Settings → Devices & services**, and add one
device at a time with **Add device**:

- **HAN:** the power of the house, the background power plus the power of all
  the simulated devices (`sensor.han_power` when the device is named «HAN»).
  There can be only one HAN.
- **Heating device:** heating cable, water heater or panel heater, with power
  (W), duty cycle (0–100 %) and period (minutes). It has a switch and a power
  sensor. While the switch is on, it heats in a fixed cycle that starts with
  the on part: 750 W, 25 % and 60 minutes give 15 minutes on and 45 minutes
  off, over and over. The cycle starts again every time the switch is turned
  on or the cycle is changed. With the switch off, it uses nothing.
- **EV charger:** three-phase 400 V with a minimum and maximum current. It has
  the switches **Charging allowed**, **Car connected** and **Car fully
  charged**, **Charging current** (A), the sensor **Charging power** and the
  binary sensor **Charging**, on while it draws power. It
  draws √3 × 400 V × the charging current (6 A gives 4.16 kW) when charging
  is allowed, a car is connected and the car is not fully charged.

Heating devices and EV chargers also have the switch **Unplugged**. While it
is on, the device uses nothing, whatever the other switches are set to. The
cycle of a heating device runs on while it is unplugged.

What controls the simulation and does not belong to a real device is under
**Configuration** on the device page, and can be changed while Home Assistant
runs: **Background power**, **Heating power**, **Duty cycle**, **Period**,
**Car connected**, **Car fully charged** and **Unplugged**. The settings can
be changed with **Reconfigure**. The switches and the charging current keep
their state over a restart.

Then set up Kraftvakt against the simulator: the power sensor of the HAN as
the power sensor, the switches of the heating devices as appliances, and for
each EV charger (the entity IDs follow the language of Home Assistant when
the device is added):

| Field in Kraftvakt | Value |
|---|---|
| Entity for allowed charging | `switch.<charger>_charging_allowed` |
| Activate and Deactivate | Standard |
| Set charging current | Entity: `number.<charger>_charging_current` |
| Actively charging | Charging power: `sensor.<charger>_charging_power`, or Entity: `binary_sensor.<charger>_charging` |
| Car connected | `switch.<charger>_car_connected` |

Change the background power and the switches for the car, and watch the
regulation on the status page.

### WebSocket API

The panel talks to the integration over its own WebSocket commands. All of
them require an administrator.

| Command | Does |
|---|---|
| `kraftvakt/capabilities` | Gives the standard actions per field, the limits and the defaults. |
| `kraftvakt/config/get` | Gives the configuration, the names of the entities and what is missing. |
| `kraftvakt/config/save` | Stores the whole configuration. Refused while the regulation runs. An invalid configuration is not stored, and the response gives the errors per field. |
| `kraftvakt/regulation/set_running` | Starts or stops the regulation, as the **Regulation** switch. |
| `kraftvakt/status/subscribe` | Sends the status at once and then for every regulation window, every decision, and on start, stop and save. |

### Logo and icon

The sources are in `assets/brand/`. The PNG files in
`custom_components/kraftvakt/brand/` (loaded directly by Home Assistant from
2026.3) are built with:

```bash
uv run --with cairosvg --with pillow scripts/build_brand.py
```

## License

[MIT](LICENSE)
