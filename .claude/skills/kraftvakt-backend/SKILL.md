---
name: kraftvakt-backend
description: Architecture of the Kraftvakt integration in custom_components/kraftvakt - modules and their responsibilities, the stored configuration format, validation and completeness, actions and template variables, entities, the WebSocket API and the status snapshot the panel uses. Use before changing Python code in custom_components/kraftvakt or the messages between the panel and the backend.
---

# Kraftvakt backend

What the regulation must do is in the `kraftvakt-regulation` skill. This file
is about how the integration is built. Follow Home Assistant's standards for
integrations.

## Decisions

- The regulation logic in `regulation/` is pure Python without Home Assistant
  imports. It takes a snapshot of the inputs and returns an ordered list of
  commands. Time is passed in, never read from a clock.
- The configuration is kept in its own `Store` (`.storage/kraftvakt.config`),
  written atomically, not in `config_entry.options`. The config entry is empty
  and the config flow asks for nothing. A stored configuration that cannot be
  read stops the setup with an error and leaves the file alone.
- The panel talks to the backend with own WebSocket commands, all
  `require_admin`.
- The panel edits a local draft and saves the whole configuration at once.
- The entities of appliances and chargers are added and removed when the
  configuration is saved, without reloading the config entry (a reload would
  start the regulation). Registry entries of removed items are removed.
- A charger is named after the device of its entity (the user's name for the
  device first), and after the entity when it has no device; an appliance is
  named after its entity. The status, the entity names sent to the panel and
  the charger switches use the same function for this, and the panel mirrors
  it for a charger that is not saved yet. The entity that allows charging
  often has a name made of the device name and a word like "Charging allowed",
  which makes a poor name for the charger.
- Templates and actions run with HA's `Template` and `Script`.
- The configure button of the integration opens the panel through
  `config_panel_domain` when the panel is registered.
- The action lock is shared over reloads, so a new runtime's turn-off
  commands wait until the previous runtime's actions are done.

## Modules

| Module | Responsibility |
|---|---|
| `__init__.py` | Setup, WebSocket commands, panel and static path, platforms. |
| `config_flow.py` | Empty flow, single instance. |
| `config_model.py` | Dataclasses, defaults and setting ranges (used for validation and sent to the panel), serialization and issues. |
| `config_reader.py` | Reads stored and received data into the model and collects type errors. |
| `config_validation.py` | Validation and completeness. Parsing a configuration from the panel must run in the event loop, since templates are checked there. |
| `storage.py` | Configuration and charger switch positions in one versioned file. |
| `measurement.py` | Time-weighted windows, the sliding hour, W/kW, fill at startup, averages unknown after two invalid closes. |
| `conditions.py` | True/false from an entity or a template, and actively charging, which also takes a power sensor and counts missing evidence as charging. |
| `actions.py` | The table of default actions, custom actions, the checks of actions against their entities, and the action runner (one command at a time under a lock, errors logged and not retried). |
| `domain_actions.py` | The table of domain actions, their parameters, script steps and checks. |
| `regulation/` | The engine (`start`, `stop`, `decide`), the model, slots and fictive appliances, waiting, penalty and charging. |
| `runtime.py` | Connects the engine to HA: follows the power sensor, fills the hour before the start from the recorder in a background task (skipped when the recorder is not loaded), schedules windows at absolute times, counts windows to decisions, reads chargers and conditions at a decision, logs each decision at DEBUG, runs commands in a background task, start and stop, starts when HA has started, safe state, status listeners, saving the configuration. |
| `switch_board.py` | The positions of the user's switches for appliances and chargers, saved together with the configuration, and when the override was switched on (memory only). |
| `websocket_api.py` | The WebSocket commands. |
| `status.py` | The status snapshot. |
| `entity.py`, `sensor.py`, `binary_sensor.py`, `number.py`, `switch.py` | The entities. The sensors and the binary sensors of the regulation are entity descriptions with a function of the runtime, updated by the status listener. `entity.py` also names appliances and chargers. |
| `item_entity.py` | The base of the entities per appliance or charger, and adding and removing them as the configuration changes. |

