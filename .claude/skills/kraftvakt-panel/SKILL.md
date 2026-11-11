---
name: kraftvakt-panel
description: The Kraftvakt panel in frontend/ - Lit and TypeScript structure, routes, which Home Assistant components work in a custom panel, the draft and save flow, translations, and building the committed bundle. Use before changing anything in frontend/ or custom_components/kraftvakt/frontend/.
---

# Kraftvakt panel

The panel is the only user interface: a sidebar panel for administrators with
a top menu holding the status page and the configuration pages (General,
Appliances, EV charging, Advanced). Messages to the backend are in the
`kraftvakt-backend` skill.

## Build

- Lit + TypeScript + Rollup in `frontend/`, Lit with `experimentalDecorators`
  and `useDefineForClassFields: false`. Versions are pinned in `package.json`
  (Lit and TypeScript as the HA frontend for the supported HA version).
- Node from `.nvmrc` (the same as the HA frontend uses), via nvm or nvm.fish.
  Node is not on `PATH` in a plain non-interactive shell; activate it with nvm
  first, for example `fish -c 'nvm use; npm run build'`.
- `npm ci`, `npm run typecheck`, `npm run build` (`npm run watch`).
- The minified bundle `custom_components/kraftvakt/frontend/kraftvakt-panel.js`
  is committed, because HACS installs from the repository. Rebuild after every
  change in `frontend/` and commit source and bundle together. CI fails when
  the committed bundle differs from a clean build.
- The bundle URL carries the manifest version. During development the browser
  may use an old bundle; reload without cache.

## Structure

`frontend/src/` has the panel element (routing on `hass.route`, the top menu,
the draft, the save bar and the lock of the configuration pages), one module
per page in `pages/`, shared components in `components/`, and modules for the
API, translations, navigation, the draft, validation, issue texts, entity
names and formatting. One page per route under `/kraftvakt/`; `/kraftvakt`
itself is the status page, and `?config_entry=` (from the integration's
configure button) goes to the Appliances page.

Code that mirrors the backend and must be kept in step with it:

- the waiting time curve, the same as in `regulation/waiting.py`,
- validation against the limits, what is missing and completing the priority
  list, the same rules as in `config_validation.py`,
- the name of a charger that is not saved yet, the same rule as the backend,
- the types of the configuration and the status snapshot,
- reading the power sensor in W or kW, the same units as the backend.

## Behaviour that was settled

### Configuration pages

- The configuration pages share one draft. Save stores everything, Discard
  goes back to the saved configuration. The panel checks the draft against
  the limits from `kraftvakt/capabilities` and works out what is missing
  itself, so errors show before saving, and Save is disabled while there are
  errors. Errors from the backend show at the fields until the next save.
- The panel asks before discarding unsaved changes when going to the status
  page; the browser asks when the page is closed. HA sidebar navigation cannot
  be stopped. The draft is discarded when the regulation starts.
- The configuration is fetched again at the first status, when the regulation
  starts or stops, when what is missing changes, and when the power limit in
  the status changes, since the power limit entity can change the stored
  limit at any time. A draft with unsaved changes is kept while stopped.
- While the regulation runs, the configuration pages are locked and show a
  banner with a button to stop the regulation, on one line. Forms and lists
  are dimmed, add buttons are disabled and dialogs only show the item.
- The configuration pages extend `ConfigPage`, which holds what they share:
  the locked look, the list card with its add button, and the entities other
  items use. The status page and the lock banner share the start and stop
  button.
- The warning against controlling regulated appliances outside Kraftvakt is
  shown only while a list is empty (appliances on the Appliances page,
  chargers on the EV charging page), since the user does not need to see it
  all the time.
- Default is offered only for domains with a default action. It is chosen
  when an entity with a default action is picked and the action is not set,
  and a default action becomes an empty custom action when the new entity has
  none. A custom action starts as the default action.
- The entity picker of an appliance or charger leaves out the entities that
  other appliances and chargers use.
- Set charging current also offers Entity: an entity picker limited to the
  domains with a default set-current action, with a helper telling which
  service runs. Required until an entity is chosen.
