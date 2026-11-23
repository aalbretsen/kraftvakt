---
name: kraftvakt-regulation
description: How Kraftvakt's regulation must behave - concepts, measurement and averages, decisions, waiting times, penalty, safe state, start and stop, variants,
  excluded appliances and EV charging.
  Use before changing or reviewing anything in regulation/, measurement.py, power_measurement.py, decision_clock.py, decision_input.py, runtime.py or settings.py,
  or when a question is about what the regulation should do.
---

# Kraftvakt regulation

Kraftvakt is a Home Assistant integration for the Norwegian capacity tariff.
The grid company sets the capacity part of the grid fee from the hours of the month with the highest consumption.
Kraftvakt keeps the average consumption over the last hour just below a power limit chosen by the user, by turning appliances that can wait on and off in priority order.
Everything runs locally.

This file is the specification. When a rule here is unclear, ask the owner instead of deciding.
The ranges and defaults below are part of the specification; the code holds them in one place (`config_model.py`).

## Concepts

| Term | Meaning |
|---|---|
| Power limit | The highest allowed average power, 1000–50 000 W, default 10 000 W. The target the regulation keeps just below. |
| Power sensor | A sensor from another integration with the house's total momentary power, in W or kW. A sensor without unit is read as W. Other units, non-numbers, `unknown` and `unavailable` are invalid. Negative values count as 0 W. |
| Update | A report of the power sensor, of a changed or an unchanged value, valid or not. A HAN reader reports at a fixed interval, 2–10 s depending on the meter. |
| Update interval | How often the power sensor reports, measured when it is chosen: from the recorder's history of its changes when they are regular, else by listening to its updates for up to 30 s. Stored with the configuration. It gives a regulation window its shortest length, and tells when the power sensor no longer reports as when it was chosen (see Measurement). |
| Regulation window | A number of updates of the power sensor, closed at the update that completes it, once it has lasted three quarters of its length at the update interval. Chosen as the multiples of the fewest updates that last at least 10 s, at most 6 choices, for at most 60 s at the update interval. No default, since it depends on the power sensor. Why: a window that follows the meter holds whole measurements, so with a meter that reports every 10 s the regulation average of a 10 s window is the newest measurement, not a mix of the last two. Why the shortest length: a meter may send an extra report, as a Kamstrup meter sends its hourly list a few seconds after a report, and that must not close a window that has only just started. |
| Regulation average | Time-weighted average of the power sensor over one regulation window. Drives all decisions. |
| Tariff window | One hour back from now, sliding, not configurable. |
| Tariff average | Time-weighted average of the power sensor over the tariff window. The regulation uses it only for the penalty. Why sliding: the grid company measures each clock hour, and every clock hour is one of the sliding hours; a sliding hour also finds overconsumption early, where a budget per clock hour could be used up in the middle of the hour and leave no power for the rest of it. |
| Decision | What the regulation decides at each interval. All evaluation and all switching happens at decisions. The command repeat sends commands also between decisions, but only for the state the regulation has already set. |
| Command repeat interval | 10–60 min, default 30 min. How long an appliance or charger may go without a command before the command for its state is sent again. |
| Action timeout | 10–300 s, default 60 s. How long an action may run before it is stopped and counts as failed. Why: the actions run one at a time, so one that never finishes would hold back every later command, also the turn-offs, and a longer maximum would hold them back too long. |
| Power sensor timeout | 10–3600 s, default 300 s. How long the power sensor may go without reporting, also an unchanged value, before it counts as invalid. Why: a HAN reader that loses its connection may keep its last value. |
| Free power | Power limit minus regulation average. |
| Turn-on margin | How far below the limit the regulation average must be before anything is turned on, 1–1000 W, default 100 W. 0 is not allowed. |
| Power reserve | Free power a step needs before it may be turned on. For an appliance an optional setting, ≥ 0 W, no upper limit, only for an appliance with a fixed load, as a ceiling fan: one with a thermostat or other control of its own draws less than its reserve most of the time, so the reserve only holds it back. For the first ampere step of a charger, its power at minimum current, and for the others its power per ampere. A step with a power reserve does not wait the first time it is turned on (see Waiting time). |
| Power at minimum current | A charger setting, 1000–5000 W, default 4157 W, what 6 A draws on three phases at 400 V: what the car and charger draw at the minimum current, as about 1400 W for a car that charges on one phase. The power reserve of the charger's first ampere step, the base of held at minimum, and its power per ampere until that is measured. |
| Power per ampere | What a charger draws per ampere: its charging power divided by its current, measured at each decision where it is activated and actively charging with a valid charging power above 0 W, and kept until it is measured again. Before that, its power at minimum current divided by its minimum current. Why: it fits any charger and car, on one phase or three. |
| Settling step | A step with a power reserve turned on since the start of the regulation window of the decision. It holds its power reserve, since that window's average shows it only in part. |
| Held power reserve | The power reserve of a settling step, counted as used by the steps below it and the other steps of its group. |
| Power to free | How far the regulation average must drop before the next step may be turned on: below the limit by the turn-on margin, and with room for its power reserve, with the held power reserves counted as used. Found at each decision and shown on the status page. |
| Waiting time | Time that must pass before a step is turned on: an appliance without a power reserve, and a fixed-load appliance that is turned on again, while no step below it that may be switched off for room is on, and the first ampere step of a charger that is turned on again. |
| Waiting time for EV chargers | 1–5, default 2. How many times the waiting time at the limit the first ampere step of a charger waits, for the curve and the growth on repeated turn-on alike. |
| Waiting time curve | The share of the waiting time at the limit, by how close the regulation average is to the limit. Set with steepness and pivot point. |
| Appliance | An entity Kraftvakt turns on and off with configurable actions. |
| Essential appliance | An appliance that is kept on, and turned off only in a penalty period, for an appliance that must always run, as a freezer. No step, no variants. |
| Display value | An optional power and temperature of an appliance, from a sensor or a template, only shown on the status page. The regulation never reads them. |
| Priority list | Sorted list of appliances, their variants and an entry per charger group. Top is highest priority, turned off last. The essential appliances are above every other entry. |
| Variant | Extra entry for an appliance with a label and a true/false expression, giving it another place in the list, and optionally its own actions. |
| Current variant | The variant of the topmost true expression, or the appliance itself when none is true. Only this entry takes part. |
| Step | An entry the regulation switches: the current variant of an appliance that is not essential, or an ampere step. |
| Safe state | Everything off and nothing turned on, because there is no valid power measurement. |
| Penalty threshold | 0–10 000 W above the power limit, default 100 W. |
| Overconsumption | Net energy above the power limit since the overconsumption state started (above adds, below subtracts). |
| Penalty period | Safety valve: everything held off until the overconsumption is paid back. Should never be needed. |
| Switched by | A charger setting: how it is activated and deactivated. By its on/off entity (the default), by custom actions to activate and deactivate, or by current, for a charger that can only be told a current: its minimum current activates it, and 0 A deactivates it. |
| On/off entity | The entity, usually a switch that allows charging, that a charger switched by it gets turned on to activate it and off to deactivate it. |
| Cloud-controlled charger | A charger setting, off by default, for a charger controlled through a cloud service: no command repeat while no car is connected. |
| Start delay | A charger setting, 0–900 s. How long the car may take from activation until it draws power, and so how long a charger is starting. Filled in from the charger profile of its device, or from the default profile, 180 s, for a charger without one. |
| Ampere damping time | 60–1800 s, default 300 s. How long an ampere step above the first taken back for power waits before it is turned on again, counted from when it was taken back. Why: consumption that changes for short moments would otherwise move a charger up and down between the same two amperes at every decision. |
| Damped ampere step | An ampere step above the first taken back for power, by Freeing power above the limit or to make room for a step higher up, within the ampere damping time since. |
| Starting charger | An activated charger within its start delay since activation. Nothing after its first ampere step is turned on but its own ampere steps (see EV charging). |
| Deactivate on fault | A charger setting, off by default, with its fault flag: the charger has a fault while it shows one. |
| Fault flag | A condition of the charger that tells that it has a fault. |
| Charger with a fault | A charger whose fault flag showed a fault at the last decision, with deactivate on fault on. It behaves as a deactivated charger, not allowed to charge. |
| Charger profile | How Kraftvakt controls the chargers of a known integration: the entities, actions and conditions it fills in when the user chooses a charger's device. |
| Charger group | A named group of chargers with its own entry in the priority list and its own EV charging settings. A charger is in exactly one group. |
| Ampere step | One ampere of an EV charger's current, treated by the regulation as an appliance. |
| Car charging | An optional condition of the charger that is true while the car charges. |
| Charging power | A power sensor of the charger, in W or kW, or a template giving the charger's power in W. Above 100 W counts as actively charging. Every charger has one. |
| Actively charging | The car draws power: the charging power or car charging shows it, and either is enough. |
| Held at minimum | A charger whose car does not charge actively with at least 50 % of the charger's power at minimum current, or 90 % while it is starting. It gets no more than its first ampere step. |
| Estimated draw | What a charger draws with fewer ampere steps on: its charging power, at most its current times its power per ampere, and 0 deactivated. |
| Freeing power | Switching off steps from the lowest until their estimated draw covers the power needed, at once. |
| Bypassed charger | A charger without a car connected, which must not stand in the way of others. |
| Dynamic charging order | A group setting, off by default. On, a charger that charges keeps its place ahead of the chargers that do not charge. Off, the configured charging priority always applies. |
| Queued charger | A charger that is allowed to charge and has a car, but waits for its turn: with one charger at a time after the one that charges, and with several at once and dynamic charging order behind the activated chargers. |
| Switch-over | With several at once and dynamic charging order: the chargers that charge are set to their minimum current at once to make room for a queued charger. |
| Charging window | Optional daily time span in whole minutes, in HA's time zone, may span midnight, start ≠ end. |
| Allowed to charge | A charger without a fault that is not excluded, and has no charging window, is inside it, has an active window override, or charges until disconnected. |
| Window override | A charger's switch that allows charging outside its charging window, until it is switched off or its override end ends it. |
| Override end | What switches a window override off besides the user: manual, when the car no longer charges, or when the car is disconnected. |
| Armed override | A window override where what ends it has started since it was switched on: the car charging or connected. Only an armed override ends. |
| Charged in window | A charger that was activated and actively charging at a decision inside its charging window, since its car was last disconnected. |
| Charging until disconnected | A charger charged in window, with charge until disconnected, allowed to charge outside its window until its car is disconnected. |

