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
  imports. It takes a snapshot (`DecisionInput`) and returns an ordered list of
  commands. Time is passed in, never read from a clock.
- The configuration is kept in its own `Store` (`.storage/kraftvakt.config`),
  written atomically, not in `config_entry.options`. The config entry is empty
  and the config flow asks for nothing.
- The panel talks to the backend with own WebSocket commands, all
  `require_admin`.
- The panel edits a local draft and saves the whole configuration at once.
- Charger switches are added and removed when the configuration is saved,
  without reloading the config entry (a reload would start the regulation).
  Registry entries of removed chargers are removed.
- A charger is named after the device of its entity (the user's name for the
  device first), and after the entity when it has no device; an appliance is
  named after its entity. The status, `entity_names` and the charger switches
  use the same names (`item_name()` in `entity.py`), and the panel mirrors it
  for a charger that is not saved yet. Settled with the owner after the
  exploratory test: the entity that allows charging often has a
  name like «Garage Charging allowed».
- Templates and actions run with HA's `Template` and `Script`.
- The configure button of the integration opens the panel through
  `config_panel_domain` in `panel_custom.async_register_panel`. The panel turns
  `?config_entry=` into `/kraftvakt/appliances`.

## Modules

| Module | Responsibility |
|---|---|
| `__init__.py` | Setup, WebSocket commands, panel and static path, platforms. A stored configuration that cannot be read raises `ConfigEntryError` (`unreadable_configuration`) and leaves the file alone. The action lock lives in `hass.data[DOMAIN]` so it is shared over reloads. |
| `config_flow.py` | Empty flow, single instance. |
| `config_model.py` | Dataclasses, defaults, `SETTING_RANGES` (used for validation and sent to the panel), (de)serialization, `parse_config()` (must run in the event loop, templates are checked there), `missing_items()`. |
| `storage.py` | `KraftvaktStorage`: configuration and charger switch positions in one versioned file. |
| `measurement.py` | `PowerAverager`: time-weighted windows, sliding hour, W/kW, fill at startup, averages unknown after two invalid closes (history kept). |
| `conditions.py` | True/false from an entity or a template, with `entity_id` and `entity`. |
| `actions.py` | Default action table, custom actions, `ActionRunner` (one command at a time under a lock, errors logged and not retried), `default_action_issues()`. |
| `regulation/` | `engine.py` (`RegulationEngine`: `start`, `stop`, `decide`), `model.py`, `priority.py` (slots and fictive appliances), `waiting.py`, `penalty.py`, `charging.py`. |
| `runtime.py` | `KraftvaktRuntime`: follows the power sensor, fills the hour before the start from the recorder's history in a background task (`recorder` is an `after_dependency`; skipped when the recorder is not loaded), schedules windows at absolute times, counts windows to decisions, reads chargers and conditions at a decision, logs each decision at DEBUG (averages, safe state, penalty, waiting, commands), runs commands in a background task, start/stop, starts when HA has started, safe state, status listeners, `async_save_config()`. |
| `charger_switches.py` | `ChargerSwitchBoard`: switch positions, saving with the configuration, when the override was switched on (memory only). |
| `websocket_api.py` | The commands below. |
| `entity.py`, `sensor.py`, `binary_sensor.py`, `number.py`, `switch.py` | The entities. Sensors and binary sensors are entity descriptions with a function of the runtime, updated by the status listener. |

## Stored configuration

```json
{
  "general": {
    "power_sensor": "sensor.han_power",
    "power_limit_w": 10000,
    "turn_on_margin_w": 100,
    "regulation_window_s": 10,
    "regulation_interval": 1,
    "wait_at_limit_s": 300,
    "wait_curve_steepness": 6.0,
    "wait_curve_pivot": 80,
    "appliance_cycling_step_factor": 0.5,
    "appliance_cycling_steps": 4,
    "charger_cycling_step_factor": 1.0,
    "charger_cycling_steps": 5,
    "penalty_threshold_w": 100
  },
  "appliances": [
    {
      "id": "a1",
      "entity_id": "switch.varmtvannsbereder",
      "turn_on": { "mode": "default" },
      "turn_off": { "mode": "custom", "action": [ { "action": "switch.turn_off", "target": { "entity_id": "{{ entity_id }}" } } ] },
      "power_reserve_w": null,
      "variants": [
        { "id": "v1", "label": "Morgen", "condition": { "type": "template", "value": "{{ 5 <= now().hour < 8 }}" } }
      ]
    }
  ],
  "priority": [
    { "type": "appliance", "appliance_id": "a1", "variant_id": "v1" },
    { "type": "ev_charging" },
    { "type": "appliance", "appliance_id": "a1", "variant_id": null }
  ],
  "charging": {
    "enabled": false,
    "one_at_a_time": true,
    "chargers": [
      {
        "id": "c1",
        "entity_id": "switch.lader_garasje",
        "activate": { "mode": "default" },
        "deactivate": { "mode": "default" },
        "set_current": { "mode": "entity", "entity_id": "number.lader_garasje_strom" },
        "min_current_a": 6,
        "max_current_a": 16,
        "charge_power_sensor": "sensor.lader_garasje_effekt",
        "power_reserve_w": 4000,
        "car_connected": { "type": "entity", "value": "binary_sensor.lader_garasje_bil" },
        "charging_window": { "start": "22:00", "end": "06:00" }
      }
    ]
  },
  "charger_switches": { "c1": { "excluded": false, "window_override": false } }
}
```

