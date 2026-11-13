---
name: kraftvakt-regulation
description: How Kraftvakt's regulation must behave - concepts, measurement and averages, decisions, waiting times, penalty, safe state, start and stop, variants, excluded appliances and EV charging. Use before changing or reviewing anything in regulation/, measurement.py, runtime.py or settings.py, or when a question is about what the regulation should do.
---

# Kraftvakt regulation

Kraftvakt is a Home Assistant integration for the Norwegian capacity tariff.
The grid company sets the capacity part of the grid fee from the hours of the
month with the highest consumption. Kraftvakt keeps the average consumption
over the last hour just below a power limit chosen by the user, by turning
appliances that can wait on and off in priority order. Everything runs locally.

This file is the specification. When a rule here is unclear, ask the owner
instead of deciding. The ranges and defaults below are part of the
specification; the code holds them in one place (`config_model.py`).

## Concepts

| Term | Meaning |
|---|---|
| Power limit | The highest allowed average power, 1000–50 000 W, default 10 000 W. The target the regulation keeps just below. |
| Power sensor | A sensor from another integration with the house's total momentary power, in W or kW. A sensor without unit is read as W. Other units, non-numbers, `unknown` and `unavailable` are invalid. Negative values count as 0 W. |
| Regulation window | 10–600 s, default 10 s. |
| Regulation average | Time-weighted average of the power sensor over one regulation window. Drives all decisions. |
| Regulation interval | 1–4 regulation windows, default 1. A decision is made every N windows. |
| Tariff window | One hour back from now, sliding, not configurable. |
| Tariff average | Time-weighted average of the power sensor over the tariff window. The regulation uses it only for the penalty. Why sliding: the grid company measures each clock hour, and every clock hour is one of the sliding hours; a sliding hour also finds overconsumption early, where a budget per clock hour could be used up in the middle of the hour and leave no power for the rest of it. |
| Decision | What the regulation decides at each interval. All evaluation and all switching happens at decisions. The command repeat sends commands also between decisions, but only for the state the regulation has already set. |
| Command repeat interval | 10–60 min, default 30 min. How long an appliance or charger may go without a command before the command for its state is sent again. |
| Action timeout | 10–3600 s, default 60 s. How long an action may run before it is stopped and counts as failed. Why: the actions run one at a time, so one that never finishes would hold back every later command, also the turn-offs. |
| Power sensor timeout | 10–3600 s, default 300 s. How long the power sensor may go without reporting, also an unchanged value, before it counts as invalid. Why: a HAN reader that loses its connection may keep its last value. |
| Free power | Power limit minus regulation average. |
| Turn-on margin | How far below the limit the regulation average must be before anything is turned on, 1–1000 W, default 100 W. 0 is not allowed. |
| Power reserve | Optional free power an appliance needs before it may be turned on, ≥ 0 W, no upper limit. |
| Waiting time | Time that must pass before an appliance is turned on. |
| Waiting time curve | The share of the waiting time at the limit, by how close the regulation average is to the limit. Set with steepness and pivot point. |
| Appliance | An entity Kraftvakt turns on and off with configurable actions. |
| Priority list | Sorted list of appliances, their variants and an entry per charger group. Top is highest priority, turned off last. |
| Variant | Extra entry for an appliance with a label and a true/false expression, giving it another place in the list, and optionally its own actions. |
| Current variant | The variant of the topmost true expression, or the appliance itself when none is true. Only this entry takes part. |
| Step | An entry the regulation switches: the current variant of an appliance, or an ampere step. |
| Safe state | Everything off and nothing turned on, because there is no valid power measurement. |
| Penalty threshold | 0–10 000 W above the power limit, default 100 W. |
| Overconsumption | Net energy above the power limit since the overconsumption state started (above adds, below subtracts). |
| Penalty period | Safety valve: everything held off until the overconsumption is paid back. Should never be needed. |
| Charger group | A named group of chargers with its own entry in the priority list and its own EV charging settings. A charger is in exactly one group. |
| Ampere step | One ampere of an EV charger's current, treated by the regulation as an appliance. |
| Bypassed charger | A charger that does not draw power and so must not stand in the way of others. |
| Waiting charger | With one charger at a time: a charger that may not charge because another in its group is actively charging. |
| Charging window | Optional daily time span in whole minutes, in HA's time zone, may span midnight, start ≠ end. |

