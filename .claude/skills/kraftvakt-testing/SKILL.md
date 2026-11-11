---
name: kraftvakt-testing
description: How Kraftvakt is tested - the test layout, the scenario language for the regulation engine, conventions for black box tests with the Home Assistant test harness, the checks every commit must pass, and how to test by hand against a local Home Assistant with the Kraftvakt simulator. Use when writing or changing tests, before committing, or when testing the panel or the regulation by hand.
---

# Testing Kraftvakt

## Strategy

- Black box tests with the HA test harness are the main tool. They find more
  faults than unit tests.
- Complex logic (`regulation/`, `measurement.py`, `config_model.py`) is also
  proven by itself with unit tests. Error handling that is hard to reach from
  the outside is unit tested.
- Aim for coverage, not every permutation. Every line of Kraftvakt and the
  simulator should be covered, except defensive code that cannot be reached.
  Check the coverage report for new uncovered lines before committing.
- The panel has no automatic tests. The type check and the build run in CI,
  and the panel is tested by hand in a browser.

## Checks before every commit

```bash
.venv/bin/python -m pytest -q --cov=custom_components/kraftvakt --cov=simulator/custom_components/kraftvakt_simulator --cov-report=term-missing
.venv/bin/ruff check .
.venv/bin/ruff format --check .
cd frontend && npm run typecheck && npm run build && git status --short ../custom_components/kraftvakt/frontend/
```

The bundle must be unchanged after the build, or be committed with the source.
Node must be activated with nvm first, see the `kraftvakt-panel` skill.
Setup: `uv venv --python 3.14 && uv pip install -r requirements_dev.txt`, and
`npm ci` in `frontend/`.

## Updating dependencies

`uv run scripts/update_dependencies.py`, with Node active, updates every pin:
the Python development dependencies, `pyproject.toml`'s Python, `.nvmrc`, the
panel's packages and lock file, and the GitHub actions. Most versions follow
one chain from the newest `pytest-homeassistant-custom-component`, so the
test harness, Home Assistant, its frontend, ruff, Node, Lit and TypeScript
always fit together; the rest get their newest release. Afterwards install
again, `nvm install`, run every check and rebuild the panel. Commit the
dependency changes on their own. A new Home Assistant version also needs the
panel tested by hand, see the `kraftvakt-panel` skill.

## Layout

- `tests/unit/`: unit tests. `tests/unit/regulation/` has the scenario tests
  for the engine, one file per area of the regulation.
- `tests/`: black box tests, one file per area. `tests/config_examples.py` has
  a full configuration that uses every feature.
- `tests/simulator/` and `tests/unit/simulator/`: the simulator, see the
  `kraftvakt-simulator` skill. `pyproject.toml` puts `simulator` on pytest's
  `pythonpath`, so both integrations load in every test.

## Scenario language

The engine's unit tests use a small scenario language in
`tests/unit/regulation/` (`scenario.py` and `configs.py`): a `Scenario` runs
decisions one interval apart with a given regulation average and other
inputs, and the returned commands are compared with helpers named after the
commands. Configurations are built with helpers for appliances, chargers and
priority entries. Read those two files before writing an engine test, and
extend them rather than building engine inputs by hand.

## Black box conventions

- Tests with the recorder go in their own file, which overrides the autouse
  `auto_enable_custom_integrations` to request `recorder_mock` first: the
  recorder must start before `hass`. Record states at past times with
  `freezer.move_to()` and `async_wait_recording_done()`.
- Store the configuration in `hass_storage` before setup.
- Use `light.*` entities for appliances: mocking `switch.turn_on` would replace
  Kraftvakt's own switch service. For the same reason, mock
  `input_number.set_value`, not `number.set_value`: Kraftvakt has a number
  entity.
- Move time with `freezer.tick()` and `async_fire_time_changed`. Commands run
  in a background task: use
  `hass.async_block_till_done(wait_background_tasks=True)`. A test with a
  service that blocks on purpose must not wait for it.
- The test `hass` is running, so the regulation starts at setup. To test the
  start when HA has started, set `hass.set_state(CoreState.starting)` before
  setup and fire `EVENT_HOMEASSISTANT_STARTED` afterwards.
- With a status subscription, use one WebSocket client for the subscription and
  another for commands; events can come before a command's result.

## Manual test against a local Home Assistant

1. Make a config folder outside the repository (the scratchpad) with a real
   `custom_components/` folder holding two symlinks, one to Kraftvakt and one
   to the simulator. Never print or store a password in the repository.
2. `configuration.yaml`: `trusted_networks` for `127.0.0.1/32` and `::1/128`
   with `allow_bypass_login` (block style; flow style broke the provider),
   plus `type: homeassistant`; `frontend:`, `config:`, `history:`; a logger
   with debug for Kraftvakt. No helpers or template sensors are needed: the
   simulator gives the power sensor, appliances and chargers.
3. Start with `.venv/bin/hass -c <folder>` in the background (port 8123; check
   first that it is free). Let it install its missing modules (do not use
   `--skip-pip`). Onboard over REST (`/api/onboarding/users` with a random
   password, `/auth/token`, then the remaining steps). Keep the token in a
   file with mode 600 in the scratchpad, never in the output. After
   onboarding, `/api/onboarding` gives 404; wait for the log line that Home
   Assistant is initialized instead.
4. Add the simulator devices with `/api/config/config_entries/flow` (handler
   `kraftvakt_simulator`, then the menu step of the device kind and its form),
   typically a HAN, two heating devices with short periods and a charger, and
   add Kraftvakt the same way. The entity ids follow the device names and the
   language chosen at onboarding.
5. Save a Kraftvakt configuration against those entities with
   `kraftvakt/config/save` over the WebSocket (or `hass.callWS` from the
   panel) and start it with `kraftvakt/regulation/set_running`. A short
   regulation window and waiting time make it fast.
6. Drive the scenario with the simulator: change the background power,
   connect the car and let it be fully charged, and record the states
   regularly (or read the history API). Open the panel to watch the status
   page; trusted networks logs in. Setting the HAN sensor to `unavailable`
   with `POST /api/states/<entity>` simulates a lost sensor until the
   simulator writes it again.
7. Stop Home Assistant and delete the folder afterwards.