- The boolean entity picker offers binary sensors, input booleans, switches
  and schedules. Templates are previewed with HA's `render_template`
  subscription, with `entity` as the frontend's state object. A result that is
  not a boolean gets a warning that it counts as false.
- Missing items are not marked in a dialog until a new item has been added. A
  new variant starts as a template. Car connected is shown as required when
  only one charger may charge at a time.
- The power sensor picker offers sensors with device class power, without
  Kraftvakt's own sensors.
- While EV charging is disabled, the chargers can only be viewed, and one
  charger at a time is hidden.
- Configuration pages and dialogs show power in W.

### Advanced page

- The last page in the menu, with the settings most users never change. Its
  settings belong to `general` in the stored configuration, so issues for
  those fields send the user to it. The waiting time at the power limit is on
  the General page.
- Little text: the user reads the curve and the result, not how it is
  computed.
- First card, the waiting time curve: one line of text, sliders for steepness
  and pivot point (no tooltip, the value as plain text beside it, no input box,
  no helper text), a table and a graph that follow the draft while the sliders
  move. The pivot point is not marked on the graph.
- The card speaks of free power as a share of the power limit, not of
  utilization, since free power is the term the status page uses. The pivot
  slider shows free power, from 50 % at the left end to 1 % at the right; it
  moves over the stored pivot and shows 100 minus it; the stored value and the
  regulation use utilization.
- The table shows, for a range of free power from half the limit down to
  almost nothing, the free power in kW, the waiting time and the actual
  waiting time, rounded up to whole decision intervals since the slot is
  turned on at the first decision after the waiting time. The line of text
  says why it is rounded. Times are minutes and whole seconds. Values come
  from the draft, with a dash when a setting is not set.
- The graph has the waiting time in percent on the y-axis, so its shape does
  not change with the waiting time at the limit, and free power in kW on the
  x-axis, decreasing to 0 at the right so the waiting time grows to the right.
  It starts a bit above half the limit, so the curve always starts flat at 0.
- Second card, the waiting time on repeated turn-on: a short text saying it is
  about the regulation turning the same appliance or ampere on over and over
  again, then one part for appliances and one for EV chargers. Each has
  dropdowns for the step and the number of steps, and a table with one column
  per turn-on in a row up to the one that reaches the cap, marked as holding
  for every time after it, with the waiting time and the actual waiting time.
  The first two follow the curve and show the waiting time at the pivot point,
  which the text says. Dropdowns keep their values as numbers in the draft.
- Tables are left out on a narrow screen.

### Status page

- The status page shows everything in the status snapshot: averages against
  the limit, next decision, safe state and penalty with what is left and
  whether recovery has started,
  appliances with variant and waiting, chargers with current and state.
  Power is shown in kW and energy in kWh.
- While stopped, the regulation card lists what is missing, each with a link
  to the page where it is fixed.
- The regulation card's header holds the title, a chip for running or stopped,
  chips for safe state and penalty while active, and the next decision at the
  right end. Start and stop are in a footer under a divider, on every screen
  width; stop is a plain danger button, start a filled one.
- While the power sensor is valid again but the safe state lasts until the
  next decision, the safe state banner is an info that the regulation starts
  again at the next decision, not the error that the sensor gives no valid
  measurement.
- Countdowns are never ticking text. The next decision is a small ring that
  empties over one decision interval, animated by the browser (Web Animations
  API) so it needs no clock; the time is a tooltip. On a narrow screen only
  the ring is shown.
- A waiting slot shows an icon (a timer for an appliance, a plus for one more
  ampere) before a thin bar that empties smoothly from when the waiting
  started to the decision that turns the slot on, animated like the ring. What
  it is and the time are a tooltip. The bar is smooth because a wait can span
  very many regulation windows. The waiting column is left out on a narrow
  screen.
- The tiles are, from the left, consumption now, regulation average, average
  consumption and the power limit. Consumption now is the power sensor's
  state read in the panel, so it updates live. Under each average is the time
  it covers.