Resolution of settings: power in whole watts, the regulation window and the
waiting time at the limit in whole seconds, currents in whole amperes. Power
is in W everywhere inside the regulation, the configuration and the entities,
energy in Wh; the status page shows kW.

## Ground rules

- Kraftvakt only decides whether an appliance may be on. It never estimates
  what an appliance uses from changes in the total consumption.
- It does not read or react to the state of appliances. It assumes each one is
  as Kraftvakt last told it, and repeats that command now and then (see
  Command repeat). Switching appliances outside Kraftvakt can disturb
  the regulation. Exception: for chargers it reads actively charging and car
  connected.
- A failed action, also one stopped by the action timeout, is logged and not retried. The regulation goes on as if it
  worked. The command repeat sends the command for the state again later.
- Only the current configuration is regulated. Kraftvakt never hands an
  appliance or charger back: removed, excluded, with the regulation stopped or
  the integration removed, it stays as last commanded, and the user sets it
  as wanted.
- The configuration can only be changed while the regulation is stopped, except
  the user's switches (one per appliance, two per charger), finish after window
  (see EV charging) and the power limit (see Power limit entity). Everything is off while stopped, so removed
  appliances are already off and new ones are controlled from the next start.
- The state of the regulation (on/off, waiting times, repeated turn-on counters,
  overconsumption, penalty, current charging priority, bypassed chargers,
  rests, current variants, excluded appliances, when each appliance and
  charger last got a command) starts again with defaults at
  every start: HA or integration start, user start, after the safe state and
  after a penalty. The configuration and the
  switch positions are kept over any restart.
- True/false from HA (variant expressions, car connected, actively charging)
  is a boolean entity or a template, and for actively charging also a power
  sensor. Only evidence makes it true: an entity that is `on`, a template that
  gives the boolean true, or a valid power above 100 W. Everything else is
  false, also unavailable entities and sensors and failing templates.
  Settings are named so that true means the thing is the case.

## Measurement

- Windows keep their own cadence from when the integration starts, scheduled
  at absolute times, also while the regulation is stopped. Each regulation
  average covers its own window, without overlap.
- Averages are energy divided by time, correct for any update rate of the
  sensor (each value holds until the next).
- At startup (HA or integration start) the hour before is taken from HA's
  recorder history of the power sensor, read like live values (an invalid
  value keeps the last valid one in place, and the oldest valid value fills
  the time before it). The time HA was down counts with the last value
  recorded before it stopped. Without a recorder or any valid history, the
  missing past is filled with the first measured value. The regulation window
  is not affected: the first one starts at startup. Why: everything is
  turned off at start, so the first value after a restart is only the
  background and cannot stand for the hour before.
- Validity is the state when a window closes. A power sensor that has not
  reported for the power sensor timeout is invalid. A gap inside a window is filled
  with the last valid value.
- One window closing without a valid value is tolerated (the last valid value
  is used). Two in a row make the averages unknown: the average sensors become
  unavailable until a valid value comes, also while the regulation is stopped.
  The history is kept, and the gap counts with the last valid value before it,
  like the time HA was down. Why: the first value after the gap is only the
  background (everything is off in the safe state) or a short peak while the
  appliances are turned off, so it cannot stand for the time before.
- Before the first valid value there is no average. Windows without any
  measurement count as invalid.
- Saving a configuration does not restart the averages. A new power sensor is
  followed from the save, a new window length applies from the next window.

## Decisions

- With interval N, a decision is made when the N-th window that started after
  the start of the regulation (or the previous decision) has closed. Windows
  that started before the start do not count, so the first decision comes
  after N to N+1 windows. The decision time is the end of that window.
