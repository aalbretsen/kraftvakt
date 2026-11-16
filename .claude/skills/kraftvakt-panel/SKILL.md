---
name: kraftvakt-panel
description: The Kraftvakt panel in frontend/ - Lit and TypeScript structure, routes, which Home Assistant components work in a custom panel, the draft and save flow, translations,
  and building the committed bundle. Use before changing anything in frontend/ or custom_components/kraftvakt/frontend/.
---

# Kraftvakt panel

The panel is the only user interface: a sidebar panel for administrators with a top menu holding the status page and the configuration pages (General, Appliances, EV charging,
Advanced). Messages to the backend are in the `kraftvakt-backend` skill.

## Build

- Lit + TypeScript + Rollup in `frontend/`, Lit with `experimentalDecorators` and `useDefineForClassFields: false`.
  Versions are pinned in `package.json` (Lit and TypeScript as the HA frontend for the supported HA version).
- Node from `.nvmrc` (the same as the HA frontend uses), via nvm or nvm.fish.
  Node is not on `PATH` in a plain non-interactive shell; activate it with nvm first, for example `fish -c 'nvm use; npm run build'`.
- `npm ci`, `npm run typecheck`, `npm test`, `npm run build` (`npm run watch`).
- The minified bundle `custom_components/kraftvakt/frontend/kraftvakt-panel.js` is committed, because HACS installs from the repository.
  Rebuild after every change in `frontend/` and commit source and bundle together. CI fails when the committed bundle differs from a clean build.
- The bundle URL carries the manifest version. During development the browser may use an old bundle; reload without cache.

## Structure