## Stored configuration

The format is defined by the dataclasses and their serialization in
`config_model.py`, and by `config_reader.py`. Top-level sections:

- `general`: the power sensor and every general setting, also those shown on
  the panel's Advanced page.
- `appliances`: each with an id, its entity, turn-on and turn-off actions, an
  optional power reserve and its variants (id, label, condition).
- `priority`: the priority list, with an entry per appliance and variant and
  one EV charging entry.
- `charging`: enabled, one at a time, and the chargers, each with an id, its
  entity, activate, deactivate and set-current actions, min and max current,
  power reserve, an optional car connected condition, actively charging and
  an optional charging window.
- `appliance_switches`: the position of the excluded switch per appliance.
- `charger_switches`: the positions of the two switches per charger.

IDs are short UUIDs, so entities can change without losing the place in the
list. An action is `default`, `custom` (a script), `entity` or `domain` (the
key of a domain action and a value per parameter, `null` while not chosen). A
condition is
an entity or a template; actively charging may also be a power sensor. HA's
action editor adds empty `data`; stored actions must tolerate that.

## Validation and completeness

An invalid configuration is not saved:

- The priority list has exactly one entry per appliance and variant, and the
  EV charging entry exactly once while charging is enabled. Missing entries
  are added at the bottom. Duplicates, unknown entries and the EV charging
  entry while disabled are rejected.
- Labels are non-empty and unique per appliance.
- The entity that identifies an appliance or charger is unique in the whole
  configuration. Sensors, conditions and actions may reuse entities.
- `1 ≤ min ≤ max` current, whole amperes. Charging window start ≠ end, whole
  minutes.
- Settings are checked against the setting ranges in `config_model.py`.
- Custom actions are checked with HA's script schema, templates for syntax.
  Whether a default action exists for the entity's domain is checked
  separately in `actions.py`, outside parsing; type errors must be fixed
  before that check can run.
- The `entity` action mode is only allowed for setting the charging current:
  it runs the default action of the chosen entity instead of the charger's own
  entity, so it must be a `number` or `input_number`. Most chargers have a
  number entity for the current, and a custom action for it is needlessly
  hard.
- A value of the wrong type is reported and read as its default, so every
  other rule is still checked and all issues come back together; the default
  is not checked again. Why: the user sees every error at once, not one at a
  time.

An incomplete configuration can be saved, but the regulation cannot start.
Missing items and validation errors are both issues with a code, a section, a
target (the id of the appliance or charger) and a field; a variant field is
addressed through the variant's id. Every issue code needs a text in the
panel's translations.

## Actions and templates

- A default action exists for switch-like domains (turn on and off) and for
  number-like domains (set value, for the charging current). The table is in
  one place in `actions.py` and is sent to the panel, and the `entity` mode
  uses the same table for the chosen entity.
- A domain action is a service of the entity's domain with values the user
  chooses, such as the thermostat actions (HVAC mode, temperature, or both).
  The panel renders the parameters from the table in `domain_actions.py` and
  has no code per domain. The keys start with the domain.
  - A domain action belongs to action kinds, not sections, so it is offered
    wherever an action of that kind is, chargers included. Why: no special
    cases per section.
  - A parameter has a type (an option or a temperature) and names the
    entity's attributes that hold its options and range. The default option
    is the first preferred option for the action kind that the entity
    supports, worked out in the panel; a number parameter has a fixed
    default. The temperature defaults to 0, outside every thermostat's range,
    so the user must set it.
  - At save, the domain action must belong to the domain of the entity and
    the action kind, every parameter must be present, and the values must be
    of the right type and among the options or within the range the entity
    reports. Without the entity's state, only the types are checked. A value
    that is not chosen (`null`) is missing, not an error. Issues for a
    parameter are addressed as `<field>.<parameter>`.