Resolution of settings: power in whole watts, the waiting time at the limit in whole seconds, the update interval in tenths of a second, currents in whole amperes.
Power is in W everywhere inside the regulation, the configuration and the entities, energy in Wh; the status page shows kW.

## Ground rules

- Kraftvakt only decides whether an appliance may be on. It never estimates what an appliance uses from changes in the total consumption.
- It does not read or react to the state of appliances. It assumes each one is as Kraftvakt last told it, and repeats that command now and then (see Command repeat).
  Switching appliances outside Kraftvakt can disturb the regulation. Exception: for chargers it reads actively charging and car connected.
- A failed action, also one stopped by the action timeout, is logged and not retried. The regulation goes on as if it worked.
  The command repeat sends the command for the state again later.
- Commands that wait for an action that has not finished are merged with newer ones, as the commands of one decision are (see Decisions).
  Why: a slow action, as with a cloud service that is down, must not be followed by a burst of outdated commands that switch a device on and off.
- Only the current configuration is regulated. Kraftvakt never hands an appliance or charger back: removed, excluded, with the regulation stopped or the integration removed,
  it stays as last commanded, and the user sets it as wanted.
- The configuration can only be changed while the regulation is stopped, except the user's switches (one per appliance, two per charger),
  charge until disconnected (see EV charging) and the power limit (see Power limit entity).
  Everything is off while stopped, so removed appliances are already off and new ones are controlled from the next start.