- Order inside a decision, each step may end it:
  1. Safe state.
  2. Window overrides that have ended are switched off.
  3. Overconsumption.
  4. Penalty.
  5. EV chargers: allowed, bypassed, current priority, waiting.
  6. Forced switch-offs: chargers not allowed to charge (all ampere steps off and
     deactivate), newly bypassed chargers down to one ampere step,
     excluded appliances, appliances that switch variant or are included
     again.
  7. Build the ordered steps (current variants, ampere steps in place of
     the entry of their group).
  8. Above the limit: switch off the lowest priority step that is on and not a
     bypassed charger's, without waiting, and cancel any waiting. When step 6
     switched off something that was on, nothing more is switched off;
     the waiting is still cancelled and nothing is turned on. Why: the
     average was measured before the forced switch-off, so switching off one
     more would often be too much.
  9. Turn on: only the first step that is off and not skipped may be turned on.
     Without room for it, room is made below it instead (see Making room).
- An appliance gets at most one command per decision, the last one. Turned
  off and on again at the same decision, it only gets the turn-on. Why:
  switching a device off and on at once wears its relays, for example in a
  thermostat.
- Only one step is turned on or off per decision based on free power. Several
  may be switched off at once only when consumption must drop at once or
  switching does not change consumption: start and stop, safe state, penalty,
  chargers not allowed to charge, bypassed chargers, excluded appliances,
  variant switches, appliances included again, and the other charger
  deactivated when one is activated with one charger at a time.
- Turn on only when the regulation average is under the limit minus the
  turn-on margin, and average plus power reserve is at most the limit. Switch
  off only when the average is above the limit, or to make room. Between limit
  minus margin and the limit, both included, nothing is turned on, and nothing
  is switched off except to make room. Why: commands run
  just after a window closes, and a real meter reports the change only at its
  next update, so the window after a decision still holds the consumption
  from before its commands. The margin keeps an appliance from being turned on
  on a stale average just under the limit, only for one to be switched off at
  the next decision. The margin is below the limit only, so the regulation
  never accepts being above it.
- Fixed order: a step is never turned on before all above it are on. Skipped:
  entries that are not the current variant, excluded appliances, and the
  ampere steps the EV charging rules hold back: of chargers that are not
  allowed to charge, are bypassed, are waiting or are not chosen when only one
  may charge, and all but the first of a charger on trial.
- Making room: when the first step that is off and not skipped may not be
  turned on for lack of room (the average is at or above the limit minus the
  margin, or its reserve does not fit) while steps below it are on, the lowest
  of them that is not a bypassed charger's is switched off, without waiting,
  one per decision until it fits or none is left. Not at a decision where step
  6 switched off something that was on, for the same reason as in step 8. Why:
  by the fixed order the steps below cannot be turned on before it anyway, and
  they would otherwise keep the power it waits for. Steps end up on below one
  that is off after a variant switch or an appliance included again, and when
  steps below a charger on trial were turned on before it charges or is tried
  again.

## Waiting time

- When the next step may be turned on, its waiting time starts. It is turned on
  at the first decision after the waiting time has passed, if the conditions
  still hold. Waiting time 0 turns it on at the same decision. If the
  conditions fail, the waiting is cancelled and starts again later. Only the
  step that is next can wait.
- Waiting time at the limit: 0–600 s, default 300 s.
- Curve: waiting time = waiting time at the limit × share(average / limit),
  recalculated at each decision while it runs. Why: an appliance should hardly
  wait while there is plenty of free power, and wait the whole time only close
  to the limit. With u = average / limit and x = clamp((u − 0.5) / 0.5, 0, 1),
  the share is the normalized Hill function x^n · (1 + K) / (x^n + K): 0 at or
  below half the limit, slow at first, and 1 at the limit and above. n is the
  steepness, 1.5–9 in steps of 0.5, default 6. The pivot point, 50–99, default
  80, is the utilization in percent where the share is 80 %: with t = (pivot −
  50) / 50, K = t^n · 0.2 / (0.8 − t^n), computed once per start. A pivot the
  curve cannot reach at the steepness is capped silently just below t =
  0.8^(1/n); the setting keeps what the user chose. Pivot 50 gives K = 0: no
  waiting up to half the limit and the whole waiting time above it. The test
  values for the curve are in the unit tests for waiting.