- All templates and actions get `entity_id` and `entity` (the state object of
  the appliance's or charger's entity, `none` when missing). The set-current
  action also gets `current`, `min_current` and `max_current`; `current` is
  clamped between min and max.

## Entities

- All belong to one service device, Kraftvakt, and use `has_entity_name` and
  `translation_key`. The unique id and the translation key are the key.
- The entity ids are technical, English in every language, and grouped by
  prefix (`regulation_`, `power_`, `waiting_time_`, `penalty_`, `appliance_`,
  `charger_`).
  An entity suggests its object id (the key unless given), which HA prefixes
  with the device name. The names are grouped the same way, in every language.
- The averages, power free and the power limit are power in W, shown as kW
  for the sensors. The overconsumption is energy in Wh without a state class,
  since it is not a total. The waiting times are durations in seconds.
- The power limit entity saves at once, through the switch board so
  configuration and switches are saved together. While running, the runtime
  starts a new engine at the next decision when the engine's limit differs
  from the stored one.
- The regulation switch has no stored position; it is the same function as
  start and stop in the panel, and stays off and logs when the configuration
  is incomplete.
- Each appliance has an excluded switch, and each charger an excluded switch,
  a window override switch and a binary sensor for charging allowed by
  window, keyed by the item's id, with an entity id from the slug of the
  item's name. The positions of the switches are stored. The charger
  entities are unavailable while charging is disabled.
- The charging allowed by window binary sensor computes the window from the
  clock with the same function as the engine, updated by the switch board
  and at every whole minute, since windows are in whole minutes.

## WebSocket API

All commands require an administrator. Commands that need the runtime fail
with `not_loaded` when Kraftvakt is not loaded.

| Command | In | Out |
|---|---|---|
| `kraftvakt/capabilities` | – | The default action (domains, service and data) and the domain actions (by key, with their parameters for the field's action kind) per section and field, limits per field (`max: null` means no upper limit), and defaults. |
| `kraftvakt/config/get` | – | The configuration, the entity names and what is missing. |
| `kraftvakt/config/save` | `config` | Saved with the completed priority list and what is missing, or not saved with the errors. Refused with `regulation_running` while running, checked before validation. Errors are a result, not a WebSocket error, because HA's error cannot carry data. |
| `kraftvakt/regulation/set_running` | `running` | The new state. Start refused with `config_incomplete`. |
| `kraftvakt/status/subscribe` | – | Empty result, then status events: at once, at every window, decision, start, stop and save. Survives a reload. Events may arrive before the result of another command on the same connection. |

A saved configuration is used from the next start without a reload.

## Status snapshot

Built in `status.py` and typed in the panel's `api.ts`; keep the two in
step. Rules that are not obvious from the code:

- Power in W and energy in Wh. Times are ISO 8601 in HA's time zone.
- Averages are `null` until the first window.
- The power limit is the one the regulation uses now, which lags the stored
  one until the next decision after the power limit entity changed it while
  running.
- The next decision time is `null` while stopped.
- The penalty part holds whether a penalty is active, the overconsumption and
  whether recovery has started.
- The waiting fields are set only for the appliance or charger that is next
  and waiting (for a charger: its next fictive appliance): when the waiting
  started, when the waiting time ends, and the decision that turns it on, the
  first at or after the end of the waiting time.
- An appliance's variant is the label of its current variant, or `null`.
- An appliance is excluded when it was excluded at the last decision, so it
  is false before the first decision after a start.
- Charger details are from the last decision. Before the first decision after
  a start, a charger is not allowed and excluded is `null`. Charging is true
  while the charger is activated and was actively charging at the last
  decision. Window overridden is true while it was allowed to charge only
  because of the override. Car connected is `null` when it is not set or
  before the first decision.
- Appliances are sorted by the entry of their current variant, chargers by the
  current charging priority. The EV charging position is the number of
  appliances whose current variant is placed before the EV charging entry,
  `null` while EV charging is disabled.
