---
name: kraftvakt-panel
description: The Kraftvakt panel in frontend/ - Lit and TypeScript structure, routes, which Home Assistant components work in a custom panel, the draft and save flow, translations, and building the committed bundle. Use before changing anything in frontend/ or custom_components/kraftvakt/frontend/.
---

# Kraftvakt panel

The panel is the only user interface: a sidebar panel for administrators with a
top menu (Status, General, Appliances, EV charging). Messages to the backend
are in the `kraftvakt-backend` skill.

## Build

- Lit + TypeScript + Rollup in `frontend/`, Lit with `experimentalDecorators`
  and `useDefineForClassFields: false`. Versions are pinned in `package.json`
  (Lit and TypeScript as the HA frontend for the supported HA version).
- Node from `.nvmrc` (the same as the HA frontend uses), via nvm or nvm.fish.
  Here: `~/.local/share/nvm/v24.21.0/bin` first in `PATH`.
- `npm ci`, `npm run typecheck`, `npm run build` (`npm run watch`).
- The minified bundle `custom_components/kraftvakt/frontend/kraftvakt-panel.js`
  is committed, because HACS installs from the repository. Rebuild after every
  change in `frontend/` and commit source and bundle together. CI fails when
  the committed bundle differs from a clean build.
- The bundle URL has `?v=<manifest version>`. During development the browser
  may use an old bundle; reload without cache.

## Structure

```
frontend/src/
  kraftvakt-panel.ts   routing on hass.route, top menu, ?config_entry= forwarding,
                       the draft, the save bar and the lock of the config pages
  api.ts               types and WebSocket calls
  localize.ts          lookups in translations/{en,nb}.json (keys are type checked)
  navigation.ts        pages, navigateToPage()
  issues.ts            texts and page for missing items and validation errors
  draft.ts             ids, moving, completed priority list
  validation.ts        checks the draft against the limits, and what is missing
  entities.ts          entity names, and Kraftvakt's own entities
  types.ts, format.ts
  pages/               status, general, appliances, charging, config-page (shared)
  components/          countdown-ring, locked-banner, manual-control-warning, sortable-list,
                       item-dialog (shared), appliance-dialog, charger-dialog,
                       action-field, condition-field, save-bar, confirm-dialog
```

Routes: `/kraftvakt` and `/kraftvakt/status`, `/kraftvakt/general`,
`/kraftvakt/appliances`, `/kraftvakt/charging`.

## Behaviour that was settled

- The configuration pages share one draft in `kraftvakt-panel.ts`. «Save»
  saves everything, «Discard» goes back to the saved configuration. The panel
  checks the draft against the limits from `kraftvakt/capabilities` and works
  out what is missing itself (mirroring `missing_items()`), so errors show
  before saving, and «Save» is disabled while there are errors. Errors from the
  backend show at the fields until the next save.
- The panel asks before discarding unsaved changes when going to the status
  page; the browser asks when the page is closed. HA sidebar navigation cannot
  be stopped. The draft is discarded when the regulation starts (only possible
  from the status page in the panel, or from the switch).
- While the regulation runs, config pages are locked and show «Stop regulation»
  in the banner. Both config pages with appliances or chargers show the warning
  against manual control.
- «Default» is offered only for domains in `default_actions`, and is chosen
  when an entity with a default action is picked. A custom action starts as the
  default action.
- The boolean entity picker shows `binary_sensor`, `input_boolean`, `switch`
  and `schedule`. Templates are previewed with HA's `render_template`
  subscription, with `entity` as the frontend's state object.
- Missing items are not marked in a dialog until a new item has been added. A
  new variant starts as a template. «Car connected» is shown as required when
  only one charger may charge at a time.
- Kraftvakt's own sensors are left out of the power sensor pickers.
- The status page shows everything in the status snapshot: averages against
  the limit, next decision, safe state and penalty with what is left, appliances
  with variant and waiting, chargers with current, bypassed, waiting, excluded
  or outside the charging window.