- The state of the regulation (on/off, waiting times, repeated turn-on counters, settling steps, damped ampere steps, overconsumption, penalty, current charging priority,
  bypassed chargers, measured power per ampere, current variants, excluded appliances, when each appliance and charger last got a command)
  starts again with defaults at every start: HA or integration start, user start, after the safe state and after a penalty.
  The configuration and the switch positions are kept over any restart.
- True/false from HA is a condition: a boolean entity or a template, and for the conditions of a charger (car connected, car charging and the fault flag)
  also the states of an entity. The chosen states count as true, or, when the user chooses so, as false, and every other state as the opposite.
  The charging power is a power sensor or a template that gives a number.
  Only evidence makes it true: an entity that is `on`, a state that counts as true, a template that gives the boolean true, or a valid power above 100 W.
  Everything else is false, also unavailable entities and sensors, `unknown` and `unavailable` of an entity with states, and failing templates.
  The exceptions are the override end, the end of charged in window, and the deactivation of a charger whose car is disconnected with dynamic charging order (see EV charging),
  which need evidence of false.
  Settings are named so that true means the thing is the case.

## Measurement

- The first window starts when the integration starts, and each next window where the one before closed, also while the regulation is stopped.
  A window closes at the update that completes its number of updates, once it has lasted three quarters of its length at the update interval,
  so a missing update makes it longer, and an extra report counts in the window without closing it early.
  Each regulation average covers its own window, without overlap. The regulation knows only the averages and the length of each window.
- While the power sensor is invalid, because its last update was invalid or it has not reported for the power sensor timeout,
  a window also closes when it has lasted its length at the update interval, so the safe state comes without updates.
- Averages are energy divided by time, correct for any update rate of the sensor. Each update covers the time since the update before it,
  or since the last window close if that is later, and the latest also the time after it until the next. So a closed window never changes.
- At startup (HA or integration start) the hour before is taken from HA's recorder history of the power sensor,
  read like live values (an invalid value keeps the last valid one in place, and the oldest valid value fills the time before it),
  except that each value holds until the next, since the recorder keeps only changes.
  The time HA was down counts with the last value recorded before it stopped. Without a recorder or any valid history, the missing past is filled with the first measured value.
  The regulation window is not affected: the first one starts at startup.
  Why: everything is turned off at start, so the first value after a restart is only the background and cannot stand for the hour before.
- Validity is the state when a window closes. A power sensor that has not reported for the power sensor timeout is invalid.
  A gap inside a window is filled with the last valid value, and the update after it covers the time since the gap started or the last close.
- One window closing without a valid value is tolerated (the last valid value is used).
  Two in a row make the averages unknown: the average sensors become unavailable until a valid value comes, also while the regulation is stopped.
  The history is kept, and the gap counts with the last valid value before it, like the time HA was down.
  Why: the first value after the gap is only the background (everything is off in the safe state) or a short peak while the appliances are turned off,
  so it cannot stand for the time before.
- Before the first valid value there is no average. Windows without any measurement count as invalid.
- A window that would close by the clock a whole window length or more after its time, or a power sensor timeout noticed that late, is missed,
  as when HA's event loop was paused (a host that sleeps, a paused virtual machine, a blocked loop).
  Windows closed by the clock that have ended are skipped, and the window running when it is noticed closes next, in the same cadence;
  after a late timeout, the next window starts when it is noticed and the timeout starts again, since the updates could not be received.
  Skipped windows make no decision and no command repeat.
  The time missed counts with the last valid value, like the time HA was down, but not in the overconsumption, which counts closed windows only.
  Waiting times, the start delay and the command repeat count it as time that has passed.
  A warning is logged. Why: closing the missed windows one by one would replay their decisions at once, by the old clock.
- Changed update interval: a window closed by an update is off when its length divided by its updates is more than a quarter off the update interval,
  in either direction. Five windows off in a row are reported as a repair issue, with a warning in the log, and the regulation goes on.
  Five windows in a row that are not off remove it. A window closed by the clock, or skipped, breaks the row.
  The check starts again when another power sensor, update interval or number of updates is saved, and the issue is removed then and when the integration stops.
  Why: the windows rely on the update interval, which changes when the HAN reader is set up anew or replaced.
  A power sensor that reports only partly regularly is reported too, since its windows do not last as chosen.
- Saving a configuration does not restart the averages. A new power sensor is followed from the save, a new number of updates applies from the next window.

## Decisions

- A decision is made each time a window that started at or after the start of the regulation closes.
  A window that started before the start does not count, so the first decision comes after one or two windows. The decision time is the end of the window.