IDs are short UUIDs, so entities can change without losing the place in the
list. The action editor adds `data: {}`; stored actions must tolerate that.

Validation (an invalid configuration is not saved):

- The priority list has exactly one entry per appliance and variant, and
  `ev_charging` exactly once while charging is enabled. Missing entries are
  added at the bottom. Duplicates, unknown entries and `ev_charging` while
  disabled are rejected.
- Labels are non-empty and unique per appliance.
- The entity that identifies an appliance or charger is unique in the whole
  configuration. Sensors, conditions and actions may reuse entities.
- `1 ≤ min_current_a ≤ max_current_a`, whole amperes. Charging window
  start ≠ end, whole minutes.
- Ranges and defaults from `SETTING_RANGES`.
- Custom actions are checked with HA's script schema and templates for syntax.
  Whether «default» exists for the entity's domain is checked by
  `default_action_issues()` in `actions.py` (it cannot be called from
  `parse_config()`). Type errors must be fixed before that check can run.
- An action is `default`, `custom` or `entity`. `entity` is only allowed for
  `set_current` (elsewhere it is `invalid_type`): it runs the default action
  of the chosen `entity_id` instead of the charger's own entity, so it must
  be a `number` or `input_number` (`unsupported_entity_domain` from
  `default_action_issues()`, `invalid_entity_id` when malformed, and
  `missing_action` while none is chosen). Settled with the owner: most
  chargers have a number entity for the current, and a custom action for it
  was needlessly hard.
- A value of the wrong type is reported and read as its default, so every
  other rule is still checked and all issues come back together; the default
  is not checked again. Settled with the owner after the exploratory test:
  one type error hid every other error.

An incomplete configuration can be saved, but the regulation cannot start.
Missing items and validation errors are issues:
`{"code": "missing_action", "section": "appliances", "target": "a1", "field": "turn_on"}`.
`section` is `general`, `appliances`, `priority`, `charging` or `chargers`,
and a variant field is `variants.<id>.label`. Missing codes:
`missing_power_sensor`, `missing_entity`, `missing_action`,
`missing_charge_power_sensor`, `missing_car_connected`.

## Actions and templates

| Domain | Turn on / activate | Turn off / deactivate | Set current |
|---|---|---|---|
| `switch`, `input_boolean`, `light`, `fan`, `climate`, `water_heater` | `<domain>.turn_on` | `<domain>.turn_off` | – |
| `number`, `input_number` | – | – | `<domain>.set_value` with `value: {{ current }}` |

The table is in one place in `actions.py` and is sent to the panel. The
`entity` mode of the set-current action uses the same table for the chosen
entity. All
templates and actions get `entity_id` and `entity` (the state object of the
appliance's or charger's entity, `none` when missing). The set-current action
also gets `current`, `min_current` and `max_current`; `current` is clamped
between min and max.

## Entities

All belong to one service device «Kraftvakt» and use `has_entity_name` and
`translation_key`.