- Repeated turn-on: when the same step is turned on again without any other
  step being switched in between, a counter grows. The first turn-on and the
  first turn-on again use the curve. From the second turn-on again, the
  waiting time is fixed, independent of the average: min(cap, waiting at limit
  + step × (n − 2)), where n is the count of turn-ons again. The step is a
  share of the waiting time at the limit, 0.25, 0.5, 0.75 or 1, and the cap is
  the waiting time at the limit plus a number of steps, 1–9. Both are set
  separately for appliances (default 0.5 and 4) and for ampere steps
  (default 1 and 5). With waiting time 0 at the limit, the step and the cap
  are 0, so the waiting time does not grow. Any command for another step,
  also forced ones, resets the counter.
- Known limitation, to revisit if it shows up in real use: two steps that
  alternate (A on, B on, B off, A off, A on …) reset each other's counter, so
  their waiting time never grows.

## Penalty

- Overconsumption state: starts when the tariff average is above the limit
  at a decision, with overconsumption 0 at that decision. Every regulation
  average closed after it adds (average − limit) × window. It ends when the
  overconsumption is ≤ 0 (rounding noise counts as 0), at the earliest at the
  next decision. If the tariff average is still above the limit, a new
  state starts at 0 at once.
- A penalty starts when the tariff average is above limit + threshold and
  the overconsumption is > 0. With threshold 0 it starts one decision after the
  state started. Everything is turned off at once, also chargers, with a
  turn-off command to every appliance in the configuration. Nothing is turned
  on while it lasts.
- During a penalty the overconsumption still counts net. Recovery has started
  at the first regulation average under the limit after the penalty started;
  the status shows whether it has.
- The penalty ends only when the overconsumption is paid back (then the
  regulation starts again with everything off at that decision) or by a restart
  (stop, safe state, HA start). The current variants are
  still evaluated during a penalty; a switch gives only the turn-off action of
  the new variant, since everything is off.
- The start after a penalty resets the repeated turn-on counters, so while the tariff
  average stays above limit plus threshold, an appliance that pushes the
  average over the limit cycles with the waiting time from the curve only.

## Safe state

- Entered at the first decision where the power sensor was invalid at the last
  two window closes. Every appliance and charger is turned off at once, and
  nothing is turned on. The safe state binary sensor is on.
- When a valid value comes back, the averages are known again and the
  regulation starts again with everything off at the first decision.
- A sensor that never reports after startup also leads to the safe state.

## Start and stop

- Every start turns off every appliance in the configuration, once per
  appliance even with variants, and deactivates every charger. The same holds
  wherever everything is turned off. The current variant is found at the
  first decision, so a start uses the appliance's own turn-off action, and
  stop, the safe state and a penalty use the current variant's.
- Starts: when HA has finished starting (so the appliances' integrations are
  loaded), at once after a reload of the integration, when the user starts it,
  when a penalty ends and when the power sensor is back after the safe state. The
  regulation always tries to start when HA starts and when the integration is
  reloaded (for example after an update). If the user starts or stops before
  HA has finished starting, that wins.
- After a reload, the turn-off commands wait until the previous runtime's
  actions are done.
- The user stops and starts from the panel or the regulation switch; they are
  the same function. Stopping turns everything off at once and makes no more
  decisions.
- The regulation can only start when the configuration is complete: power
  sensor chosen; every appliance has entity, turn-on and turn-off action;
  every charger has entity, activate, deactivate and
  set-current actions and actively charging, and also car connected when only
  one charger in its group may charge at a time.

## Command repeat

- An appliance or charger can change state without Kraftvakt, for example
  after a power outage on its circuit or a fault in the device. The regulation
  keeps when each appliance and charger last got a command; a start commands
  every one of them.
- When a window closes while the regulation runs, also in the safe state and
  during a penalty, each appliance and charger that has had no command for the
  command repeat interval gets the command for the state the regulation has
  set: an appliance the turn-on or turn-off action of its current variant, an
  activated charger only the set-current action with its current, and a
  deactivated charger min current and deactivate. At a decision it comes after
  the decision's commands, so what got a command at the decision is not
  repeated. It is checked at every window, not only at decisions, so a long
  regulation interval does not delay it.
- A repeat is not a switch: it leaves waiting times and repeated turn-on counters alone
  and does not count against one step per decision.
- Excluded appliances and chargers get no repeat, by the position of the
  switch when the window closes, so the user can control them by hand. They
  still get the commands the regulation sends them otherwise, such as the
  turn-off when they are excluded and at start and stop.