- Order inside a decision, each step may end it:
  1. Safe state.
  2. Window overrides that end are switched off (see Override end).
  3. Overconsumption.
  4. Penalty.
  5. EV chargers: allowed, bypassed, charging, held at minimum, current priority, queued.
  6. Forced switch-offs: chargers not allowed to charge, chargers whose car is known to have left with dynamic charging order,
     and with one charger at a time the chargers after the one that charges (all ampere steps off and deactivate),
     newly bypassed chargers and chargers held at minimum down to one ampere step, excluded appliances, appliances that switch variant or are included again.
     Essential appliances that are included again are turned on here (see Essential appliances).
  7. Build the ordered steps (current variants, ampere steps in place of the entry of their group).
  8. Above the limit: free the power above the limit (see Freeing power), without waiting, and cancel any waiting.
     When step 6 switched off something that was on, nothing more is switched off; the waiting is still cancelled and nothing is turned on.
     Why: the average was measured before the forced switch-off, so switching off one more would often be too much.
  9. Turn on: a switch-over when one may be made (see EV charging), or else the first step that is off and not skipped.
     Without room for it, room is made below it instead (see Making room). A damped ampere step waits instead,
     and so does a step after the first ampere step of a starting charger that is not one of its own (see EV charging).
- An appliance gets at most one command per decision, the last one. Turned off and on again at the same decision, it only gets the turn-on.
  Why: switching a device off and on at once wears its relays, for example in a thermostat.
  A charger gets only its last activation or deactivation, with the current set before it, and its last current after it.
- Only one step is turned on or off per decision based on free power.
  Several may be switched off at once only when consumption must drop at once or switching does not change consumption: start and stop, safe state, penalty,
  chargers not allowed to charge, bypassed chargers and chargers held at minimum, excluded appliances, variant switches, appliances included again,
  the chargers after the one that charges with one charger at a time, a switch-over, and freeing power above the limit or to make room.
- Turn on only when the regulation average is under the limit minus the turn-on margin, and average plus power reserve is at most the limit.
  The held power reserves above the step, and in the step's own group, count as used:
  they are added to the average in both and in its waiting time (see EV charging).
  Why a settling step holds its reserve: the window after a decision still holds the consumption from before its commands,
  so without it the next step would be turned on as if the step before drew nothing.
  Switch off only when the average is above the limit, or to make room. Between limit minus margin and the limit, both included, nothing is turned on,
  and nothing is switched off except to make room. Why: commands run just after a window closes, and a real meter reports the change only at its next update,
  so the window after a decision still holds the consumption from before its commands. The margin keeps an appliance from being turned on on a stale average just under the limit,
  only for one to be switched off at the next decision. The margin is below the limit only, so the regulation never accepts being above it.
- Fixed order: a step is never turned on before all above it are on.
  Skipped: entries that are not the current variant, excluded appliances, and the ampere steps the EV charging rules hold back: of chargers that are not allowed to charge,
  are bypassed or are queued with one charger at a time, and all but the first of a charger held at minimum.
- Making room: when the first step that is off and not skipped may not be turned on for lack of room (the average is at or above the limit minus the margin,
  or its reserve does not fit) while steps below it are on, the steps below it free the power it needs to fit: the average down to the limit minus the margin,
  and its reserve below the limit (see Freeing power), with the held power reserves counted as used.
  Not at a decision where step 6 switched off something that was on, for the same reason as in step 8.
  Why: by the fixed order the steps below cannot be turned on before it anyway, and they would otherwise keep the power it waits for.
  Steps end up on below one that is off after a variant switch or an appliance included again,
  and when a charger higher up gets a car, or its car draws power again and so may get more than its minimum current.
- Freeing power: the steps that are on are switched off from the lowest, at once, until the power they are estimated to free covers what is needed.
  The ampere steps of a bypassed charger, and of a charger whose car does not charge actively, are passed, since switching them off frees nothing.
  Only what a charger draws is known, from its charging power (see Estimated draw), so an appliance ends it, and is switched off only when it is the first.
  At least one step is switched off. Why: a car may suddenly draw more than the regulation let it count on, as one that starts heating in the morning,
  or one that did not use the current it had and suddenly does, and one ampere per decision would take minutes to bring the average back under the limit.

## Waiting time

- A step with a power reserve does not wait the first time it is turned on: it is turned on at the first decision where it fits.
  Turned on again (see Repeated turn-on), a fixed-load appliance and the first ampere step of a charger wait as any appliance,
  the first ampere step with the waiting time at the limit times the waiting time for EV chargers, and both count their own power reserve in the curve.
  An ampere step above the first never waits; it is damped instead (see EV charging).
  Why: the reserve tells whether it fits, and the waiting time is for an appliance whose draw is unknown.
  But one that is switched on and off again and again wears its relays, and a charger also those of the car: better not charged than switched on and off.
  Its own reserve makes it wait by how close it would bring the average to the limit, so one switched off just above the limit is not turned on again at the next decision,
  when the average without it is far below.
- Nor does an appliance with steps on below it that may be switched off for room (see Making room), as after a variant switch:
  it is turned on at the first decision where the average is under the limit minus the turn-on margin.
  Why: by the fixed order nothing below it can be turned on while it waits, so waiting changes nothing,
  and if it takes the average above the limit, the steps below give way by Freeing power.
  The first ampere step of a charger that is turned on again waits also then. Why: its waiting protects the relays, whatever is on below,
  and a charger deactivated at a decision where a step below it is turned on, as by a short fault, would otherwise be activated again at the next.
- When the next step may be turned on and it waits, its waiting time starts.
  It is turned on at the first decision after the waiting time has passed, if the conditions still hold.
  Waiting time 0 turns it on at the same decision. If the conditions fail, the waiting is cancelled and starts again later.
  Only the step that is next can wait, and a queued charger before a switch-over (see EV charging).
- Waiting time at the limit: 0–600 s, default 300 s.
- Every waiting time is rounded to whole seconds, half up, so one under half a second is none.
  Why: just above half the limit the curve gives a few milliseconds, which would otherwise hold the turn-on back a whole window.
