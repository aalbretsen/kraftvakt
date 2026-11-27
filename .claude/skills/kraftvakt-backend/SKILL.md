---
name: kraftvakt-backend
description: Architecture of the Kraftvakt integration in custom_components/kraftvakt - modules and their responsibilities, the stored configuration format,
  validation and completeness, actions and template variables, entities, the WebSocket API and the status snapshot the panel uses.
  Use before changing Python code in custom_components/kraftvakt or the messages between the panel and the backend.
---

# Kraftvakt backend

What the regulation must do is in the `kraftvakt-regulation` skill. This file is about how the integration is built. Follow Home Assistant's standards for integrations.

## Decisions

- The regulation logic in `regulation/` is pure Python without Home Assistant imports. It takes a snapshot of the inputs and returns an ordered list of commands.
  Time is passed in, never read from a clock.
- The configuration is kept in its own `Store` (`.storage/kraftvakt.config`), written atomically, not in `config_entry.options`.
  The config entry is empty and the config flow asks for nothing. A stored configuration that cannot be read stops the setup with an error and leaves the file alone.
- The panel talks to the backend with own WebSocket commands, all `require_admin`.
- The panel edits a local draft and saves the whole configuration at once.
- The entities of appliances and chargers are added and removed when the configuration is saved, without reloading the config entry (a reload would start the regulation).
  Registry entries of removed items are removed.
- A charger is a device in HA, stored as its `device_id`, without an entity of its own. Every entity it names (the on/off entity, the set-current entity,
  the entities of car connected, car charging, the charging power and the fault flag) must belong to that device.
  Templates and custom actions are not checked, and cover a charger whose values are elsewhere.
- The display sensors of an appliance must belong to the device of its entity, `entity_not_on_device` otherwise; templates are not checked.
  An appliance whose entity has no device, as a helper or a template switch, may show any sensor.
  Why: integrations group a charger's entities as a device, so picking them from it keeps the setup easy for most users.
