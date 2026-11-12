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
- the checks of default and domain actions against their entities, the same
  as in `actions.py` and `domain_actions.py`,
- the name of a charger that is not saved yet, the same rule as the backend,
- the types of the configuration and the status snapshot,
- reading the power sensor in W or kW, the same units as the backend.

## Behaviour

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
  starts or stops, when what is missing changes, and when the config version
  in the status changes, since entities can change the stored configuration
  at any time. A draft with unsaved changes is kept while stopped.
- While the regulation runs, the configuration pages are locked and show a
  banner with a button to stop the regulation, on one line. Forms and lists
  are dimmed, add buttons are disabled and dialogs only show the item.
- The configuration pages extend `ConfigPage`, which holds what they share:
  the locked look, the list card with its add button, and the entities other
  items use. The status page and the lock banner share the start and stop
  button.
- The warning against controlling regulated appliances outside Kraftvakt is
  shown only while a list is empty (appliances on the Appliances page,
  chargers on the EV charging page).
- Default is offered only for domains with a default action. It is chosen
  when an entity with a default action is picked and the action is not set,
  and a default action becomes an empty custom action when the new entity has
  none. A custom action starts as the default action.
- The entity picker of an appliance or charger leaves out the entities that
  other appliances and chargers use.
- The charger dialog starts with the device, required, and every entity
  picker in it offers only the device's entities, none before a device is
  chosen. The panel checks, as the backend does, that the device exists and
  each entity belongs to it.
- Choosing another device clears every entity field that is not on the new
  device, then fills each empty field from the device in `charger-device.ts`,
  and adapts the actions to the new entity as a new entity does. A field is
  filled with the candidate of its type with the highest score from words in
  its name and entity ID (English and Norwegian, without the device name,
  which every entity has) and a likely device class or unit; a tie fills
  nothing, and a word on a field's exclusion list rules a candidate out. For
  the charger's own entity, the set-current entity and the charging power
  sensor, the only candidate of the type is enough. An entity filled for one
  field is not used for another. Actively charging prefers a boolean
  charging entity and falls back to a power sensor.
- The appliance dialog lists the variants by label, with drag and edit, and
  Add variant. What else is wrong or missing in a variant is
  shown under its label. A variant's edit button, and its row in the priority
  list, open the variant dialog: the expression and one switch per action to
  override it, both off by default. Switched on, the action starts from what
  it had while the dialog is open, or else a copy of the appliance's. The
  variant dialog edits a copy of the whole appliance; its Delete removes the
  variant and its actions with `item-changed`, since it changes the appliance.
- Edit in the appliance dialog is disabled, with a hint, while the dialog has
  changes or the appliance is new, because the variant dialog edits the
  appliance as it is in the draft. Edit closes the appliance dialog and opens
  the variant dialog when it has closed.
- A new entity adapts the actions of the appliance and every action a
  variant overrides the same way.
- The domain actions of the entity's domain are offered after Default, in
  the order of the table. Choosing one fills each value with the one already
  chosen for the parameter, or its default for the entity, so switching
  between them keeps a chosen HVAC mode. The values are a second `ha-form`
  under the choice: an option is a dropdown of the entity's options with
  HA's names for the states, and a temperature is a number box in HA's
  temperature unit with the entity's range as helper. A cleared value is
  `null`. A domain action becomes an empty custom action when the entity
  changes to one where it is not available.
- Finish ongoing charging after the charging window is shown under the
  times of the charging window, only while the charger has one. Its value is
  kept when the window is removed, since it has no effect without one.
- Set charging current also offers Entity: an entity picker limited to the
  domains with a default set-current action, with a helper telling which
  service runs. Required until an entity is chosen.
- The boolean entity picker offers binary sensors, input booleans, switches
  and schedules. Templates are previewed with HA's `render_template`
  subscription, with `entity` as the frontend's state object. A result that is
  not a boolean gets a warning that it counts as false.
- Missing items are not marked in a dialog until a new item has been added. A
  new variant starts as an empty template, which is missing, not an error, so
  the appliance can be confirmed before the variant gets its expression. Actively charging has no «not set», offers
  a boolean entity first and shows it until one is chosen; its preview reads the
  value as the backend does, so missing evidence shows as charging. Car
  connected is shown as required when only one charger in the group may
  charge at a time.
- The power sensor picker offers sensors with device class power, without
  Kraftvakt's own sensors.
- The EV charging page has one card per charger group, with its name, its
  settings and its chargers, and Add group under the cards. A new group gets
  the first free name of «EV chargers», «EV chargers 2» and so on, so it has
  no error at once. A group can be deleted
  only when it has no chargers.