- Curve: waiting time = waiting time at the limit × share(average / limit), recalculated at each decision while it runs.
  The average includes the held power reserves above the step and in its own group, and for a step with a power reserve that is turned on again, its own reserve.
  Why: an appliance should hardly wait while there is plenty of free power, and wait the whole time only close to the limit.
  With u = average / limit and x = clamp((u − 0.5) / 0.5, 0, 1), the share is the normalized Hill function x^n · (1 + K) / (x^n + K):
  0 at or below half the limit, slow at first, and 1 at the limit and above.
  n is the steepness, 1.5–9 in steps of 0.5, default 6.
  The pivot point, 50–99, default 80, is the utilization in percent where the share is 80 %:
  with t = (pivot − 50) / 50, K = t^n · 0.2 / (0.8 − t^n), computed once per start.
  A pivot the curve cannot reach at the steepness is capped silently just below t = 0.8^(1/n); the setting keeps what the user chose.
  Pivot 50 gives K = 0: no waiting up to half the limit and the whole waiting time above it. The test values for the curve are in the unit tests for waiting.
- Repeated turn-on: when the same step is turned on again without any other step being switched in between, a counter grows.
  The first turn-on and the first turn-on again use the curve. From the second turn-on again, the waiting time is fixed, independent of the average: min(cap, waiting at limit
  + step × (n − 2)), where n is the count of turn-ons again. The step is a share of the waiting time at the limit, 0.25, 0.5, 0.75 or 1,
    and the cap is the waiting time at the limit plus a number of steps, 1–9, default 0.5 and 4.
    With waiting time 0 at the limit, the step and the cap are 0, so the waiting time does not grow. Any command for another step, also forced ones, resets the counter.
- A charger is one unit for repeated turn-on, with a counter of its own: activated after it has been deactivated, it is turned on again,
  whatever was switched in between, its own ampere steps above the first included.
  It is forgotten when the charger has stayed activated or deactivated for longer than the cap for chargers,
  and when car connected gives evidence that the car is disconnected, so a car connected again is activated as the first time.
  A command for a charger still resets the counter of an appliance.
  Why: switching a charger on and off wears the relays of the charger and the car, and a change of its current does not.
  A charger that stayed as it was for longer than the longest it can wait, or whose car left, was not switched on and off.
- Known limitation, to revisit if it shows up in real use: two steps that alternate (A on, B on, B off, A off, A on …) reset each other's counter,
  so their waiting time never grows.

## Penalty

- Overconsumption state: starts when the tariff average is above the limit at a decision, with overconsumption 0 at that decision.
  Every regulation average closed after it adds (average − limit) × the length of its window. It ends when the overconsumption is ≤ 0 (rounding noise counts as 0),
  at the earliest at the next decision. If the tariff average is still above the limit, a new state starts at 0 at once,
  except when a penalty ends: the regulation then starts again with defaults, and the state starts at the next decision where the tariff average is above the limit.
- A penalty starts when the tariff average is above limit + threshold and the overconsumption is > 0. With threshold 0 it starts one decision after the state started.
  Everything is turned off at once, also chargers, with a turn-off command to every appliance in the configuration. Nothing is turned on while it lasts.
- During a penalty the overconsumption still counts net.
  Recovery has started at the first regulation average under the limit after the penalty started; the status shows whether it has.
- The penalty ends only when the overconsumption is paid back (then the regulation starts again with everything off at that decision) or by a restart (stop, safe state, HA start).
  The current variants are still evaluated during a penalty; a switch gives only the turn-off action of the new variant, since everything is off.
- The start after a penalty resets the repeated turn-on counters, so while the tariff average stays above limit plus threshold,
  an appliance that pushes the average over the limit cycles with the waiting time from the curve only.

## Safe state

- Entered at the first decision where the power sensor was invalid at the last two window closes. Every appliance and charger is turned off at once, and nothing is turned on,
  except the essential appliances that are not excluded, which are turned on (see Essential appliances).
  The safe state binary sensor is on.
- When a valid value comes back, the averages are known again and the regulation starts again with everything off at the first decision.
- A sensor that never reports after startup also leads to the safe state.

## Start and stop

- Every start turns off every appliance in the configuration, once per appliance even with variants, and deactivates every charger.
  The same holds wherever everything is turned off. The essential appliances that are not excluded are turned on instead, except in a penalty.
  The current variant is found at the first decision, so a start uses the appliance's own turn-off action, and stop, the safe state and a penalty use the current variant's.
