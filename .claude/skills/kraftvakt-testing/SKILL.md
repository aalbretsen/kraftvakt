---
name: kraftvakt-testing
description: How Kraftvakt is tested - the test layout, the scenario language for the regulation engine, conventions for black box tests with the Home Assistant test harness, the checks every commit must pass, and how to test by hand against a local Home Assistant with a simulated power sensor. Use when writing or changing tests, before committing, or when testing the panel or the regulation by hand.
---

# Testing Kraftvakt

## Strategy

- Black box tests with the HA test harness are the main tool. They find more
  faults than unit tests.
- Complex logic (`regulation/`, `measurement.py`, `config_model.py`) is also
  proven by itself with unit tests. Error handling that is hard to reach from
  the outside is unit tested.
- Aim for coverage, not every permutation. Today: 455 tests, 99 % line
  coverage. The only uncovered line is the `TypeError` for an unknown slot in
  `engine.py`.
- The panel has no automatic tests. The type check and the build run in CI, and
  the panel is tested by hand in a browser.

## Checks before every commit

```bash
.venv/bin/python -m pytest -q --cov=custom_components/kraftvakt --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/ruff format --check .
cd frontend && npm run typecheck && npm run build && git status --short ../custom_components/kraftvakt/frontend/
```

The bundle must be unchanged after the build, or be committed with the source.
Setup: `uv venv --python 3.14 && uv pip install -r requirements_dev.txt`
(Python ≥ 3.14.2), and `npm ci` in `frontend/` with Node from `.nvmrc`.

## Layout

- `tests/unit/`: unit tests. `tests/unit/regulation/` has the scenario tests
  for the engine, one file per area (switching, waiting, cycling, variants,
  penalty, safe state, charging, priority).
- `tests/`: black box tests per area: `test_regulation.py` (end to end),
  `test_charging.py`, `test_sensor.py`, `test_runtime.py`,
  `test_websocket_api.py`, `test_storage.py`, `test_init.py`,
  `test_config_flow.py`. `tests/config_examples.py` has a full configuration.

## Scenario language

`tests/unit/regulation/scenario.py` and `configs.py`:

```python
scenario = Scenario(make_config("a", "b"))
assert scenario.decide(5.0) == on("a")
```

`Scenario.decide(average, capacity=..., averages=..., after=..., true=...,
sensor_valid=..., sensor_lost=...)` makes one decision one interval (or
`after`) after the previous; `true` names the variants whose expression is
true.
`decide_many`, `turn_on`, `charge` and `set_charger` set up states. Commands are
compared with `on`, `off`, `activate`, `deactivate`, `current` and
`reset_override`. `make_config()` builds configurations with `appliance()`,
`charger()` and priority entries written as text.

## Black box conventions

- Store the configuration in `hass_storage[STORAGE_KEY]` before setup.
- Use `light.*` entities for appliances: mocking `switch.turn_on` would replace
  Kraftvakt's own switch service.
- Move time with `freezer.tick()` and `async_fire_time_changed`. Commands run in
  a background task: use `hass.async_block_till_done(wait_background_tasks=True)`.
  A test with a service that blocks on purpose must not wait for it.
- The test `hass` is running, so the regulation starts at setup. To test the
  start when HA has started, `hass.set_state(CoreState.starting)` before setup
  and fire `EVENT_HOMEASSISTANT_STARTED` afterwards.
- With a status subscription, use one WebSocket client for the subscription and
  another for commands; events can come before a command's result.

## Manual test against a local Home Assistant

1. Make a config folder outside the repository (the scratchpad) and link
   `custom_components` into it. Never print or store a password in the
   repository.
2. `configuration.yaml`: `trusted_networks` for `127.0.0.1/32` and `::1/128`
   with `allow_bypass_login` (block style, flow style broke the provider), plus
   `type: homeassistant`; `frontend:`, `config:`, `history:`; a logger with
   `custom_components.kraftvakt: debug`; `input_number` for the house power,
   charging power and current; `input_boolean` for appliances, chargers and
   «car connected»; template sensors in W with `device_class: power` as power
   sensor and charging power sensor.
3. Start with `.venv/bin/hass -c <folder>` in the background (port 8123; check
   first that it is free). Onboard over REST (`/api/onboarding/users` with a
   random password, `/auth/token`, then the remaining steps) and add Kraftvakt
   with `/api/config/config_entries/flow`. After onboarding `/api/onboarding`
   gives 404; wait for the log line «Home Assistant initialized» instead.
4. Open `http://127.0.0.1:8123/kraftvakt` in the browser; trusted networks
   logs in. The panel's own WebSocket commands can set up a configuration
   quickly with `hass.callWS` from the page.
5. Drive the scenario by changing the `input_number` power and watch the status
   page and the entity history (`/api/history/period/...`). A short regulation
   window (10 s) and waiting time (0–1 min) make it fast. Setting a state to
   `unavailable` with `POST /api/states/<entity>` simulates a lost sensor.
6. Stop Home Assistant and delete the folder afterwards.