- Countdowns are never ticking text. «Next decision» is
  `kraftvakt-countdown-ring` alone at the right end of the chips row, without
  a label: a 20 px ring that empties counterclockwise towards the top over one
  decision interval (`regulation_window_s` × `regulation_interval`), animated
  with the Web Animations API, so it needs no clock. The time is a tooltip.
- The waiting column shows one block per regulation window left until
  `waiting_ends_at`, the decision that turns the slot on. All blocks have the
  same whole-pixel size (`blockSize()`): 8 px squares in the text colour with
  a 2 px gap, aligned right; with many windows they get thinner and taller, at
  most 3 × 12 px bars like the ampere bars. When more windows are left than
  fit (18 bars in 88 px, 10 in 48 px on a narrow screen), each block
  stands for several windows, so the whole wait fits (owner's choice over
  clipping or a count). The status comes at every window, so the blocks are
  recalculated each time. The time is a tooltip. A bar and a ring were tried here and turned down by the owner.
- The tiles are average consumption, regulation average, «Consumption now» and
  the power limit. «Consumption now» is the power sensor's state read in the
  panel (`measuredPowerKw()`, same units as the backend), so it updates live;
  the meter does not show it.
- The average consumption comes first: its tile is to the left and it is the
  thick bar in the primary (blue) colour. The regulation average is the second
  tile and a thin line in the text colour on top, so it shows against the blue
  bar and the empty track. Under each average value is the time it covers
  («over 1 hour», «over 60 s» from `regulation_window_s`).
- Appliances and chargers share one full-width card, «Priority list». An
  «EV charging» row with its own rank sits at `ev_charging_position`, and the
  chargers are indented under it in the current charging priority, with their
  reasons under the name. Columns, without headings: rank, name, variant,
  current, waiting and state. The current column reads «6 A ▮▮▮▮▯▯▯ 9 A»: the minimum current, one
  vertical bar per ampere from min to max filled up to the current (narrower
  above 16 steps), and the current. On a narrow
  screen the variant goes after the name and the ampere bars under it.

## Home Assistant components

Defined when the panel renders (checked with HA 2026.10.4), and the only ones
to use: `ha-form` with selectors (`text`, `number`, `select`, `entity`,
`template`, `action`, `time`, `boolean`), `ha-selector`, `ha-sortable` (listen
to `item-moved` and re-render; it does not move elements), `ha-dialog`,
`ha-card`, `ha-alert`, `ha-button`, `ha-icon-button`, `ha-svg-icon`,
`ha-switch`, `ha-formfield`, `ha-settings-row`, `ha-expansion-panel`,
`ha-md-list-item`, `ha-code-editor`, `ha-yaml-editor`, `ha-menu-button`,
`ha-tab-group` with `ha-tab-group-tab` (event `wa-tab-show`).

Not available, do not use: `ha-textfield`, `ha-radio`, `ha-md-list`,
`ha-list-item`, `ha-wa-dialog`, `ha-md-dialog`, `ha-segmented-button`,
`window.loadCardHelpers`, and no `partial-panel-resolver` hacks.

- Wait for `customElements.whenDefined("ha-form")` before the first render.
- The action editor needs `hass.loadFragmentTranslation("config")`, otherwise
  its labels are empty.
- `ha-dialog` in 2026.10 is built on `wa-dialog`: `open`, `header-title`, slot
  `footer`, event `closed`. When it closes itself, set `open` false on
  `closed`.
- When the HA version in `requirements_dev.txt` is raised, test the panel by
  hand against this list and update `.nvmrc` to the HA frontend's Node version.

## Translations

Panel texts are in `frontend/src/translations/en.json` and `nb.json` (English
is the default, Norwegian the first translation), chosen from `hass.language`.
`nb.json` must have every key in `en.json`. Use the Norwegian terms the users
know: «effektgrense», «reguleringssnitt», «snittforbruk», «elbillader»,
«ladetidsrom», «straffeperiode», «sikker tilstand».