- Starts: when HA has finished starting (so the appliances' integrations are loaded), at once after a reload of the integration, when the user starts it,
  when a penalty ends and when the power sensor is back after the safe state.
  The regulation always tries to start when HA starts and when the integration is reloaded (for example after an update).
  If the user starts or stops before HA has finished starting, that wins.
- After a reload, the turn-off commands wait until the previous runtime's actions are done.
- The user stops and starts from the panel or the regulation switch; they are the same function. Stopping turns everything off at once and makes no more decisions.
  Excluded appliances are read from the switches at a start and a stop.
- The regulation can only start when the configuration is complete: power sensor chosen; every appliance has entity, turn-on and turn-off action; every charger has entity,
  activate, deactivate and set-current actions, car connected, a charging power, and with deactivate on fault a fault flag.

## Command repeat

- An appliance or charger can change state without Kraftvakt, for example after a power outage on its circuit or a fault in the device.
  The regulation keeps when each appliance and charger last got a command; a start commands every one of them.
- When a window closes while the regulation runs, also in the safe state and during a penalty,
  each appliance and charger that has had no command for the command repeat interval gets the command for the state the regulation has set:
  an appliance the turn-on or turn-off action of its current variant, an activated charger only the set-current action with its current,
  and a deactivated charger min current and deactivate. At a decision it comes after the decision's commands, so what got a command at the decision is not repeated.
  It is checked at every window close, also one that makes no decision.
  An activated charger is not activated again. Why: activating again may start a new charging session in the charger and reset its measurements.
  A charger that has lost its activation does not charge actively, and is handled as any charger that does not charge.
- A repeat is not a switch: it leaves waiting times and repeated turn-on counters alone and does not count against one step per decision.
- Excluded appliances and chargers get no repeat, by the position of the switch when the window closes, so the user can control them by hand.
- A cloud-controlled charger gets no repeat while car connected gives evidence, when the window closes, that no car is connected, activated or deactivated.
  Why: a charger controlled through a cloud service sends every command over the internet, also an unchanged one.
  They still get the commands the regulation sends them otherwise, such as the turn-off when they are excluded and at start and stop.
- Nothing is repeated while the regulation is stopped.

## Power limit entity

Automations can set the power limit with it:

- A `number` entity in whole watts with the same range as the setting, the same value as the power limit in the panel. A new value is saved at once and rounded to whole watts.
- The new limit is used from the next decision, also while running, without a restart. Above a lower limit, steps are switched off one per decision as usual.
  A value equal to the stored one changes nothing.

## Status entities

Penalty active, penalty overconsumption, power free and the state of each charger have no entity category, so they show as sensors; the others have entity category diagnostic.

- Penalty active: on while a penalty period lasts.
- Penalty overconsumption (Wh): the overconsumption at the last decision, 0 outside the overconsumption state.
- Power free: the power limit minus the last regulation average, negative above the limit. Unavailable without an average.
- Regulation steps on: the number of steps that are on, appliances and ampere steps alike, without the essential appliances.
  Meant for a graph of how much the regulation has switched on.
- Waiting time remaining (s): the time from now to the decision expected to turn on the step that waits, an appliance or an ampere step,
  or to the decision that ends the start delay or the ampere damping holding back the next step,
  with the windows lasting their length at the update interval, a whole number of window lengths after a decision. 0 when nothing waits.
  Updated at each window, decision, start and stop, and when missed windows are skipped.
- Allowed to charge (per charger): on while the charger is allowed to charge (see EV charging), with the switches and charge until disconnected as they are now.
  The charging window follows the clock, so it is right also while the regulation is stopped and changes at the whole minute.
  Charged in window and a fault are as the last decision found them,
  so the sensor stays on without a break when the window ends with a charger that charges until disconnected, and goes off at the decision that finds the car disconnected.
- State (per charger): the charger's state as on the status page, stopped while the regulation is stopped,
  with an icon and a colour that templates can read, for a dashboard.
- Waiting time next turn-on (calculated) (s): the waiting time an appliance without a power reserve gets from the curve, for the last regulation average and the limit in use,
  without the longer waiting time on repeated turn-on, the held power reserves, or the longer waiting time for EV chargers. Unavailable without an average.

## Variants

- Each ordinary appliance that is not essential may have variants, sorted, each with a non-empty label unique for the appliance and an expression. Same reserve as the appliance.
  A variant uses the actions of the appliance, or overrides the turn-on action, the turn-off action or both; an action it does not override is the appliance's.
  Every command for an appliance uses the actions of its current variant. Not for chargers or charger groups.
- Evaluated at each decision. When an appliance switches variant: it is off afterwards at the new place and comes on again the normal way.
  It is sent the turn-off action of the new variant also when it was off, since variants may turn it off in different ways (for example a thermostat in heat or cool mode).
  The appliance itself is the variant before the first decision after a start. If it was off and its new place is above a step that is on,
  the lowest step below it that may be switched off for room is switched off to give room at once, and more room is made at the next decisions if needed (see Making room).
  As in Freeing power, a bypassed charger and a charger whose car does not charge actively are passed, since switching them off frees nothing.
  Its waiting time and repeated turn-on counter are reset.
- Several switching at the same decision are handled one by one in the order of their new place, highest first,
  together with the appliances included again (see Excluded appliances). One that must go off anyway can be the one that gives room.

## Excluded appliances

- Excluded switch (per appliance, default off): while on, the appliance is never turned on.
  It keeps its place in the priority list, and the regulation passes it as if it was not there. Not for charger groups; chargers have their own switch.
- Read at each decision. An excluded appliance that is on is switched off.
- An appliance included again is handled like an appliance that switches variant: if its place is above a step that is on, the lowest step below it
  that may be switched off for room is switched off to give room,
  and its waiting time and repeated turn-on counter are reset. An excluded appliance that switches variant gives no room.
- The switch can be used while the regulation runs, is saved at once, and takes effect at the next decision, for the command repeat at the next window close.
  It does not restart the regulation.

## Essential appliances

- An appliance marked essential is kept on: every start turns it on, and so do a stop and the safe state, so a stop during a penalty does not leave it off.
  A penalty turns it off with everything else, and the start when the penalty ends turns it on again. Nothing else turns it off.
  Why: it is in the regulation only so that a penalty can turn it off.
- It is no step. It never waits, is never switched off above the limit or to make room, does not count against one step per decision,
  and its commands leave the waiting time and the repeated turn-on counters alone.
- An excluded essential appliance is turned off at the next decision, as any excluded appliance, and counts as a forced switch-off.
  Included again, it is turned on at once at the next decision, unless a penalty lasts. A start or stop with it excluded turns it off.
- It gets the command repeat for its state, as any appliance.
- It has no variants and no power reserve, and its entries sit above every other entry in the priority list; the backend refuses a configuration where it does not.

## EV charging

- Chargers are in charger groups. Each group has a name, non-empty and unique among the groups, its own entry in the priority list, and its own settings below.
  Every rule in this section applies within a group: a group knows nothing of the chargers of other groups.
  So two groups with one charger at a time may each have a charger charging at once.
- Every group is regulated. Without groups there is no EV charging; to keep a charger from charging for a while, the user excludes it.
- One charger at a time: default yes. The chargers of a group are sorted in its configured charging priority.
- Each charger is split into ampere steps, one per ampere from min to max current (whole amperes, 1 ≤ min ≤ max, default 6 and 16). Current = min + number on − 1.
  None on means deactivated. The ampere steps sit at the place of the entry of their group.
- First ampere step on: set current to min, then activate. Its power reserve is the charger's power at minimum current.
  Later ones: set the new current. Their power reserve is the charger's power per ampere.
  Switching off: set the lower current, or for the last one set current to min and then deactivate. Every deactivation sets min current first.
  The set-current action always gets a current between min and max, except 0 A for a charger switched by its current.
- Ampere damping: every ampere step above the first taken back for power, also several at once, is damped from then.
  The first, which deactivates the charger, waits its waiting time instead when it is activated again (see Waiting time).
  A damped ampere step that is next waits as an appliance with a waiting time does: nothing below it is turned on and no room is made for it.
  When its damping time has passed, it is turned on at the first decision where it fits.
  Ampere steps that the EV charging rules switch off are not damped: held at minimum, bypassed, not allowed, the chargers after the one that charges, and a switch-over.
  So a raise without a take-back before it, as when a charger ramps up or its car draws power again, never waits.
- Switched by (per charger setting, default its on/off entity): activating turns the on/off entity on or runs the action to activate, and deactivating the opposite.
  By current, for a charger that can only be told a current, it gets only the current: its minimum to activate it, and 0 A to deactivate it, one command each.
  The on/off entity and the actions of the ways it is not switched are kept, and neither used nor needed.
- Car connected: required for every charger, read at each decision, true only with evidence (see Ground rules).
  Why: without it, a car could only be found by activating the charger, and chargers without a car would be activated in turn.
- Actively charging: read at each decision, also when deactivated, from the charging power and car charging, true when either gives evidence (see Ground rules).
  Every charger has a charging power; car charging is optional. Evidence that it does not charge needs each of them that is given to show it.
  Why: car charging often reports a car that starts sooner than the power, and a charger that has lost power or its connection reports unavailable, and does not charge.
- A charger that charges is activated and charges actively. Kraftvakt never guesses that a car is done: a car that is full stays activated at its minimum current,
  and may draw power again at any time, as when it heats before a trip, or the user raises its charging limit.
- Held at minimum: a charger whose car does not charge actively with at least 50 % of its power at minimum current, or 90 % while it is starting,
  gets only its first ampere step, and one that has more is set back to its minimum current at once.
  Once its start delay has passed, the steps after it may be turned on meanwhile, so a car that is full does not hold back the appliances below.
  Why: a car may start drawing power at any time, and at its minimum current it can only take about its power at minimum current, which a fast reaction can free.
  So a car that draws little or nothing, as one that is full, is not given more.
  The regulation relies on the user setting the power at minimum current to match the car and charger.
- Starting: every activated charger is starting for its whole start delay since activation, whether its car draws power or not.
  While it is starting, nothing after its first ampere step is turned on but its own ampere steps: neither the steps below its group
  nor the ampere steps of the other chargers in its group after it, and no room is made for them. The steps above it are turned on as usual.
  Its own ampere steps are turned on once its car draws 90 % of its power at minimum current (see Held at minimum), when one of them is the next step.
  With several at once, one that comes after an ampere step of another charger waits behind it by the fixed order,
  so the chargers of the group keep their currents until the start delay has passed.
  Why: the power is shared further only when what the car draws at its minimum current is known, so the currents do not go up and down while a car starts.
  A charger that is deactivated is no longer starting, also in a penalty or the safe state.
  Its state is starting only until its car charges; one whose car charges is shown as charging, though it is still starting.
  The status shows the start delay as what holds back the next step, as the waiting.
  Why: a car takes some time from activation until it draws power and ramps up, longer through a cloud service, so the average shows its power as free meanwhile.
  A step turned on in that power would be switched off again when the car starts. The start delay ends it for a car that never starts, as one that is full.
- Bypassed: car connected is false. Evaluated at each decision, ends as soon as it does not hold.
  A bypassed charger keeps its first ampere step if it has one and stays activated, gets no more,
  is not switched off for room and does not stand in the way of others. When it becomes bypassed, all ampere steps but the first are switched off at once.
  Why it stays activated: without evidence that the car left, as while a cloud service is down, the car may still be charging.
  With dynamic charging order, a charger whose car connected gives evidence that the car is disconnected is deactivated at once instead,
  so a car connected again is queued and gets in when there is room for its power at minimum current, instead of drawing power at once.
- Dynamic charging order (per group setting, default off): whether a charger that charges keeps its place ahead of the chargers that do not charge.
  Off, the configured charging priority always applies, so a car connected to a charger higher up goes first and takes the room of a charger below it.
  On, the current charging priority below decides.
- Current charging priority: equal to the configured one at each start, and always the configured one without dynamic charging order.
  With dynamic charging order, a charger that starts charging moves behind those that already charge,
  and a charger that stops charging for any reason, a fault included, or becomes bypassed moves to the back,
  each keeping the order of those that move at once, so the chargers that wait are queued in the order they fell back.
- Several at once without dynamic charging order: the ampere steps of all allowed chargers that are not bypassed are interleaved:
  the first of each charger in the configured priority, then the second, and so on.
- Several at once with dynamic charging order: the ampere steps of the activated chargers are interleaved in the configured priority.
  The ampere steps of the queued chargers come after them, interleaved in the current charging priority.
  Why: a charger activated to start sits among those that charge, so room is never made for them from its first ampere step.
  The first queued charger is turned on the normal way when it is the next step,
  and a switch-over can make room for it before that.
- Switch-over: with several at once and dynamic charging order, the first queued charger that is not activated gets its first ampere step,
  and every charger that charges above its minimum current is set to it, at the same decision.
  It is made when the free power, plus what those chargers draw above their estimated draw at their minimum current,
  covers the power at minimum current of the queued charger, also when none of them is above its minimum.
  The turn-on margin applies as for any step.
  Not above the limit, not at a decision where step 6 switched off something that was on,
  and not while a charger of the group is starting, so the charging power read is not from before the last switch-over.
  A charger that is activated again waits its waiting time first, as the next step does: nothing is turned on meanwhile, and the waiting is shown on its row.
  Why: it is never the next step while the chargers that charge can take more, so it would otherwise wait until its activations are forgotten.
  Why: a charger at the minimum current draws little, so the cars can share the power instead of the queued one waiting until the others are full.
- One at a time: the first charger in the current charging priority that charges may go on and get ampere steps, whatever the others do.
  The allowed chargers with a car before it may be activated, and wait at their minimum current, since they do not charge.
  Those after it are queued, and deactivated at once, so a car after it cannot draw power. When none charges, every allowed charger with a car may be activated,
  in the current charging priority as room allows, and the first whose car draws power, even a little, is the one that charges.
  Without dynamic charging order, a charger higher up that gets a car is activated with room made below it, if need be from the one that charges,
  and takes over when its car draws power. With dynamic charging order, the one that charges keeps its turn while it draws, since it is first in the current charging priority.
- A charger charges only when the regulation has activated it, so a car that is connected to a deactivated charger never starts by itself.
- Allowed to charge: no fault, not excluded, and no charging window, inside it, with an active override, or charging until disconnected.
  A charger that is not allowed has all ampere steps switched off at once and is deactivated at the first decision.
- Charge until disconnected (per charger setting, default off, only with a charging window): a charger charged in window is allowed to charge outside its window
  until car connected gives evidence that the car is disconnected. Why: a car cannot tell the charger that it is done, so only unplugging ends a charging session.
  It is regulated as without a window, so it may get and lose amperes, and be deactivated and activated again as room allows; the limit taking its last ampere does not end it.
  It shows the same charger states as without a window. A charger whose car has not charged in the window is deactivated when the window ends.
  The setting is configuration, but also a switch that may be changed while the regulation runs; it applies from the next decision without a restart.
- Charged in window is found at every decision while the regulation runs, also in the safe state and during a penalty, from what the decision reads before its commands:
  it starts at a decision inside the window where the charger is activated and actively charging, and ends at one where car connected gives evidence that the car is disconnected,
  whatever the setting. It is kept in memory over stops, the safe state and penalties, and lost at a restart of HA or the integration.
  Why the safe state and penalties: a car that is disconnected meanwhile must not leave the next car allowed.
  No decisions are made while the regulation is stopped, so a car disconnected then is not noticed, and a car connected before the start is allowed until it is disconnected.
  Why it is kept anyway: clearing it at a stop would end the charging of a car that stays connected over a stop and start.
- Excluded switch (per charger, default off): while on, the charger never charges.
- Deactivate on fault (per charger setting, default off): a charger has a fault while its fault flag shows one, read at each decision.
  Only evidence is a fault (see Ground rules). Why: a charger controlled through a cloud service reports unavailable while the service is down,
  and must not stop charging for that. The fault flag is kept while the setting is off, and is then neither read nor needed.
  A charger with a fault is not allowed to charge, so it is switched off and deactivated at once, does not stand in the way of the others in its group,
  and gets the command repeat of a deactivated charger.
  A fault neither arms nor ends a window override. Nothing is kept about a fault: when no flag shows one, the charger is regulated as before from the next decision.
- Override switch (per charger, default off): allows charging outside the charging window until it is switched off. A window that starts does not end it.
  No effect for a charger without charging window. Switching it off stops charging outside the window like the window ending.
  It only allows charging: it does not move the charger ahead of the others in its group.
- Override end (per charger setting, only with a charging window): what switches the override off besides the user.
  The override is armed at the first decision where what ends it has started, and only an armed override ends, so it can be turned on before the car arrives.
  When it ends, the switch is set back to off.
  - Manual (default): never ends by itself.
  - When the car no longer charges: armed when the charger is activated and actively charging;
    ends at the first decision where the charger is activated and the charging power and car charging give evidence that it does not charge.
    A charger the regulation has deactivated neither arms nor ends it. A car that never starts charging, as one that is already full, never arms it.
  - When the car is disconnected: armed when car connected is true; ends at the first decision where it is false.
- Only evidence of false ends an override: car connected from an entity that is off, a state that counts as false or a template that gives false,
  and not actively charging from each source that is given: a valid power of at most 100 W, an entity that is off, a state that counts as false or a template that gives false.
  Why: an override that has ended does not come back, so a sensor that is unavailable for a moment, as while a cloud service is down, must not stop the charging the user asked for.
- Whether an override is armed is kept in memory over stops, the safe state and penalties, and lost at a restart of HA or the integration and when its override end is changed;
  a car still connected or charging arms it again. Decisions in the safe state neither arm nor end it. The setting is configuration only, without a switch.
- Both switches can be used while the regulation runs, are saved at once, and take effect at the next decision;
  the excluded switch takes effect for the command repeat at the next window close. They do not restart the regulation.
