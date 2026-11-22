---
name: kraftvakt-panel
description: The Kraftvakt panel in frontend/ - Lit and TypeScript structure, routes, which Home Assistant components work in a custom panel, the draft and save flow, translations,
  and building the committed bundle. Use before changing anything in frontend/ or custom_components/kraftvakt/frontend/.
---

# Kraftvakt panel

The panel is the only user interface: a sidebar panel for administrators with a top menu holding the status page, the configuration pages (General, Appliances, EV charging,
Advanced) and the diagnostics page. Messages to the backend are in the `kraftvakt-backend` skill.

## Build

- Lit + TypeScript + Rollup in `frontend/`, Lit with `experimentalDecorators` and `useDefineForClassFields: false`.
  Versions are pinned in `package.json` (Lit and TypeScript as the HA frontend for the supported HA version).
- Node from `.nvmrc` (the same as the HA frontend uses), via nvm or nvm.fish.
  Node is not on `PATH` in a plain non-interactive shell; activate it with nvm first, for example `fish -c 'nvm use; npm run build'`.
- `npm ci`, `npm run format:check`, `npm run typecheck`, `npm test`, `npm run build` (`npm run watch`).
- Prettier formats everything in `frontend/` with its defaults and the line length from `.editorconfig`; `npm run format` applies it.
- The minified bundle `custom_components/kraftvakt/frontend/kraftvakt-panel.js` is committed, because HACS installs from the repository.
  Rebuild after every change in `frontend/` and commit source and bundle together. CI fails when the committed bundle differs from a clean build.
- The bundle URL carries the manifest version. During development the browser may use an old bundle; reload without cache.

## Structure