- A charger is named after its device (the user's name for the device first), and after its on/off entity while the device is missing or unknown;
  an appliance is named after its entity.
  The status, the entity names sent to the panel and the charger switches use the same function for this, and the panel mirrors it for a charger that is not saved yet.
  Why: the on/off entity often has a name like «Garage Charging allowed».
- The entity Kraftvakt turns on and off (`controlled_entity`) is an appliance's entity, or a charger's on/off entity while it is switched by it.
  It is unique in the configuration, is reported when it no longer exists, and names the item in the panel.
- Templates and actions run with HA's `Template` and `Script`.
- The configure button of the integration opens the panel through `config_panel_domain` when the panel is registered.
- The action lock is shared over reloads, so a new runtime's turn-off commands wait until the previous runtime's actions are done.
- The diagnostics hold everything the backend keeps in memory. The configuration is in its own section, and what is looked up from it is left out.
  A part shows a setting only when it keeps its own copy, such as the power limit the engine uses and the action runner's timeout.
  Callbacks and handles are shown as whether they are set.
  Each object that holds state describes its own with `diagnostics()`, in its own types, and the runtime gives a section per part.
  `plain` in `json_values.py` turns it into JSON: times in ISO 8601 in HA's time zone, durations in seconds, enums as their values, sets as sorted lists and dataclasses as objects.
  A type it does not know is an error, so the black box tests of the diagnostics find it before a release.
  The decision records are kept as JSON from the start. Commands carry their kind, since some kinds have the same fields.
  State added to the backend is added to its object's `diagnostics()`.
- The diagnostics also hold the recorded history of the last 24 hours of every entity the regulation reads and sets, read from the recorder at the download,
  so the switching of the appliances and chargers can be analysed without keeping it in memory.
  Read: the power sensor, the conditions the regulation reads (`regulation_conditions`: the variants', and the fault flag only with deactivate on fault, not the display values),
  the expression of one at a time of a charger group, under the group's id,
  and the entities of a template as it renders at the download.
  Set: each item's `controlled_entity`, and the entities of its actions (`action_entities`): the target of a default, entity or domain action,
  and the entities a custom action names outside templates, from HA's `Script.referenced_entities`.
  Kraftvakt's own entities are there too, except those that change at every window, which the power sensor's history covers.
  The entities that are set come with their attributes, since an action may set one, such as a thermostat's temperature; the others without, to keep the file small.
  The recorder gives the state at the start and the significant changes after it, so an attribute change counts only in the domains where the recorder keeps them, such as climate.
- The panel's diagnostics page shows what the diagnostics hold, but the recorded history, and nothing is kept for it alone.

## Modules

| Module | Responsibility |
|---|---|
| `__init__.py` | Setup, WebSocket commands, panel and static path, platforms. |
| `config_flow.py` | Empty flow, single instance. |
| `config_model.py` | Dataclasses, defaults and setting ranges (used for validation and sent to the panel), serialization and issues. |
| `config_reader.py` | Reads stored and received data into the model and collects type errors. |
| `config_validation.py` | Validation and completeness. Parsing a configuration from the panel must run in the event loop, since templates are checked there. |
| `storage.py` | Configuration and charger switch positions in one versioned file. |
| `measurement.py` | Time-weighted averages, each measurement covering at most one update interval back, the sliding hour, W/kW, fill at startup, averages unknown after two invalid closes, skipping missed windows, and the window clock that keeps the windows in step with the updates. Pure Python. |
| `report_analysis.py` | How the power sensor reports, from the times of its updates over the last hour: the update interval, whether the updates are steady, the shortest interval, the longest silence and the lost updates, and the power sensor timeout suggested for it. Pure Python. |
| `conditions.py` | True/false from an entity, the states of an entity or a template, both as a value and as evidence of true or false, and the charging power from a power sensor or a template. |
| `devices.py` | The device of a charger: its name, the device of an entity, and the check that a charger's entities belong to its device. |
| `charger_profiles/` | The charger profiles: `profile.py` describes a profile, `recognition.py` finds the profile of a device and fills a charger from it, `device_description.py` describes a charger's device for the diagnostics, and `profiles/` has one module per profile, listed in `PROFILES`. |
| `actions.py` | The table of default actions, custom actions, the checks of actions against their entities, and the action runner (one command at a time under a lock, commands that wait merged, errors logged and not retried). |
| `domain_actions.py` | The table of domain actions, their parameters, script steps and checks. |
| `regulation/` | The engine (`start`, `stop`, `decide`), the model, steps and ampere steps, waiting, penalty and charging. |
| `power_measurement.py` | Follows the power sensor in HA (with the hour before from the recorder and the power sensor timeout), keeps the times of its updates over the last hour and learns its update interval from them, closes the windows by the window clock, at an update or by the clock, skips the missed ones, tells its listeners, and reports a silence close to the timeout. Also analyses a sensor it does not follow, from its history or by listening. |
| `decision_clock.py` | Counts the closed windows to decisions, and when the next decision and the one that ends a waiting time are expected. Pure Python. |
| `decision_input.py` | Reads the conditions, the chargers and the user's switches into the input of a decision. |
| `runtime.py` | Connects the engine to HA: makes a decision when the decision clock says so, runs the commands in a background task, repeats commands, starts when HA has started, saves configuration changes, keeps the last failed actions for the diagnostics, and gives the state of each of its parts for them. |
| `settings.py` | The one owner of the stored configuration and the positions of the user's switches, saved together, and which window overrides are armed and which chargers charged in window (memory only). |
| `websocket_api.py` | The WebSocket commands. |
| `status.py` | The status snapshot. |
| `entity.py`, `sensor.py`, `binary_sensor.py`, `number.py`, `switch.py` | The entities. The sensors and the binary sensors of the regulation are entity descriptions with a function of the runtime, updated by the status listener. `entity.py` also names appliances and chargers. |
| `item_entity.py` | The base of the entities per appliance or charger, and adding and removing them as the configuration changes. |
| `repairs.py` | Repair issues for problems the user fixes in the configuration: the regulation could not start, an entity of an appliance, charger or charger group no longer exists, and a power sensor silent for at least half its timeout. |
| `decision_log.py` | The decisions kept for the diagnostics: those of the hour before the last decision, the same hour as the measurements, and the commands before them, which are the commands of the last start with those of the later decisions that have left the hour, so what each appliance and charger was set to is known from the last start on. |
| `diagnostics_feed.py` | What the diagnostics page gets, per subscription: the health of the power sensor and the actions, how the power sensor has reported over the last hour, the start, when commands are repeated, the commands before the decisions, and the measurements and the decisions in parts, every one kept in the first and after a reload, then only the new ones. |
| `diagnostics.py` | The diagnostics: configuration, status, a section for the state of each part of the runtime, the decisions with the commands before them and the last failed actions, kept in memory by the runtime, the device of each charger, described so a charger profile can be written from it, and the recorded history. The diagnostics tools in `diagnostics/` read `config`, `charger_devices` and `history`, see the `kraftvakt-diagnostics` skill. |
| `recorded_history.py` | The recorded history of the last 24 hours of the entities the regulation reads and sets, and Kraftvakt's own entities, with what uses each of them, for the diagnostics. |
| `json_values.py` | `plain`, which turns the state held in memory into JSON for the diagnostics. |

## Stored configuration

The format is defined by the dataclasses and their serialization in `config_model.py`, and by `config_reader.py`. Top-level sections:

- `general`: the power sensor and every general setting, also those shown on the panel's Advanced page.
  The regulation window is a length in seconds (`regulation_window_s`). The update interval of the power sensor is not stored, since it is learned while running.
- `appliances`: each with an id, its entity, its turn-on and turn-off actions, essential, an optional power reserve,
  its variants (id, label, condition and the actions it overrides), and the display power and display temperature.
  In a variant's actions, a key that is left out is not overridden, and a key with `null` is overridden but not set, so it is missing.
- `priority`: the priority list, with an entry per appliance and variant and an entry per charger group.
- `charger_groups`: each with an id, a name, one at a time, and its chargers in charging priority, each with an id, its device, how it is switched
  (`switched_by`: `on_off_entity`, `actions` or `current`), its on/off entity, the activate, deactivate and set-current actions, min and max current,
  power at minimum current (`min_current_power_w`), car connected, car charging (`actively_charging`), the charging power, an optional charging window,
  charge until disconnected, the override end, cloud-controlled, the start delay, deactivate on fault and its fault flag.
  A group has its name, one at a time and dynamic charging order. One at a time is a boolean, or an expression: a condition that is an entity or a template.
  A charger is nested in its group, so it cannot be in two.
- `appliance_switches`: the position of the excluded switch per appliance.
- `charger_switches`: the positions of the two switches per charger. Charge until disconnected is a field of the charger, not a switch position.

The store and the config entry are at version 1, without migrations.
Before the first stable release, the stored format and the entities change without migrations, and installations are set up again from scratch.

IDs are short UUIDs, so entities can change without losing the place in the list.
An action is `default`, `custom` (a script), `entity` or `domain` (the key of a domain action and a value per parameter, `null` while not chosen;
a temperature may be a template or a temperature source, see Actions and templates).
A condition is an entity or a template, and for car connected, car charging and the fault flag also the states of an entity (`states`, and `states_are_true`,
which is false when the chosen states count as false). The charging power and the display power are a power sensor or a template,
and the display temperature a temperature sensor, the current or target temperature of a climate entity (`current_temperature`, `target_temperature`, else `not_a_thermostat`),
or a template.
HA's action editor adds empty `data`; stored actions must tolerate that.

## Validation and completeness

An invalid configuration is not saved:

- The priority list has exactly one entry per appliance and variant, and one per charger group. Missing entries are added at the bottom.
  Duplicates and unknown entries are rejected.
- Labels are non-empty and unique per appliance. Group names are non-empty and unique among the groups.
- An essential appliance has no variants (`essential_with_variants` on `essential`) and no power reserve (`essential_with_power_reserve` on `essential`),
  and its entry is above every other entry (`essential_not_at_top` in `priority`).
  A missing entry of an essential appliance is added after the last essential entry, the others at the bottom.
- Charger ids are unique across all groups.
- The entity that identifies an appliance or charger is unique in the whole configuration. Sensors, conditions and actions may reuse entities.
- `1 ≤ min ≤ max` current, whole amperes. Charging window start ≠ end, whole minutes.
- Settings are checked against the setting ranges in `config_model.py`.
- Custom actions are checked with HA's script schema, templates for syntax.
  Whether a default action exists for the entity's domain is checked separately in `actions.py`, outside parsing; type errors must be fixed before that check can run.
  That a charger's device exists and its entities belong to it is checked the same way, against the registries, in `devices.py`.
  For a charger switched by its current, the entity its default or entity set-current action sets must take 0 A, as its `min` attribute tells,
  or the error is `current_off_unsupported` on `set_current`. An entity without a known `min`, and a custom action, are trusted.
- The `entity` action mode is only allowed for setting the charging current: it runs the default action of the chosen entity instead of the charger's own entity,
  so it must be a `number` or `input_number`. Why: most chargers have a number entity for the current.
- A value of the wrong type is reported and read as its default, so every other rule is still checked and all issues come back together; the default is not checked again.

An incomplete configuration can be saved, but the regulation cannot start. A charger without a device is missing, not an error.
An empty condition is missing, not an error; a variant is added in the appliance dialog and gets its expression in its own dialog.
Missing items and validation errors are both issues with a code, a section, a target (the id of the appliance or charger) and a field;
a variant field is addressed through the variant's id, also the variant's own actions (`variants.<id>.turn_on`),
and with deactivate on fault, a fault flag that is not given or empty is `missing_fault_flag` on `fault_flag`. A state without a chosen state is missing.
A charger without a charging power is `missing_charging_power`; car charging is optional.
An empty expression of one at a time is `missing_condition` on `one_at_a_time` of a group with two chargers or more.
In a group with one, the expression does not apply (`ChargerGroup.sharing_applies`), so it is not checked, evaluated, recorded or a source of repairs.
A charger switched by its on/off entity without one is `missing_on_off_entity`, and an on/off entity of a domain without a default action to turn on and off
is `unsupported_entity_domain`.
A charger's power at minimum current is at least 1000 W, since the regulation estimates from it what the charger draws per ampere,
and when its car may get more than the minimum current.
Every issue code needs a text in the panel's translations.

## Charger profiles

- A charger profile is data: one module per profile in `charger_profiles/profiles/` with a `PROFILE`, listed in `PROFILES`. The shared code sits next to that folder,
  so adding a profile changes no shared code. A device without a profile gets the default profile, which fills only cloud-controlled, as for a new charger,
  and keeps the start delay, since the user may have set it.
- The backend recognises and applies a profile, and the panel only applies the fields it gets back.
  Why: the backend sees the integration, manufacturer, model, translation keys and the integration's own entity names, and the panel keeps no knowledge of chargers.
- A device has a profile when its config entry is of the profile's integration, and its manufacturer and model ID match where the profile names them.
  The first profile in `PROFILES` that fits is used, so profiles must not overlap.
- An entity is found by what does not change with the language: its translation key, the name the integration gives it (for integrations that do not translate),
  or as the main entity, without a name of its own. Only enabled entities count. A field is left out when its entity is missing or not the only one that fits,
  and so is a template that names such an entity. `$name` in a profile's template is replaced by the entity ID of the entity `name`.
- A profile has a charging power, and may have a car charging condition and a fault flag.
  It has an on/off entity or actions to activate and deactivate, unless the charger is switched by its current.
  It always fills how the charger is switched, cloud-controlled and the start delay, the last with the charger default when the profile leaves it out,
  so choosing a device with a profile never keeps the settings of the charger's previous device.
  The other settings, such as the currents, the power at minimum current and the charging window, are not part of a profile and follow the standard defaults.
  It fills the fault flag, with its setting for deactivate on fault, only when it finds it,
  so choosing a device never turns the setting on without a flag.
- The actions and templates of a profile use `device_id`, so one profile works for every charger of its kind.
- A profile is not validated when it is loaded; its test saves a charger made from it, which the backend must accept.
- `DeviceEntities` finds entities in anything with an entity ID, a domain, a translation key and an original name, so the charger profile extractor in `diagnostics/`
  finds them with the same code in the entities a diagnostics file describes.

## Actions and templates

- A default action exists for switch-like domains (turn on and off) and for number-like domains (set value, for the charging current).
  The table is in one place in `actions.py` and is sent to the panel, and the `entity` mode and a charger's on/off entity use the same table.
- A charger has no entity of its own, so its actions to activate and deactivate are custom, and its set-current action an entity or custom.
  Any other mode is `invalid_type`, and the panel gets no domain actions for a charger.
- A domain action is a service of the entity's domain with values the user chooses, such as the thermostat actions (HVAC mode, temperature, or both).
  The panel renders the parameters from the table in `domain_actions.py` and has no code per domain. The keys start with the domain.
  - A domain action may be suggested: the panel chooses it for a new entity of its domain, before the default action, and a domain has at most one in each field.
    Setting the HVAC mode is suggested for thermostats, since most thermostats are better controlled by their mode than turned on and off.
  - A parameter has a type (an option or a temperature) and names the entity's attributes that hold its options and range.
    The default option is the first preferred option for the action kind that the entity supports, worked out in the panel; a number parameter has a fixed default.
    The temperature defaults to 0, outside every thermostat's range, so the user must set it.
    A temperature may also be a template, rendered with the item's variables when the action runs; it is checked for syntax, not against the range,
    and an empty one is missing. An option is never a template.
  - A temperature may also be a temperature source, `{"type", "value"}` with the types of a display temperature but no template:
    the state of a sensor, `input_number` or `number` (`temperature_sensor`, else `unsupported_entity_domain`),
    or the current or target temperature of a climate entity (else `not_a_thermostat`). One without an entity is missing.
    It is read only when the action runs, at a command or a command repeat, so its script is not kept.
    The value is converted to HA's unit when the entity has another temperature unit, and moved inside the range of the thermostat.
    Without a value the action fails as any failed action.
  - At save, the domain action must belong to the domain of the entity and the action kind, every parameter must be present,
    and the values must be of the right type and among the options or within the range the entity reports. Without the entity's state, only the types are checked.
    A value that is not chosen (`null`) is missing, not an error. Issues for a parameter are addressed as `<field>.<parameter>`.
- The commands for an appliance carry its current variant, and the action runner runs the variant's action if it overrides it, otherwise the appliance's.
- All templates and actions of an appliance get `entity_id` and `entity` (the state object of its entity, `none` when missing),
  and those of a charger `device_id`, since a charger has no entity of its own.
  The expression of a charger group gets `power_limit`, the power limit in W from the stored configuration, so a change from the power limit entity applies at the next decision.
  The runtime evaluates it in the decision input, and the engine gets a boolean per group, as for the variants.
  The set-current action also gets `current`, `min_current` and `max_current`; `current` is clamped between min and max,
  except 0 A for a charger switched by its current that is deactivated.

## Entities

- All belong to one service device, Kraftvakt, and use `has_entity_name` and `translation_key`. The unique id and the translation key are the key.
- The entity ids are technical, English in every language, and grouped by prefix (`regulation_`, `power_`, `waiting_time_`, `penalty_`, `appliance_`, `charger_`).
  An entity suggests its object id (the key unless given), which HA prefixes with the device name. The names are grouped the same way, in every language.
- The averages, power free and the power limit are power in W, also as shown. The overconsumption is energy in Wh without a state class, since it is not a total.
  The waiting times are durations in seconds.
- The power limit entity and the charge until disconnected switch of each charger change the stored configuration, also while running.
  They save at once, through the settings, so configuration and switches are saved together.
  While running, the engine gets the new power limit for the next decision, and charge until disconnected reaches it in the charger readings.
- The runtime counts every change of the stored configuration in a config version, sent in the status, so the panel fetches the configuration again when an entity has changed it.
- The regulation switch has no stored position; it is the same function as start and stop in the panel.
  With an incomplete configuration, turning it on raises a translated `ServiceValidationError` and it stays off.
- Repair issues are only for problems in the configuration, never for an entity that is merely unavailable, since that is often a cloud service that is down.
  The regulation that could not start is reported when HA or the integration starts, also right after a fresh install with nothing configured, and cleared at any start.
  Removed entities are looked for at every start of the regulation and after every failed action.
  A silence of the power sensor close to its timeout is not persistent: it is found again after a restart.
  Removing the integration removes all its repair issues.
- The waiting time next turn-on sensor is disabled by default.
- Each appliance has an excluded switch, and each charger an excluded switch, a window override switch, a charge until disconnected switch (configuration,
  see above), a binary sensor for allowed to charge and a state sensor, keyed by the item's id, with an entity id from the slug of the item's name.
  The positions of the switches are stored.
  The charger entities do not depend on the group, so moving a charger to another group keeps them.
  The switches of appliances and chargers have entity category config, since they configure the item, the override included.
  The allowed to charge binary sensor and the state sensor of a charger have entity category diagnostic.
- Each charger has a state sensor, an enum sensor with the charger's state from the status snapshot and its labels as state translations,
  so `state_translated` gives the label in a template. Its icon and colours, colour names of the Home Assistant theme, are the `icon` property
  and the `color` and `badge_color` attributes, not icon translations, since a template cannot read those. They are left out of the recorder.
  `badge_color` is for a circle behind the icon in white: the same as `color`, but dark grey for grey and orange for amber, since white on them is hard to read,
  and grey and amber as an icon read better on a dark theme.
  Red is for what keeps a charger from charging until someone acts: stopped and fault.
  Amber is for a car that is connected and waits to be allowed: outside its charging window, queued and deactivated.
  Green is for an activated charger: activated and charging.
  The panel's chips for a charger use the same icons and colours, and its tests check them against a fixture made from the sensor's table.
- The allowed to charge binary sensor uses the engine's own permission rule with the clock, the switches and the charger's status after the last decision, updated by the settings,
  the status of the regulation and at every whole minute, since windows are in whole minutes.

## WebSocket API

All commands require an administrator. Commands that need the runtime fail with `not_loaded` when Kraftvakt is not loaded.

| Command | In | Out |
|---|---|---|
| `kraftvakt/charger_profile/get` | `device_id` | The name of the device's charger profile and the fields of a charger it fills, as stored; `null` and the fields of the default profile without one. Needs no runtime. |
| `kraftvakt/capabilities` | – | The default action (domains, service and data) and the domain actions (by key, with their parameters for the field's action kind) per section and field, limits per field (`max: null` means no upper limit), and defaults. |
| `kraftvakt/power_sensor/analysis` | `entity_id` | How the sensor reports, in seconds, with the power sensor timeout suggested for it: from the updates of the last hour when it is the power sensor Kraftvakt follows and its update interval is known, else from its history, or by listening for up to 30 seconds when the history shows no update interval. Needs no runtime. |
| `kraftvakt/config/get` | – | The configuration, the entity names and what is missing. |
| `kraftvakt/config/save` | `config` | Saved with the completed priority list and what is missing, or not saved with the errors. Refused with `regulation_running` while running, checked before validation. Errors are a result, not a WebSocket error, because HA's error cannot carry data. |
| `kraftvakt/regulation/set_running` | `running` | The new state. Start refused with `config_incomplete`. |
| `kraftvakt/status/subscribe` | – | Empty result, then status events: at once, at every window, decision, start, stop and save, and when missed windows are skipped. Survives a reload. Events may arrive before the result of another command on the same connection. |
| `kraftvakt/diagnostics/subscribe` | – | Empty result, then events for the diagnostics page at the same times as the status. The measurements and the decisions come in parts: a part replaces what the panel holds, or holds the items from the first one that may have changed, and tells from when items are kept. The last two measurements are sent again, since a new measurement at the same time replaces the last one and may merge it into the one before. |

A saved configuration is used from the next start without a reload.

## Status snapshot

Built in `status.py` and typed in the panel's `api.ts`; keep the two in step. Rules that are not obvious from the code:

- Power in W and energy in Wh. Times are ISO 8601 in HA's time zone.
- Averages are `null` until the first window.
- The next decision time is `null` while stopped. It and the decision that ends a waiting time are expected times, with the windows lasting the regulation window.
- `regulation_window_s` is the regulation window in seconds.
- `power_sensor_silent` tells that the power sensor has not reported for the power sensor timeout, since its state in Home Assistant keeps the last value.
- The penalty part holds whether a penalty is active, the overconsumption and whether recovery has started.
- The waiting fields are set only on the row of the next step while it waits: an appliance,
  or the charger of an ampere step that is damped or activated again, also a queued charger before a switch-over,
  and on the row of a starting charger while its start delay holds back the next step, or only its own next ampere step when nothing else can be turned on.
  `waiting_reason` tells which: the waiting time, the damping or the start delay.
  They hold when the waiting started, when it ends, and the decision that turns the step on, the first at or after its end.
  The engine keeps a damped ampere step that is next, and a start delay that holds back the next step, as the waiting, with its reason,
  so the waiting time remaining sensor counts down to it as to any waiting, and the decisions kept for the diagnostics show why.
- The power to free from the last decision is set only on the row of the next step: its appliance, or the charger of its ampere step.
  It is `null` on the other rows, when the next step fits, and while a waiting holds the next step back, so one row tells what holds it.
- An appliance's variant is the label of its current variant, or `null`.
- The display values of an appliance, and the charging power of a charger, are read when the snapshot is built, `null` without a valid value.
  A temperature carries its unit: the sensor's, or Home Assistant's for a template.
- An appliance is excluded when it was excluded at the last decision, so it is false before the first decision after a start.
- A charger's state is the first that holds of: stopped (while the regulation is stopped), fault, first decision (before the first decision after a start),
  no car connected (bypassed), excluded, outside its charging window, queued (waiting and not activated), charging, starting, activated,
  override (allowed only by the override and deactivated), deactivated. It is worked out in the engine from the last decision,
  before its commands, so a charger activated at a decision shows its new state at the next one.
  Stopped comes before fault, since the fault flag is not read while the regulation is stopped.
  Fault comes next, since the user needs to know that the charger is broken.
  No car connected comes before the other reasons not to charge, since without a car nothing else matters.
  Charging is true while the charger is activated and was actively charging at the last decision.
  A starting charger also has when its start delay ends, `null` for the others.
- A charger group tells whether it was restricted to one charger at a time at the last decision, since it may follow an expression;
  false before the first decision and in a group with one charger.
- The priority list has one row per appliance, at the entry of its current variant, and one per charger group, with its chargers in the order of their ampere steps:
  the current charging priority, or with several at once and dynamic charging order the activated ones first, then the queued ones.