- A charger moves to another group by dragging it to that group's list, with
  `ha-sortable`'s `group`, which puts the dragged row back so the lists follow
  the draft. An empty list stays in view as a place to drop on.
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
  waiting time, rounded up to whole decision intervals since the step is
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
- Third card, command repeat: a short text on why commands are repeated and
  that excluded appliances and chargers are left alone, and the interval in
  minutes.
- Tables are left out on a narrow screen.

### Status page

- The status page shows everything in the status snapshot: averages against
  the limit, next decision, safe state and penalty with what is left and
  whether recovery has started, appliances with variant and waiting, chargers
  with current and state.
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
- A waiting step shows an icon (a timer for an appliance, a plus for one more
  ampere) before a thin bar that empties smoothly from when the waiting
  started to the decision that turns the step on, animated like the ring. What
  it is and the time are a tooltip. The bar is smooth because a wait can span
  very many regulation windows.
- The tiles are, from the left, consumption now, regulation average, average
  consumption and the power limit. Consumption now is the power sensor's
  state read in the panel, so it updates live. Under each average is the time
  it covers.
- The meter is a bar for consumption now. Each other value is a triangle above
  the bar pointing down at it, in its own colour, and each tile has the same
  triangle as swatch. Nothing else is drawn on the meter. Under the bar is a
  kW scale with readable ticks, reaching a bit above the limit and every
  value.
- Appliances and chargers share one full-width priority list card. Each
  charger group has a row with its name and its own rank at its position,
  and its chargers are indented under it in the group's current charging
  priority. Every row is one line, with columns that line up without
  headings: rank, name with the variant after it, current, waiting and state
  chip. The rank is right aligned with digits of equal width. A name too long
  for its column is cut with an ellipsis and has the whole name as a tooltip;
  the variant is cut first, down to a few letters.
  - On a phone (a viewport at most 600 px wide, by a media query of its own,
    since a tablet that HA calls narrow still has room for every column) a
    row is only the icon, the name and the state chip: the rank, the variant,
    the charger count, the current, the ampere bars, the waiting and the
    text that there are no chargers are left out.
  - Icons instead of short texts, each with its sentence as a tooltip, and no
    legend. A group's row shows how many of its chargers are charging of all.
  - The current column has the current before one bar per ampere from min to
    max, filled up to the current. The filled bars of a bypassed charger are
    hatched.
  - The state chip has an icon and a word, with the whole sentence as a
    tooltip. An appliance shows excluded, on or off, and the title of an
    excluded appliance is dimmed. A charger shows the first that
    holds of: first decision (before the first decision after a start),
    excluded, its charging window when it is not allowed to charge, no car
    connected (bypassed and car connected is false), not charging (bypassed
    otherwise), queued (waiting), override (allowed only by the override
    while activated), finishing (allowed only to finish ongoing charging
    after the window), charging, activated, deactivated. Excluded comes before
    bypassed, so a stale bypassed is not shown. No car connected is a state
    of its own, because the user needs to know that the car is missing.
  - A resting charger is shown as bypassed, without when it is tried again.
  - A dashed cut-off line goes under the last entry that is on: an appliance,
    or a group's row while one of its chargers is activated and not
    bypassed. It is hidden when nothing is on, or when only excluded
    appliances are below the last entry that is on, so something that can be
    turned on is always below it. It shows the free power and its share of the
    power limit while that is above 0, and explains itself in a tooltip. By the
    fixed order nothing below the line is on.
- Colours come from Home Assistant's theme variables, set once on `:host`:
  the Energy dashboard's grid colour for the tariff average, a teal
  colour for everything EV charging, and HA's active and inactive state
  colours for appliance icons. Each appliance shows its entity's icon, and
  what is off is dimmed. An appliance whose entity is missing, or whose icon
  HA cannot show in the panel (an icon set that is not loaded renders
  nothing), shows a default icon instead: the icon step is one icon wide,
  and the entity's icon pushes the default icon out of it. The safe state and
  penalty chips are in the alarm colour and show only while active.

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
- `ha-dialog` is built on `wa-dialog`: `open`, `header-title`, step `footer`,
  event `closed`. When it closes itself, set `open` false on `closed`.
- When the HA version in `requirements_dev.txt` is raised, test the panel by
  hand against this list.

## Translations

Panel texts are in `frontend/src/translations/en.json` and `nb.json` (English
is the default, Norwegian the first translation), chosen from `hass.language`.
The keys are type checked, and `nb.json` must have every key in `en.json`.
Use the same terms as the rest of each translation file, and the same as the
integration's own translations.