`frontend/src/` has the panel element (routing on `hass.route`, the top menu, the draft, the save bar and the lock of the configuration pages), one module per page in `pages/`,
shared components in `components/`, and modules for the API, translations, navigation, the draft, validation, issue texts, entity names, formatting, the width query,
the styles the status page shares with its components, and the parts the configuration pages and the dialogs share (`section-styles.ts`).
The status page holds the regulation card; the power tiles with the meter, and the priority list, are components of their own.
The diagnostics page subscribes to its own feed while it is open, and works out its history in `diagnostics.ts`.
One page per route under `/kraftvakt/`; `/kraftvakt` itself is the status page, and `?config_entry=` (from the integration's configure button) goes to the Appliances page.

A page that changes its layout by width uses its own width (`WidthQuery`), not HA's `narrow`, which follows the viewport:
HA's sidebar is docked on a phone in landscape in the app and leaves the page little room, while a tablet that HA calls narrow has room.

Logic is kept in modules outside the elements, so it is unit tested, see the `kraftvakt-testing` skill. Code that mirrors the backend and must be kept in step with it:

- the waiting times, the curve and the growth on repeated turn-on, the same as in `regulation/waiting.py`,
- the choices of the regulation window, the same as in `config_model.py`,
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
- A dialog starts with the fields that concern the whole item, without a frame: the device, the entity and a charger's power at minimum current. The rest is in groups.
  A group is a frame with a section header, a description and its fields, as a card is on a page.
  A group with a switch in its header is about something that can be turned on, and shows its fields only while it is on.
  An add button is a filled button at the right end of a header; where the header holds a switch, it goes at the right end under the list.
  Groups are not nested, so a field in a group, such as an action, has no frame of its own.
  A group with several parts, such as two actions, two conditions or a choice and what it shows, has a line from edge to edge between them,
  as Home Assistant divides a card. An action field draws the same line between how the action is given and what that shows,
  such as the values of a domain action, the entity or the action editor, and a condition field between where its value comes from and the value.
- A description under a title is secondary text. A footer has a note to the left of its control: the card footer under a divider, and the page footer under the last card.
- An alert is only for a state or a warning, such as the lock, the warning against manual control or an applied charger profile, never for an explanation.
- Fields are HA's own components with their own labels, helper texts and spacing, also where HA puts the label above one field and inside another.
  The panel's own text under a field, such as under an action or a condition, is indented as HA indents the helper text of a field.
- Most users read the helper texts, not the README, so the details of a setting are in its helper text, and the README stays general.
  A helper text tells the effect of the setting for the user, and when to use it, as briefly as it can, followed by the range and the default;
  not how the regulation works or why. Users click around to set it up and do not read long texts,
  so a helper text is one or two short sentences before the range. A label is worded so the helper text can be short, or left out.
  The more advanced the setting, the more technical the language may be.

### Configuration pages

- The configuration pages share one draft. Save stores everything, Discard goes back to the saved configuration.
  The panel checks the draft against the limits from `kraftvakt/capabilities` and works out what is missing itself, so errors show before saving,
  and Save is disabled while there are errors. Errors from the backend show at the fields until the next save.
- The panel asks before discarding unsaved changes when going to the status page or the diagnostics page; the browser asks when the page is closed.
  HA sidebar navigation cannot be stopped.
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
  General leaves out the power limit, since it is the tariff step the user has chosen, and the power sensor and the regulation window, which have no default.
  It only changes the draft, so it asks for no confirmation, and it is disabled while every setting it restores has its default.
- The warning against controlling regulated appliances outside Kraftvakt is shown only while a list is empty (appliances on the Appliances page, chargers on the EV charging page).
- Default is offered only for domains with a default action. When an entity is picked and the action is not set, the suggested domain action of its domain is chosen,
  with its values for the entity, or else Default when the domain has one. A default or domain action becomes an empty custom action when the new entity has none.
  A custom action starts as the default action. The rule is in `actions.ts`.
- The entity picker of an appliance or charger leaves out the entities that other appliances and chargers use.
- The charger dialog starts with the device, required, and every entity picker in it offers only the device's entities, none before a device is chosen.
- The charger dialog has no entity of its own. After the device and the power at minimum current, the group Turn charging on and off holds a choice of three
  (a list of radio buttons): the switch for on and off, which shows an entity picker limited to the domains with a default action to turn on and off;
  the charging current, which shows a line that points to the charging current group; and custom actions, which shows the action editors to activate and deactivate,
  without a choice of kind, since a charger has only custom actions. What the other choices hold is kept out of view.
  A new charger starts with the switch for on and off, the default in the capabilities, empty custom actions,
  and the set-current action as an entity that is not chosen.
  The panel checks, as the backend does, that the device exists and each entity belongs to it.
- Labels name the kind of entity they take, such as «Binary sensor or switch», «Status sensor» or «Switch or thermostat», never a bare «Entity» or «State».
  What the user writes is named Custom actions (Egendefinerte handlinger), made with the action editor, and Custom template (Egendefinert mal),
  in every choice and label, never a bare «Custom», «Template» or «Actions».
- Choosing another device clears every entity field that is not on the new device, and keeps templates and custom actions.
  It then asks the backend for the device's charger profile, and when there is one,
  the fields it fills replace those in the draft and an info under the device names the profile. Without a profile, nothing is filled in.
  The panel has no knowledge of chargers of its own.
- Each action of an appliance has a group of its own, as the variant dialog has one per action it can override.
  The actions of a charger are in the group of what they do: activate and deactivate in Turn charging on and off, and set charging current in the charging current group.
- The appliance dialog has, after the entity, the actions, the group Essential appliance with a switch, Fixed load with a switch and the power reserve,
  the variants, and Display values with the display power and temperature, condition fields of the kinds display power and display temperature that preview the value.
  The display temperature lists the temperatures of the device in one dropdown under Entity: each temperature sensor, and each thermostat's current and set temperature,
  named after the entity; without a device, it is an entity picker of temperature sensors.
  The display sensors offer only the entities of the device of the appliance's entity, or any sensor when it has none,
  and a new entity clears the display sensors that are not on its device, as a new device does for a charger.
  Fixed load turned off clears the power reserve; its helper warns against it for an appliance with control of its own, since most users would set it otherwise.
  An essential appliance has neither Fixed load nor the variants, and its switch is disabled while the appliance has variants.
  Turned on, it clears the power reserve.
- The draft keeps the entries of the essential appliances above every other entry, each part in its own order,
  so dragging across the border puts the entry back at the border, and an appliance made essential goes to the bottom of the essential ones.
  Their rows have a light golden background, the same as on the status page, defined once on the panel's `:host`.
- The appliance dialog lists the variants by label, with drag and edit, and Add variant. In view mode the group is left out when there are no variants.
  What else is wrong in a variant is shown under its label. What is missing, such as the expression of a new variant, is not:
  it is set in the variant dialog, and the priority list shows it, so here it would look like a fault to fix in this dialog.
  A variant's edit button, and its row in the priority list, open the variant dialog: the expression and one switch per action to override it, both off by default.
  Switched on, the action starts from what it had while the dialog is open, or else a copy of the appliance's.
  The variant dialog edits a copy of the whole appliance; its Delete removes the variant with `item-changed`, since it changes the appliance.
- The variant dialog edits the appliance as it is in the draft, so Edit in the appliance dialog first applies the dialog's changes as OK does,
  then closes it and opens the variant dialog when it has closed. Edit is disabled while the appliance dialog has errors.
- A new entity adapts the actions of the appliance and every action a variant overrides the same way.
- The domain actions of the entity's domain are offered after Default, in the order of the table. Choosing one fills each value with the one already chosen for the parameter,
  or its default for the entity, so switching between them keeps a chosen HVAC mode. The values are a second `ha-form` under the choice:
  an option is a dropdown of the entity's options with HA's names for the states, and a temperature is a choice of a fixed value, Sensor, number or thermostat,
  or a template, then a number box in HA's temperature unit with the entity's range as helper, an entity picker, or a template editor.
  The entity picker offers sensors, numbers and thermostats but the appliance's own entity, and its helper shows the temperature now and the range it is kept within.
  A thermostat adds a dropdown of its set or current temperature, the set temperature at first. Switching between them starts the value empty.
  A cleared value is `null`. A domain action becomes an empty custom action when the entity changes to one where it is not available.
- Actively charging is one group with the charging power (Power sensor or Custom template), required, and car charging (a condition of the kind actively charging), optional.
  A charging power template is previewed as W.
- Car connected, car charging and the fault flag also offer Status sensor: an entity of the device, a choice of whether the chosen states are those for true
  (for example States for connected) or those for false (States for disconnected), and the states.
  The states offered are the entity's options, its current state and the states in its history over the last week, each named as HA shows it with the state after it,
  and a state that is typed is taken too. Choosing another entity clears the states.
- Each charger group has the setting dynamic charging order under one EV charger at a time. Its helper keeps its line break, since HA shows a helper as one paragraph.
  Both are disabled, with a line in their helpers that says why, while the group has fewer than two chargers, since they make no difference then, and keep their values.
- Cloud-controlled EV charger is a group with a switch under actively charging, and shows the start delay while it is on or the delay has an error.
- Deactivate on fault is the last group, with a switch. It shows the fault flag, a condition field of the kind fault, while it is on or the flag has an error,
  and keeps it when it is turned off.
  The start delay is kept when the switch is turned off, since it has no effect then.
- Charge until the car is disconnected and End the override (a dropdown) are shown under the times of the charging window, only while the charger has one.
  Their values are kept when the window is removed, since they have no effect without one.
- Set charging current offers Number entity: an entity picker limited to the domains with a default set-current action, with a helper telling which service runs.
  Required until an entity is chosen.
- The boolean entity picker offers binary sensors, input booleans, switches and schedules. Templates are previewed with HA's `render_template` subscription,
  with the item's variables as in the backend, `entity` being the frontend's state object, and the helper lists them.
  A result that is not a boolean gets a warning that it counts as false.
- Missing items are not marked in a dialog until a new item has been added. A new variant starts as an empty template, which is missing, not an error,
  so the appliance can be confirmed before the variant gets its expression.
  Car connected has no «not set», offers a boolean entity first and shows it until one is chosen.
  Every preview reads the value as the backend does, so only evidence shows as true, and shows an entity's state as HA formats it before what it counts as;
  a boolean entity that is on or off shows only its state, which says the same.
  A new charger gets the override end from the defaults in the capabilities.
- The power sensor picker offers sensors with device class power, without Kraftvakt's own sensors.
- The regulation window is a dropdown of its choices for the update interval, each as «N updates (X s)», disabled until the interval is known.
  When the power sensor is chosen, or set without an interval, the panel asks the backend for the interval and chooses the window closest to the length it had,
  10 s at first. Its helper tells the interval, or that the power sensor must be chosen, is being measured, could not be measured or reports too seldom,
  and it is not marked as missing while it cannot be chosen. Like a setting without a default, it may be saved while it is not set.
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
  rounded up to whole regulation windows since the step is turned on at the first decision after the waiting time. The line of text says why it is rounded.
  Times are minutes and whole seconds. Values come from the draft, with a dash when a setting is not set.
- The graph has the waiting time in percent on the y-axis, so its shape does not change with the waiting time at the limit, and free power in kW on the x-axis,
  decreasing to 0 at the right so the waiting time grows to the right. It starts a bit above half the limit, so the curve always starts flat at 0.
- Second card, the waiting time on repeated turn-on: a short text saying it is about the regulation turning the same appliance on over and over again,
  then dropdowns for the step and the number of steps,
  and a table with one column per turn-on in a row up to the one that reaches the cap, marked as holding for every time after it, with the waiting time and the actual waiting time.
  The first two follow the curve and show the waiting time at the pivot point, which the text says. Dropdowns keep their values as numbers in the draft.
- Third card, EV chargers: a short text on what it is for, the damping time in seconds, and the waiting time for EV chargers as a dropdown of factors.
- Fourth card, command repeat: a short text on why commands are repeated and that excluded appliances and chargers are left alone, and the interval in minutes.
- Fifth card, timeouts: a short text on what each timeout guards against, and the action timeout and the power sensor timeout in seconds.
- On a page at most 760 px wide the tables are left out and the graph is drawn small. Narrower, the tables do not fit with the most columns.

### Status page

- The status page shows everything in the status snapshot: averages against the limit, next decision, safe state and penalty with what is left and whether recovery has started,
  appliances with variant and waiting, chargers with current and state. Power is shown in kW and energy in kWh.
- While stopped, the regulation card lists what is missing, each with a link to the page where it is fixed.
- The regulation card's header holds the title, a chip for running or stopped, chips for safe state and penalty while active, and the next decision at the right end.
  Start and stop are in a footer under a divider, on every screen width; stop is a plain danger button, start a filled one.
- While the power sensor is valid again but the safe state lasts until the next decision, the safe state banner is an info that the regulation starts again at the next decision,
  not the error that the sensor gives no valid measurement.
- Countdowns are never ticking text. The next decision is a small ring that empties over one regulation window, animated by the browser (Web Animations API) so it needs no clock;
  the time is a tooltip. On a narrow screen only the ring is shown.
- A waiting appliance shows a timer icon before a thin bar that empties smoothly from when the waiting started to the decision that turns it on, animated like the ring.
  What it is and the time are a tooltip. The bar is smooth because a wait can span very many regulation windows. On a phone only the icon is shown.
  An EV charger whose next ampere step waits shows the same instead of the power to free, with the reason:
  the damping for an activated EV charger, and the waiting time for one that is activated again.
- Otherwise the row of the next step shows, in the same column, an icon and the power to free in kW, with a sentence as tooltip that tells what it is freed for:
  turning on an appliance, activating an EV charger or giving it one more ampere. On a phone only the icon is shown.
- The tiles are, from the left, consumption now, regulation average, average consumption and the power limit.
  Consumption now is the power sensor's state read in the panel, so it updates live. Under each average is the time it covers.
  A tile is a button that fires `hass-more-info` for its entity: the power sensor, or Kraftvakt's own entity found by platform and translation key,
  so an entity ID the user has changed is still found. A tile without an entity, such as one of Kraftvakt's that is not in the registry, is not a button.
- The meter is a bar for consumption now. Each other value is a triangle above the bar pointing down at it, in its own colour, and each tile has the same triangle as swatch.
  Nothing else is drawn on the meter. Under the bar is a kW scale with readable ticks, reaching a bit above the limit and every value.
- Appliances and chargers share one full-width card, Appliances and EV chargers, in priority order. Each charger group has a row with its name and its own rank at its position,
  and its chargers are indented under it in the group's current charging priority.
  A group with one charger is that charger's row alone, with the group's rank and without indent, since the group's name and settings make no difference then.
  The configuration pages always name the group, also in the priority list. Every row is one line, with columns that line up without headings: rank,
  name with the variant after it, current, power, waiting and state chip. An appliance has no current, so its name also takes the current column.
  The power is an appliance's display power or a charger's charging power, in kW, left out when no row has one.
  An appliance's display temperature, with one decimal, is in the current column, right aligned with the ampere bars, since an EV charger never has one;
  an appliance without one lets its name take the current column. An essential appliance's row has a light golden background.
  The name takes the room that is left, and the other columns are as wide as their content, so they line up at the right.
  The gaps, the waiting bar and the space at the right end grow with the list's own width (container query units),
  from tight just above the phone layout to the widest list the panel gets, where the columns after the name take its right half.
  The rank keeps a small fixed distance to the name.
  The rank is right aligned with digits of equal width.
  A name too long for its column is cut with an ellipsis and has the whole name as a tooltip; the variant is cut first, down to a few letters.
  - On a phone (a status page at most 600 px wide) a row is only the icon, the name, a charger's current, the waiting icon and the state chip:
    the rank, the variant, the power, the temperature, the charger count, the ampere bars, the waiting bar and the text that there are no chargers are left out.
    The rows share no columns there: each row puts its chip at the right end, what it has of the current and the waiting icon just before it,
    and gives the name the rest, since a shared column would be as wide as the widest chip or current in any row.
  - Icons instead of short texts, each with its sentence as a tooltip, and no legend.
    A group's row shows how many of its chargers are charging of all.
  - The current column has the current before one bar per ampere from min to max, filled up to the current. The filled bars of a bypassed charger are hatched.
    A charger without a current, which is deactivated, shows a dash and empty bars, and on a phone nothing.
  - The state chip has an icon and a word, with the whole sentence as a tooltip. An appliance shows excluded, on or off, with a dot for on and off,
    and the title of an excluded appliance is dimmed.
    A charger shows its state from the status, with its charging window as the word when it is outside it, and the icon and colour of its state sensor.
    Stopped and fault are in the alarm colour, and the states that wait to be allowed in HA's amber colour.
  - The row of an appliance or EV charger fires `hass-more-info` for its entity, the entity Kraftvakt turns on and off or activates,
    since Home Assistant has no such dialog for a device. A row whose entity Home Assistant does not have, and a group's row, opens nothing.
    A row or tile clicked with the mouse lets go of the focus before the dialog opens, since Home Assistant gives the focus back when the dialog closes,
    and the focus ring would look like a selection. Opened from the keyboard, it keeps the focus.
  - A queued charger is shown as Queued, with its own sentence in a group with several at once and dynamic charging order, where it waits for room.
    An activated charger whose car does not charge tells that it waits at the minimum current.
    A charger held at its minimum current while its car charges shows as charging, without a reason why its current does not rise.
  - A starting charger is shown as starting, and its sentence tells when its start delay ends, and that its power at minimum current is kept free until then,
    since nothing else on the page tells why nothing below it is turned on while power looks free.
  - A dashed cut-off line goes under the last entry that is on: an appliance, or a group's row while one of its chargers is activated and not bypassed.
    It is hidden when nothing is on, or when only excluded appliances are below the last entry that is on, so something that can be turned on is always below it.
    It shows the free power and its share of the power limit while that is above 0, and explains itself in a tooltip. By the fixed order nothing below the line is on.
- Colours come from Home Assistant's theme variables, set once on `:host`: the Energy dashboard's grid colour for the tariff average, a teal colour for everything EV charging,
  and HA's active and inactive state colours for appliance icons. Each appliance shows its entity's icon, and what is off is dimmed.
  An appliance whose entity is missing, or whose icon HA cannot show in the panel (an icon set that is not loaded renders nothing), shows a default icon instead:
  the icon step is one icon wide, and the entity's icon pushes the default icon out of it. The safe state and penalty chips are in the alarm colour and show only while active.

### Diagnostics page

- The last page in the menu, for advanced users. It shows only what Kraftvakt already holds in memory for Download diagnostics, and never explains in words why a step
  is on, off or waiting, since such texts would have to follow every rule of the regulation and would mislead in an edge case.
- It is shown also while the regulation is stopped, since what is kept stays until a reload or a restart.
- First a row of health tiles: the power sensor, the actions, the regulation and the command repeat, each with a dot in the success, warning or alarm colour, or grey.
  The regulation tile shows how long it has run as whole days, or else hours, or else minutes, rounded down, with the start under it,
  since a date and time is hard to read for a long run.
- Then the timeline over the last 15, 30 or 60 minutes, as the user chooses, 60 at first:
  the consumption from the measurements kept, and from the decisions kept the regulation average, the tariff average
  and the power limit, with a lane under it per appliance and EV charger in priority order, sharing the time axis. A dotted line marks the oldest decision kept.
  The card has no description: a legend under its title names every colour and mark, also on and the charging current of the lanes.
  A lane shows what each command set until the next command, starting with the commands before the decisions kept:
  an appliance on in the state colour, an EV charger's current as a teal bar of its height from min to max, and the waiting hatched.
  One without a command since the last start is as it is now while the regulation runs.
  Before the last start, and after the last decision while stopped, it is hatched as not known, since the commands of a stop are not kept, and nothing is guessed,
  so the lanes are hatched just after a start and fully known after an hour.
  Hovering shows the consumption at that time and the decision that covers it.
- Then the event log: the commands of the decisions kept and the failed actions, newest first, also the commands of one decision,
  so the log reads in one direction. Filtered by all, commands or failed actions.
  A row opens the decision with its averages, whether the power sensor was valid, the safe state, the penalty, the waiting and all its commands,
  or the error of a failed action, and marks its time in the chart. The footer links to the integration's page for Download diagnostics.
- Commands are named by the item's name in the status, with the variant's label after it; a failed action shows its action as the backend gives it, in English.

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