| Entity | Unique ID | Notes |
|---|---|---|
| Regulation average (`sensor`, power, W shown as kW) | `regulation_average` | Updated when a window closes. Unavailable without an average. |
| Average consumption (`sensor`, power, W shown as kW) | `capacity_average` | Same. |
| Safe state (`binary_sensor`, problem) | `safe_state` | On in the safe state. |
| Power limit (`number`, power, W, box) | `power_limit` | The stored power limit. `async_set_power_limit()` in the runtime saves it at once (through the charger switch board, which saves configuration and switches together); while running, the runtime builds a new engine and starts it at the next decision when the engine's limit differs from the stored one. |
| Penalty (`binary_sensor`, problem, diagnostic) | `penalty` | On during a penalty period. |
| Overconsumption (`sensor`, energy, Wh, diagnostic) | `overconsumption` | 0 outside the overconsumption state. No state class: it is not a total. |
| Free power (`sensor`, power, W shown as kW, diagnostic) | `free_power` | Limit in use minus the regulation average. |
| Steps switched on (`sensor`, measurement, diagnostic) | `steps_switched_on` | `RegulationEngine.slots_on`: appliances on plus fictive appliances on. |
| Time to next turn-on (`sensor`, duration, s, diagnostic) | `time_to_next_turn_on` | `runtime.waiting_ends_at` minus now, whole seconds, 0 when nothing waits. |
| Waiting time from curve (`sensor`, duration, s, diagnostic) | `curve_waiting_time` | `RegulationEngine.curve_waiting_time()` for the last regulation average. |
| Regulation (`switch`) | `regulation` | No stored position. Same function as start/stop in the panel. Stays off and logs when the configuration is incomplete. |
| ‹charger› excluded from regulation (`switch`) | `charger_<id>_excluded` | Stored position. Unavailable while charging is disabled. |
| ‹charger› override charging window (`switch`) | `charger_<id>_window_override` | Stored position, set back when it ends. Unavailable while charging is disabled. |

## WebSocket API

All commands require an administrator (HA's `unauthorized` otherwise).
Commands that need the runtime fail with `not_loaded` when Kraftvakt is not
loaded.

| Command | In | Out |
|---|---|---|
| `kraftvakt/capabilities` | – | `{default_actions, limits, defaults}` |
| `kraftvakt/config/get` | – | `{config, entity_names, missing}` |
| `kraftvakt/config/save` | `config` | `{saved: true, config, missing}` or `{saved: false, errors}`. Refused with `regulation_running` while running, checked before validation. Errors are a result, not a WebSocket error, because HA's error cannot carry data. |
| `kraftvakt/regulation/set_running` | `running` | `{running}`. Start refused with `config_incomplete`. |
| `kraftvakt/status/subscribe` | – | Empty result, then status events: at once, at every window, decision, start, stop and save. Survives a reload (dispatcher signal). Events may arrive before the result of another command on the same connection. |

`default_actions` gives, per section and field, the domains with a default
action. `limits` gives `{min, max, step}` per field (`max: null` means no upper
limit). The saved `config` has the priority list completed. A saved
configuration is used from the next start without a reload.

Status snapshot:

```json
{
  "running": true,
  "missing": [],
  "safe_state": false,
  "penalty": { "active": false, "overconsumption_wh": 0.0, "recovery_started": false },
  "regulation_average_w": 7420.0,
  "capacity_average_w": 8100.0,
  "power_limit_w": 10000,
  "regulation_window_s": 60,
  "regulation_interval": 1,
  "next_decision_at": "2026-11-07T12:01:00+01:00",
  "appliances": [ { "id": "a1", "name": "Varmtvannsbereder", "on": true, "variant": "Morgen", "waiting_since": null, "waiting_until": null, "waiting_ends_at": null } ],
  "ev_charging_position": 1,
  "chargers": [ { "id": "c1", "name": "Lader garasje", "activated": true, "current_a": 9, "bypassed": false, "waiting": false, "allowed": true, "excluded": false, "charging": true, "window_overridden": false, "car_connected": true, "waiting_since": null, "waiting_until": null, "waiting_ends_at": null } ]
}
```

Times are ISO 8601 in HA's time zone. Averages are `null` until the first
window. `power_limit_w` is the limit the regulation uses now, which lags the
stored one until the next decision after the power limit entity changed it
while running. `next_decision_at` is `null` while stopped. The waiting fields are set
for the appliance or charger that is next and waiting (for a charger: its next
fictive appliance): `waiting_since` when it started, `waiting_until` when the
waiting time ends, and `waiting_ends_at` the decision that turns it on, the
first at or after `waiting_until` (`runtime.waiting_ends_at`, from
`first_decision_from()` in `runtime.py`). `variant` is the label of the current variant or `null`.
Charger details are from the last decision; `allowed` is false and `excluded`
is `null` before the first decision after a start. `charging` is true while
the charger is activated and was actively charging at the last decision, and
`window_overridden` while it was allowed to charge only because its charging
window is overridden (outside the window, not excluded). `car_connected` is
«car connected» at the last decision, `null` when it is not set or before the
first decision. All three are for the panel's state chip. Appliances are sorted by the
entry of their current variant, chargers by the current charging priority.
`ev_charging_position` is the number of appliances whose current variant is
placed before «EV charging», `null` while EV charging is disabled.