`frontend/src/` has the panel element (routing on `hass.route`, the top menu, the draft, the save bar and the lock of the configuration pages), one module per page in `pages/`,
shared components in `components/`, and modules for the API, translations, navigation, the draft, validation, issue texts, entity names, formatting, the width query,
the styles the status page shares with its components, and the parts the configuration pages and the dialogs share (`section-styles.ts`).
The status page holds the regulation card; the power tiles with the meter, and the priority list, are components of their own.
One page per route under `/kraftvakt/`; `/kraftvakt` itself is the status page, and `?config_entry=` (from the integration's configure button) goes to the Appliances page.

A page that changes its layout by width uses its own width (`WidthQuery`), not HA's `narrow`, which follows the viewport:
HA's sidebar is docked on a phone in landscape in the app and leaves the page little room, while a tablet that HA calls narrow has room.

Logic is kept in modules outside the elements, so it is unit tested, see the `kraftvakt-testing` skill. Code that mirrors the backend and must be kept in step with it:

- the waiting times, the curve and the growth on repeated turn-on, the same as in `regulation/waiting.py`,
- a subset of the validation in `config_validation.py`: the limits, what is missing and completing the priority list, for quick feedback; the backend checks everything at save,
- the checks of default and domain actions against their entities, the same as in `actions.py` and `domain_actions.py`,
- the name of a charger that is not saved yet, the same rule as the backend,
- the types of the configuration and the status snapshot,
- reading the power sensor in W or kW, the same units as the backend.

## Behaviour

### Layout of the configuration pages and dialogs

The configuration pages and the dialogs share one set of parts, so the same thing looks the same everywhere, and a dialog is adapted to its smaller room.
The section header, the description and the footer note are in `section-styles.ts`.

- A page is a stack of cards made by `renderCard` in `ConfigPage`: a header with the title in HA's card header size and an optional control at the right end,
  such as an add button, then the description, the content, a list from edge to edge and a footer.
- A part of a card has a section header: a smaller title and an optional control at the right end, then its description and its fields.
- A dialog starts with the fields that concern the whole item, without a frame: the device, the entity and the power reserve. The rest is in groups.
  A group is a frame with a section header, a description and its fields, as a card is on a page.
  A group with a switch in its header is about something that can be turned on, and shows its fields only while it is on.
  Groups are not nested, so a field in a group, such as an action, has no frame of its own.
- A description under a title is secondary text. A footer has a note to the left of its control: the card footer under a divider, and the page footer under the last card.
- An alert is only for a state or a warning, such as the lock, the warning against manual control or an applied charger profile, never for an explanation.
- Fields are HA's own components with their own labels, helper texts and spacing, also where HA puts the label above one field and inside another.
  The panel's own text under a field, such as under an action or a condition, is indented as HA indents the helper text of a field.
- Texts tell the user what is configured and why. The more advanced the setting, the more technical the language may be.

### Configuration pages

- The configuration pages share one draft. Save stores everything, Discard goes back to the saved configuration.
  The panel checks the draft against the limits from `kraftvakt/capabilities` and works out what is missing itself, so errors show before saving,
  and Save is disabled while there are errors. Errors from the backend show at the fields until the next save.
- The panel asks before discarding unsaved changes when going to the status page; the browser asks when the page is closed. HA sidebar navigation cannot be stopped.
  The draft is discarded when the regulation starts.
- The configuration is fetched again at the first status, when the regulation starts or stops, when what is missing changes, and when the config version in the status changes,
  since entities can change the stored configuration at any time. A draft with unsaved changes is kept while stopped.
- While the regulation runs, the configuration pages are locked and show a banner with a button to stop the regulation, on one line.
  Forms and lists are dimmed, add buttons are disabled and dialogs only show the item.
- The configuration pages extend `ConfigPage`, which holds what they share: the locked look, the card, its footer, the page footer, the item list with its add button,
  and the entities other items use.
  The status page and the lock banner share the start and stop button.
- General and Advanced end with Restore defaults (HA's own words) in the page footer, shared in `SettingsFormPage`:
  each page passes the settings it restores, and the defaults come from the capabilities.
  General leaves out the power limit, since it is the tariff step the user has chosen, and the power sensor, which has no default.
  It only changes the draft, so it asks for no confirmation, and it is disabled while every setting it restores has its default.
- The warning against controlling regulated appliances outside Kraftvakt is shown only while a list is empty (appliances on the Appliances page, chargers on the EV charging page).
- Default is offered only for domains with a default action. When an entity is picked and the action is not set, the suggested domain action of its domain is chosen,
  with its values for the entity, or else Default when the domain has one. A default or domain action becomes an empty custom action when the new entity has none.
  A custom action starts as the default action. The rule is in `actions.ts`.
- The entity picker of an appliance or charger leaves out the entities that other appliances and chargers use.
- The charger dialog starts with the device, required, and every entity picker in it offers only the device's entities, none before a device is chosen.
  The panel checks, as the backend does, that the device exists and each entity belongs to it.
- Choosing another device clears every entity field that is not on the new device, keeps templates and custom actions,
  and adapts the actions to the new entity as a new entity does. It then asks the backend for the device's charger profile,
  and when there is one, the fields it fills replace those in the draft and an info under the device names the profile. Without a profile, nothing is filled in.
  The panel has no knowledge of chargers of its own.
- Each action of an appliance or charger has a group of its own, as the variant dialog has one per action it can override,
  except set charging current, which is in the charging current group with the currents it sets.
- The appliance dialog lists the variants by label, with drag and edit, and Add variant. In view mode the group is left out when there are no variants.
  What else is wrong or missing in a variant is shown under its label.
  A variant's edit button, and its row in the priority list, open the variant dialog: the expression and one switch per action to override it, both off by default.
  Switched on, the action starts from what it had while the dialog is open, or else a copy of the appliance's.
  The variant dialog edits a copy of the whole appliance; its Delete removes the variant with `item-changed`, since it changes the appliance.
- The variant dialog edits the appliance as it is in the draft, so Edit in the appliance dialog first applies the dialog's changes as OK does,
  then closes it and opens the variant dialog when it has closed. Edit is disabled while the appliance dialog has errors.
- A new entity adapts the actions of the appliance and every action a variant overrides the same way.
- The domain actions of the entity's domain are offered after Default, in the order of the table. Choosing one fills each value with the one already chosen for the parameter,
  or its default for the entity, so switching between them keeps a chosen HVAC mode. The values are a second `ha-form` under the choice:
  an option is a dropdown of the entity's options with HA's names for the states, and a temperature is a number box in HA's temperature unit with the entity's range as helper.
  A cleared value is `null`. A domain action becomes an empty custom action when the entity changes to one where it is not available.
- Cloud-controlled EV charger is a group with a switch under actively charging, and shows the start delay while it is on or the delay has an error.
  The start delay is kept when the switch is turned off, since it has no effect then.
- Finish ongoing charging after the charging window and End the override (a dropdown) are shown under the times of the charging window, only while the charger has one.
  Their values are kept when the window is removed, since they have no effect without one.
- Set charging current also offers Entity: an entity picker limited to the domains with a default set-current action, with a helper telling which service runs.
  Required until an entity is chosen.
- The boolean entity picker offers binary sensors, input booleans, switches and schedules. Templates are previewed with HA's `render_template` subscription,
  with `entity` as the frontend's state object. A result that is not a boolean gets a warning that it counts as false.
- Missing items are not marked in a dialog until a new item has been added. A new variant starts as an empty template, which is missing, not an error,
  so the appliance can be confirmed before the variant gets its expression. Actively charging has no «not set», offers a boolean entity first and shows it until one is chosen.
  Every preview reads the value as the backend does, so only evidence shows as true, and shows an entity's state as HA formats it before what it counts as;
  a boolean entity that is on or off shows only its state, which says the same.
  Car connected is shown as required when only one charger in the group may charge at a time, when the charger is cloud-controlled,
  or when it has a charging window and its override ends when the car is disconnected. A new charger gets the override end from the defaults in the capabilities.
- The power sensor picker offers sensors with device class power, without Kraftvakt's own sensors.
- The EV charging page has one card per charger group, with its name, its settings and its chargers in charging priority, and Add group under the cards.
  Without groups, a line of text says so, as an empty list does.
  A new group gets the first free name of «EV chargers», «EV chargers 2» and so on, so it has no error at once. A group can be deleted only when it has no chargers.
- A charger moves to another group by dragging it to that group's list, with `ha-sortable`'s `group`, which puts the dragged row back so the lists follow the draft.
  An empty list stays in view as a place to drop on.
- Configuration pages and dialogs show power in W.

### Advanced page

- The last page in the menu, with the settings most users never change.
  Its settings belong to `general` in the stored configuration, so issues for those fields send the user to it. The waiting time at the power limit is on the General page.
- Little text: the user reads the curve and the result, not how it is computed.
- First card, the waiting time curve: one line of text, sliders for steepness and pivot point (no tooltip, the value as plain text beside it, no input box, no helper text),
  a table and a graph that follow the draft while the sliders move. The pivot point is not marked on the graph.
- The card speaks of free power as a share of the power limit, not of utilization, since free power is the term the status page uses. The pivot slider shows free power,
  from 50 % at the left end to 1 % at the right; it moves over the stored pivot and shows 100 minus it; the stored value and the regulation use utilization.
- The table shows, for a range of free power from half the limit down to almost nothing, the free power in kW, the waiting time and the actual waiting time,
  rounded up to whole decision intervals since the step is turned on at the first decision after the waiting time. The line of text says why it is rounded.
  Times are minutes and whole seconds. Values come from the draft, with a dash when a setting is not set.
- The graph has the waiting time in percent on the y-axis, so its shape does not change with the waiting time at the limit, and free power in kW on the x-axis,
  decreasing to 0 at the right so the waiting time grows to the right. It starts a bit above half the limit, so the curve always starts flat at 0.
- Second card, the waiting time on repeated turn-on: a short text saying it is about the regulation turning the same appliance or ampere on over and over again,
  then one part for appliances and one for EV chargers. Each has dropdowns for the step and the number of steps,
  and a table with one column per turn-on in a row up to the one that reaches the cap, marked as holding for every time after it, with the waiting time and the actual waiting time.
  The first two follow the curve and show the waiting time at the pivot point, which the text says. Dropdowns keep their values as numbers in the draft.
- Third card, command repeat: a short text on why commands are repeated and that excluded appliances and chargers are left alone, and the interval in minutes.
- Fourth card, timeouts: a short text on what each timeout guards against, and the action timeout and the power sensor timeout in seconds.
- On a page at most 760 px wide the tables are left out and the graph is drawn small. Narrower, the tables do not fit with the most columns.

### Status page

- The status page shows everything in the status snapshot: averages against the limit, next decision, safe state and penalty with what is left and whether recovery has started,
  appliances with variant and waiting, chargers with current and state. Power is shown in kW and energy in kWh.
- While stopped, the regulation card lists what is missing, each with a link to the page where it is fixed.
- The regulation card's header holds the title, a chip for running or stopped, chips for safe state and penalty while active, and the next decision at the right end.
  Start and stop are in a footer under a divider, on every screen width; stop is a plain danger button, start a filled one.
- While the power sensor is valid again but the safe state lasts until the next decision, the safe state banner is an info that the regulation starts again at the next decision,
  not the error that the sensor gives no valid measurement.
- Countdowns are never ticking text. The next decision is a small ring that empties over one decision interval, animated by the browser (Web Animations API) so it needs no clock;
  the time is a tooltip. On a narrow screen only the ring is shown.
- A waiting step shows an icon (a timer for an appliance,
  a plus for one more ampere) before a thin bar that empties smoothly from when the waiting started to the decision that turns the step on, animated like the ring.
  What it is and the time are a tooltip. The bar is smooth because a wait can span very many regulation windows. On a phone only the icon is shown.
- The tiles are, from the left, consumption now, regulation average, average consumption and the power limit.
  Consumption now is the power sensor's state read in the panel, so it updates live. Under each average is the time it covers.
  A tile is a button that fires `hass-more-info` for its entity: the power sensor, or Kraftvakt's own entity found by platform and translation key,
  so an entity ID the user has changed is still found. A tile without an entity, such as one of Kraftvakt's that is not in the registry, is not a button.
- The meter is a bar for consumption now. Each other value is a triangle above the bar pointing down at it, in its own colour, and each tile has the same triangle as swatch.
  Nothing else is drawn on the meter. Under the bar is a kW scale with readable ticks, reaching a bit above the limit and every value.
- Appliances and chargers share one full-width priority list card. Each charger group has a row with its name and its own rank at its position,
  and its chargers are indented under it in the group's current charging priority. Every row is one line, with columns that line up without headings: rank,
  name with the variant after it, current, waiting and state chip. An appliance has no current, so its name also takes the current column.
  The rank is right aligned with digits of equal width.
  A name too long for its column is cut with an ellipsis and has the whole name as a tooltip; the variant is cut first, down to a few letters.
  - On a phone (a status page at most 600 px wide) a row is only the icon, the name, a charger's current, the waiting icon and the state chip:
    the rank, the variant, the charger count, the ampere bars, the waiting bar and the text that there are no chargers are left out.
    The rows share no columns there: each row puts its chip at the right end, what it has of the current and the waiting icon just before it,
    and gives the name the rest, since a shared column would be as wide as the widest chip or current in any row.
  - Icons instead of short texts, each with its sentence as a tooltip, and no legend. A group's row shows how many of its chargers are charging of all.
  - The current column has the current before one bar per ampere from min to max, filled up to the current. The filled bars of a bypassed charger are hatched.
    A charger without a current, which is deactivated, shows a dash and empty bars, and on a phone nothing.
  - The state chip has an icon and a word, with the whole sentence as a tooltip. An appliance shows excluded, on or off, and the title of an excluded appliance is dimmed.
    A charger shows its state from the status, with its charging window as the word when it is outside it.
  - The row of an appliance or EV charger fires `hass-more-info` for its entity, the entity Kraftvakt turns on and off or activates,
    since Home Assistant has no such dialog for a device. A row whose entity Home Assistant does not have, and a group's row, opens nothing.
    A row or tile clicked with the mouse lets go of the focus before the dialog opens, since Home Assistant gives the focus back when the dialog closes,
    and the focus ring would look like a selection. Opened from the keyboard, it keeps the focus.
  - A resting charger is shown as bypassed, without when it is tried again.
  - A starting charger is shown as starting, and its sentence tells when its time to start ends and that its power reserve is kept free until then,
    since nothing else on the page tells why nothing below it is turned on while power looks free.
  - A dashed cut-off line goes under the last entry that is on: an appliance, or a group's row while one of its chargers is activated and not bypassed.
    It is hidden when nothing is on, or when only excluded appliances are below the last entry that is on, so something that can be turned on is always below it.
    It shows the free power and its share of the power limit while that is above 0, and explains itself in a tooltip. By the fixed order nothing below the line is on.
- Colours come from Home Assistant's theme variables, set once on `:host`: the Energy dashboard's grid colour for the tariff average, a teal colour for everything EV charging,
  and HA's active and inactive state colours for appliance icons. Each appliance shows its entity's icon, and what is off is dimmed.
  An appliance whose entity is missing, or whose icon HA cannot show in the panel (an icon set that is not loaded renders nothing), shows a default icon instead:
  the icon step is one icon wide, and the entity's icon pushes the default icon out of it. The safe state and penalty chips are in the alarm colour and show only while active.

## Home Assistant components

Defined when the panel renders, and the only ones to use (checked against the HA version in `requirements_dev.txt`): `ha-form` with selectors (`text`, `number`, `select`, `entity`,
`template`, `action`, `time`, `boolean`), `ha-selector`, `ha-sortable` (listen to `item-moved` and re-render; it does not move elements), `ha-dialog`, `ha-card`, `ha-alert`,
`ha-button`, `ha-icon-button`, `ha-svg-icon`, `ha-state-icon` (`.hass`, `.stateObj`), `ha-switch`, `ha-formfield`, `ha-settings-row`, `ha-expansion-panel`, `ha-md-list-item`,
`ha-code-editor`, `ha-yaml-editor`, `ha-menu-button`, `ha-tab-group` with `ha-tab-group-tab` (event `wa-tab-show`), `ha-slider` (`.min`, `.max`, `.step`, `.value`, `.withTooltip`,
event `input`; defined by the number selector that the same page loads).

Not available, do not use: `ha-textfield`, `ha-radio`, `ha-md-list`, `ha-list-item`, `ha-wa-dialog`, `ha-md-dialog`, `ha-segmented-button`, `window.loadCardHelpers`,
and no `partial-panel-resolver` hacks.

- Wait for `customElements.whenDefined("ha-form")` before the first render.
- The action editor needs `hass.loadFragmentTranslation("config")`, otherwise its labels are empty.
- `ha-dialog` is built on `wa-dialog`: `open`, `header-title`, step `footer`, event `closed`. When it closes itself, set `open` false on `closed`.
- When the HA version in `requirements_dev.txt` is raised, test the panel by hand against this list.

## Translations

Panel texts are in `frontend/src/translations/en.json` and `nb.json` (English is the default, Norwegian the first translation), chosen from `hass.language`.
The keys are type checked, and `nb.json` must have every key in `en.json`.
Use the same terms as the rest of each translation file, and the same as the integration's own translations.
