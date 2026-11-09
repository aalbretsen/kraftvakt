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
  components/          countdown (ring and bar), locked-banner, manual-control-warning, sortable-list,
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
  subscription, with `entity` as the frontend's state object. A result that is not
  a boolean gets a warning that it counts as false (settled after the
  exploratory test).
- Missing items are not marked in a dialog until a new item has been added. A
  new variant starts as a template. «Car connected» is shown as required when
  only one charger may charge at a time.
- Kraftvakt's own sensors are left out of the power sensor pickers.
- The status page shows everything in the status snapshot: averages against
  the limit, next decision, safe state and penalty with what is left, appliances
  with variant and waiting, chargers with current, bypassed, waiting, excluded,
  outside the charging window, overridden or charging. Before the first
  decision after a start (`excluded` is null) a charger shows «First
  decision» instead (settled after the exploratory test). A charger that rests after
  not charging is shown as bypassed, without when it is tried again; the
  owner chose not to add it to the status (after the retest of the exploratory test).
- The safe state lasts until the next decision. While the power sensor is
  already valid again, the safe state banner is an info that the regulation
  starts again at the next decision, not the error that the sensor gives no
  valid measurement (settled after the exploratory test).
- The header of the «Regulation» card holds the title, the «Running» or
  «Stopped» chip, the «Safe state» and «Penalty period» chips while active,
  and «Next decision» at the right end. «Start regulation» and «Stop
  regulation» are in a footer under a divider, on every screen width; stop is
  a plain danger button, start a filled one. The owner chose this over a
  switch or a small button in the header, because a large outlined button in
  the header looked misplaced and the ring stood alone on its own row.
- Countdowns are never ticking text. «Next decision» is a label (only the
  ring on a narrow screen) and `kraftvakt-countdown-ring`: a 20 px ring
  that empties counterclockwise towards the top over one decision interval
  (`regulation_window_s` × `regulation_interval`), animated with the Web
  Animations API, so it needs no clock. The time is a tooltip.
- The waiting column shows an icon before a `kraftvakt-countdown-bar` (6 px,
  the text colour on a grey track) that empties towards the right from
  `waiting_since` to `waiting_ends_at`, the decision that turns the slot on,
  animated by the browser like the ring. The icon is a timer for an appliance
  (delayed turn-on) and a plus for an EV charger waiting for one more ampere.
  What it is and the time are a tooltip. The owner settled on the smooth bar,
  because a wait can span very many regulation windows; one block per window
  and a ring were tried and turned down. The waiting column is left out on a
  narrow screen (settled in the priority list redesign).
- The tiles are, from the left, «Consumption now», regulation average,
  average consumption and the power limit. «Consumption now» is the power
  sensor's state read in the panel (`measuredPowerKw()`, same units as the
  backend), so it updates live. Under each average value is the time it covers
  («over 1 hour», «over 60 s» from `regulation_window_s`).
- The meter is a 12 px bar for «Consumption now» in grey
  (`--kraftvakt-now-color`, the secondary text colour). Each other value is a
  triangle above the bar pointing down at it: blue (grid colour) for the
  average consumption, white (text colour) for the regulation average and red
  for the power limit. Each tile has the same triangle as swatch, and
  «Consumption now» a small grey bar. There is no limit line, limit text or
  penalty zone (the owner removed them). Under the bar are ticks every 1, 2,
  5, 10, 20 or 50 kW (the smallest step that gives at most 15), with the value
  at every second tick (every third on a narrow screen) and «kW» after the
  last value. The scale is rounded up to a whole step and reaches at least 1.2
  × the limit and every value. Standing rectangles were tried for the markers
  and turned down.
- Appliances and chargers share one full-width card, «Priority list». An «EV
  charging» row with its own rank sits at `ev_charging_position`, and the
  chargers are indented under it in the current charging priority. Every row
  is one line. Columns, without headings: rank, name with the variant tag after
  it, current, waiting and state chip. The rows are a CSS subgrid of the list,
  so the columns line up although the chips differ in width. Settled with the
  owner in the priority list redesign, after mockups of lanes across the row,
  charger tiles and badges on the icons were turned down:
  - Icons instead of text wherever a short text was, each with its sentence as
    a tooltip, and no legend. «EV charging» shows a bolt and «2 / 5»: chargers
    charging of all chargers.
  - The current column has the current right-aligned («11 A», «–» while
    deactivated) before one vertical bar per ampere from min to max, filled up
    to the current (narrower above 16 steps). The filled bar of a bypassed
    charger is hatched. On a narrow screen only the bars are shown.
  - The state chip has an icon and a word, with the whole sentence as a
    tooltip; On and Off have a dot. An appliance shows «On» or «Off». An EV
    charger shows the first that holds of: «First decision» (`excluded` is
    null), «Excluded», the charging window («22–06», whole hours without
    «:00») when it is not allowed to charge, «No power draw» (bypassed),
    «Queued» (waiting), «Override» (`window_overridden` while activated),
    «Charging» (`charging`), «Activated» (activated, not charging yet) and
    «Deactivated». Excluded comes first, so a stale bypassed is not shown.
  - A dashed cut-off line, in the primary colour, goes under the last entry
    that is on: an appliance, or «EV charging» while one of its chargers is
    activated and not bypassed. It is hidden when nothing or everything is on,
    so it always sits between two entries. It shows the free power, the power
    limit minus the regulation average, while that is above 0, and explains
    itself in a tooltip. By the fixed order nothing below the line is on.
- Colours come from Home Assistant's theme variables, set once on `:host`:
  `--kraftvakt-grid-color` (the Energy dashboard's `--energy-grid-consumption-
  color`) for the average consumption, `--kraftvakt-ev-color` (`--teal-color`)
  for the ampere bars, the «EV charging» icon and a faint tint (`color-mix`, 7
  %) behind the «EV charging» row and its chargers, and `--kraftvakt-on-color`
  (`--state-active-color`) for the icon of an appliance that is on. Each
  appliance shows its entity's icon with `ha-state-icon` (a flash icon when
  the entity is missing), and each charger the EV station icon in the EV
  colour while activated; icons of what is off are in `--state-inactive-color`
  and the name is dimmed. «Safe state» and «Penalty period» chips show only
  while active, in the alarm colour. The owner chose these over warning
  colours near the limit.

## Home Assistant components

Defined when the panel renders (checked with HA 2026.10.4), and the only ones
to use: `ha-form` with selectors (`text`, `number`, `select`, `entity`,
`template`, `action`, `time`, `boolean`), `ha-selector`, `ha-sortable` (listen
to `item-moved` and re-render; it does not move elements), `ha-dialog`,
`ha-card`, `ha-alert`, `ha-button`, `ha-icon-button`, `ha-svg-icon`,
`ha-state-icon` (`.hass`, `.stateObj`), `ha-switch`, `ha-formfield`, `ha-settings-row`, `ha-expansion-panel`,
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