- The meter is a bar for consumption now. Each other value is a triangle above
  the bar pointing down at it, in its own colour, and each tile has the same
  triangle as swatch. Nothing else is drawn on the meter. Under the bar is a
  kW scale with readable ticks, reaching a bit above the limit and every
  value.
- Appliances and chargers share one full-width priority list card. The EV
  charging row has its own rank at the EV charging position, and the chargers
  are indented under it in the current charging priority. Every row is one
  line, with columns that line up without headings: rank, name with the
  variant after it, current, waiting and state chip.
  - Icons instead of short texts, each with its sentence as a tooltip, and no
    legend. The EV charging row shows how many chargers are charging of all.
  - The current column has the current before one bar per ampere from min to
    max, filled up to the current. The filled bars of a bypassed charger are
    hatched. On a narrow screen only the bars are shown.
  - The state chip has an icon and a word, with the whole sentence as a
    tooltip. An appliance shows excluded, on or off, and the title of an
    excluded appliance is dimmed. A charger shows the first that
    holds of: first decision (before the first decision after a start),
    excluded, its charging window when it is not allowed to charge, no car
    connected (bypassed and car connected is false), no power draw (bypassed
    otherwise), queued (waiting), override (allowed only by the override
    while activated), charging, activated, deactivated. Excluded comes before
    bypassed, so a stale bypassed is not shown. No car connected is a state
    of its own, because the user needs to know that the car is missing.
  - A resting charger is shown as bypassed, without when it is tried again.
  - A dashed cut-off line goes under the last entry that is on: an appliance,
    or the EV charging row while one of its chargers is activated and not
    bypassed. It is hidden when nothing is on, or when only excluded
    appliances are below the last entry that is on, so something that can be
    turned on is always below it. It shows the free power and its share of the power
    limit while that is above 0, and explains itself in a tooltip. By the
    fixed order nothing below the line is on.
- Colours come from Home Assistant's theme variables, set once on `:host`:
  the Energy dashboard's grid colour for the average consumption, a teal
  colour for everything EV charging, and HA's active and inactive state
  colours for appliance icons. Each appliance shows its entity's icon, and
  what is off is dimmed. The safe state and penalty chips are in the alarm
  colour and show only while active.

## Home Assistant components

Defined when the panel renders, and the only ones to use (checked against the
HA version in `requirements_dev.txt`): `ha-form` with selectors (`text`,
`number`, `select`, `entity`, `template`, `action`, `time`, `boolean`),
`ha-selector`, `ha-sortable` (listen to `item-moved` and re-render; it does
not move elements), `ha-dialog`, `ha-card`, `ha-alert`, `ha-button`,
`ha-icon-button`, `ha-svg-icon`, `ha-state-icon` (`.hass`, `.stateObj`),
`ha-switch`, `ha-formfield`, `ha-settings-row`, `ha-expansion-panel`,
`ha-md-list-item`, `ha-code-editor`, `ha-yaml-editor`, `ha-menu-button`,
`ha-tab-group` with `ha-tab-group-tab` (event `wa-tab-show`), `ha-slider`
(`.min`, `.max`, `.step`, `.value`, `.withTooltip`, event `input`; defined by
the number selector that the same page loads).

Not available, do not use: `ha-textfield`, `ha-radio`, `ha-md-list`,
`ha-list-item`, `ha-wa-dialog`, `ha-md-dialog`, `ha-segmented-button`,
`window.loadCardHelpers`, and no `partial-panel-resolver` hacks.

- Wait for `customElements.whenDefined("ha-form")` before the first render.
- The action editor needs `hass.loadFragmentTranslation("config")`, otherwise
  its labels are empty.
- `ha-dialog` is built on `wa-dialog`: `open`, `header-title`, slot `footer`,
  event `closed`. When it closes itself, set `open` false on `closed`.
- When the HA version in `requirements_dev.txt` is raised, test the panel by
  hand against this list.

## Translations

Panel texts are in `frontend/src/translations/en.json` and `nb.json` (English
is the default, Norwegian the first translation), chosen from `hass.language`.
The keys are type checked, and `nb.json` must have every key in `en.json`.
Use the same terms as the rest of each translation file, and the same as the
integration's own translations.