- Nothing is repeated while the regulation is stopped.

## Power limit entity

Automations can set the power limit with it:

- A `number` entity in whole watts with the same range as the setting, the
  same value as the power limit in the panel. A new value is saved at once
  and rounded to whole watts.
- The new limit is used from the next decision, also while running, without
  a restart. Above a lower limit, steps are switched off one per decision as
  usual. A value equal to the stored one changes nothing.

## Diagnostic entities

All with entity category diagnostic:

- Penalty active: on while a penalty period lasts.
- Penalty overconsumption (Wh): the overconsumption at the last decision, 0
  outside the overconsumption state.
- Power free: the power limit minus the last regulation average,
  negative above the limit. Unavailable without an average.
- Regulation steps on: the number of steps that are on, appliances and
  ampere steps alike. Meant for a graph of how much the regulation has
  switched on.
- Waiting time remaining (s): the time from now to the decision that turns on
  the waiting step (an appliance or a charger's next ampere), so it is the
  real time left, a whole number of decision intervals after a decision. 0
  when nothing waits. Updated at each window, decision, start and stop.
- Charging allowed by window (per charger): on while the charging window
  allows charging, that is inside the window, while the override switch is
  on, or always without a window. It does not consider the excluded switch
  or finishing.
  It follows the clock, not the decisions, so it is right also while the
  regulation is stopped, and it changes at the whole minute.
- Waiting time next turn-on (calculated) (s): the waiting time the next
  turn-on gets from the curve, for the last regulation average and the limit
  in use, without the longer waiting time on repeated turn-on. Unavailable
  without an average.

## Variants

- Each ordinary appliance may have variants, sorted, each with a non-empty
  label unique for the appliance and an expression. Same reserve as the
  appliance. A variant uses the actions of the appliance, or overrides the
  turn-on action, the turn-off action or both; an action it does not override
  is the appliance's. Every command for an appliance uses the actions of
  its current variant. Not for chargers or charger groups.
- Evaluated at each decision. When an appliance switches variant: it is off
  afterwards at the new place and comes on again the normal way. It is sent
  the turn-off action of the new variant also when it was off, since variants
  may turn it off in different ways (for example a thermostat in heat or cool
  mode). The appliance itself is the variant before the first decision after
  a start. If it was off and its new place is above the lowest step that is
  on, that lowest step is switched off to give room at once, and more room is
  made at the next decisions if needed (see Making room). Its waiting time and
  repeated turn-on counter are reset.
- Several switching at the same decision are handled one by one in the order of
  their new place, highest first, together with the appliances included again
  (see Excluded appliances). One that must go off anyway can be the one that
  gives room.

## Excluded appliances

- Excluded switch (per appliance, default off): while on, the appliance is
  never turned on. It keeps its place in the priority list, and the
  regulation passes it as if it was not there. Not for charger groups;
  chargers have their own switch.
- Read at each decision. An excluded appliance that is on is switched off.
- An appliance included again is handled like an appliance that switches
  variant: if its place is above the lowest step that is on, that lowest step
  is switched off to give room, and its waiting time and repeated turn-on counter are
  reset. An excluded appliance that switches variant gives no room.
- The switch can be used while the regulation runs, is saved at once, and
  takes effect at the next decision, for the command repeat at the next
  window close. It does not restart the regulation.

## EV charging

- Chargers are in charger groups. Each group has a name, non-empty and unique
  among the groups, its own entry in the priority list, and its own settings
  below. Every rule in this section applies within a group: a group knows
  nothing of the chargers of other groups. So two groups with one charger at a
  time may each have a charger charging at once. The waiting time on
  repeated turn-on for ampere steps is one setting for all groups.
- Every group is regulated. Without groups there is no EV charging; to keep a
  charger from charging for a while, the user excludes it.
- One charger at a time: default yes. The chargers of a group are sorted in
  its configured charging priority.
- Each charger is split into ampere steps, one per ampere from min to max
  current (whole amperes, 1 ≤ min ≤ max, default 6 and 16). Current = min +
  number on − 1. None on means deactivated. The ampere steps sit at the
  place of the entry of their group.
- First ampere step on: set current to min, then activate, and only the first has
  the charger's power reserve (0–5000 W, default 4000 W). Later ones: set the
  new current. Switching off: set the lower current, or for the last one set
  current to min and then deactivate. Every deactivation sets min current
  first. The set-current action always gets a current between min and max.
- Actively charging: read at each decision, also when deactivated, from a
  charging power sensor (above 100 W, not configurable, in W or kW), a
  boolean entity or a template, true only with evidence (see Ground rules).
  Why: a charger that has lost power or its connection reports unavailable,
  and it does not charge.
- On trial: a charger that may charge but does not charge actively gets only
  its first ampere step, so it stays at the minimum current until it
  charges actively. Meanwhile the steps after it may be turned on. Why: a
  charger that may have no car must not take more power and hold back the
  appliances below the entry of its group while it is tried. A car that starts
  slowly gets its second ampere a decision later.
- Bypassed: car connected is set and false, or not actively charging while the
  first ampere step has been on for at least two windows. Evaluated at
  each decision, ends as soon as neither holds. A bypassed charger keeps its
  first ampere step if it has one and stays activated, gets no more, is
  not switched off above the limit and does not stand in the way of others.
  When it becomes bypassed, all ampere steps but the first are switched
  off at once.
- Rest: a charger that becomes bypassed because it does not charge rests. It
  stays bypassed while it rests, also after it is deactivated, and may be
  tried again when the rest is over: 15 min the first time, then 30 min, then
  60 min each time it is tried and still does not charge. The rest ends at
  once, and the next one is the first again, when car connected is false at a
  decision (a car that is connected again is tried at once) or when the
  charger charges actively while activated. Every start begins without rests.
  Why: without a rest, two chargers with full cars would take turns being
  activated forever when only one may charge at a time, and the appliances
  below the entry of their group would never be turned on.
- Current charging priority: equal to the configured one at each start.
  Newly bypassed chargers move to the back, keeping their order, and stay there
  even after they stop being bypassed, until it is corrected: when a charger
  has all its ampere steps on, the priority is set to the configured
  order for the chargers that are not bypassed; bypassed ones stay at the back.
- Several at once: the ampere steps of all allowed, not bypassed
  chargers are interleaved: the first of each charger in current priority, then
  the second, and so on.
- One at a time: an actively charging charger that is allowed to charge and
  not bypassed may go on charging, whatever the priority; others that want to
  charge are waiting. If several are actively charging, the activated one
  wins, otherwise the first in current priority. When none charges, the first
  allowed and not bypassed in current priority gets ampere steps. Before
  a charger is activated, any other activated charger is deactivated at the
  same decision (never more than one activated).
- A charger charges only when the regulation has activated it, so a car that is
  connected to a deactivated charger never starts by itself.
- Allowed to charge: not excluded, and no charging window, inside it, with
  an active override, or finishing. A charger that is not allowed has all
  ampere steps switched off at once and is deactivated at the first
  decision.
- Finishing (per charger setting finish after window, default off): outside
  the window, without an active override, a charger may go on while it is
  activated, actively charging, not excluded and car connected is not false.
  It is regulated as inside the window, so it may get and lose amperes. The
  first decision where one of these does not hold ends it, and a deactivation
  for any reason (the limit taking its last ampere, a stop, safe state,
  penalty, a start) ends it too, since a deactivated charger is never allowed
  outside the window. A charger on trial at the end of the window is not
  actively charging, so it is deactivated. The setting is configuration, but
  also a switch that may be changed while the regulation runs; it applies from
  the next decision without a restart.
- Excluded switch (per charger, default off): while on, the charger never
  charges.
- Override switch (per charger, default off): allows charging outside the
  charging window. It ends at the first decision after a charging window has
  started after the switch was turned on, also when the regulation was stopped
  or in the safe state meanwhile, and the switch is then set back to off. The
  switch-on time is kept only in memory; after a restart of HA or the
  integration the first start of the regulation counts instead. No effect for
  a charger without charging window. Switching it off stops charging outside
  the window like the window ending.
- Both switches can be used while the regulation runs, are saved at once, and
  take effect at the next decision; the excluded switch takes effect for the
  command repeat at the next window close. They do not restart the
  regulation.
