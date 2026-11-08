---
name: kraftvakt-regulation
description: How Kraftvakt's regulation must behave - concepts, measurement and averages, decisions, waiting times, penalty, safe state, start and stop, variants and EV charging, including every rule settled with the owner. Use before changing or reviewing anything in regulation/, measurement.py, runtime.py or charger_switches.py, or when a question is about what the regulation should do.
---

# Kraftvakt regulation

Kraftvakt is a Home Assistant integration for the Norwegian capacity tariff.
The grid company sets the capacity part of the grid fee from the hours of the
month with the highest consumption. Kraftvakt keeps the average consumption
over the last hour just below a power limit chosen by the user, by turning
appliances that can wait on and off in priority order. Everything runs locally.

This file is the specification. The original requirement document and the
implementation plan have been removed. When a rule here is unclear, ask the
owner instead of deciding.

## Concepts

| Term (Norwegian in the UI) | Meaning |
|---|---|
| Power limit (effektgrense) | The highest allowed average power, 1–50 kW, default 10 kW. The target the regulation keeps just below. |
| Power sensor (effektsensor) | A sensor from another integration with the house's total momentary power, in W or kW. A sensor without unit is read as W. Other units, non-numbers, `unknown` and `unavailable` are invalid. Negative values count as 0 W. |
| Regulation window (reguleringsvindu) | 10–600 s, default 60 s. |
| Regulation average (reguleringssnitt) | Time-weighted average of the power sensor over one regulation window. Drives all decisions. |
| Regulation interval (reguleringsintervall) | 1x–4x the regulation window, default 1x. A decision is made every N windows. |
| Capacity window / average consumption (snittforbruk) | Sliding time-weighted average over exactly one hour back, not configurable. Used only for the penalty. |
| Decision (avgjørelse) | What the regulation decides at each interval. All evaluation and all switching happens at decisions. |
| Free power | Power limit minus regulation average. |
| Power reserve (effektreserve) | Optional free power an appliance needs before it may be turned on, ≥ 0 kW, no upper limit. |
| Waiting time (ventetid) | Time that must pass before an appliance is turned on. |
| Appliance (apparat) | An entity Kraftvakt turns on and off with configurable actions. |
| Priority list (prioritetsliste) | Sorted list of appliances, their variants and the «EV charging» entry. Top is highest priority, turned off last. |
| Variant | Extra entry for an appliance with a label and a true/false expression, giving it another place in the list. |
| Current variant | The variant of the topmost true expression, or the appliance itself when none is true. Only this entry takes part. |
| Safe state (sikker tilstand) | Everything off and nothing turned on, because there is no valid power measurement. |
| Penalty threshold (straffeterskel) | 0–10 kW above the power limit, default 1 kW. |
| Overconsumption (overforbruk) | Net energy above the power limit since the overconsumption state started (above adds, below subtracts). |
| Penalty period (straffeperiode) | Safety valve: everything held off until the overconsumption is paid back. Should never be needed. |
| Fictive appliance (fiktivt apparat) | One ampere of an EV charger's current, treated by the regulation as an appliance. |
| Bypassed charger (forbigått) | A charger that does not draw power and so must not stand in the way of others. |
| Waiting charger (ventende) | With one charger at a time: a charger that may not charge because another is actively charging. |
| Charging window (ladetidsrom) | Optional daily time span in whole minutes, in HA's time zone, may span midnight, start ≠ end. |

Resolution of settings: kW with two decimals, the regulation window in whole
seconds, the waiting time in whole minutes, currents in whole amperes.

## Ground rules

- Kraftvakt only decides whether an appliance may be on. It never estimates
  what an appliance uses from changes in the total consumption.
- It does not read or react to the state of appliances. It assumes each one is
  as Kraftvakt last told it. Switching appliances outside Kraftvakt can disturb
  the regulation. Exception: for chargers it reads the charging power and
  «car connected».
- A failed action is logged and not retried. The regulation goes on as if it
  worked.
- Only the current configuration is regulated. Removed appliances and chargers
  get no more commands and are not cleaned up.
- The configuration can only be changed while the regulation is stopped,
  except the two switches per charger. Everything is off while stopped, so
  removed appliances are already off and new ones are controlled from the next
  start.
- The state of the regulation (on/off, waiting times, cycling counters,
  overconsumption, penalty, current charging priority, bypassed chargers,
  current variants) starts again with defaults at every start: HA or
  integration start, user start, after the safe state and after a penalty.
  The configuration and the charger switch positions are kept over any restart.
- True/false from HA (variant expressions, «car connected») is a boolean entity
  or a template. True only when the entity is `on` or the template gives the
  boolean true. Everything else is false, also unavailable entities and
  failing templates. Settings are named so that true means the thing is the
  case. Missing evidence means the regulation acts as if the thing is not the
  case.

## Measurement

- Windows keep their own cadence from when the integration starts, scheduled
  at absolute times, also while the regulation is stopped. Each regulation
  average covers its own window, without overlap.
- Averages are energy divided by time, correct for any update rate of the
  sensor (each value holds until the next).
- At startup (HA or integration start) the hour before is taken from HA's
  recorder history of the power sensor, read like live values (an invalid
  value keeps the last valid one in place, and the oldest valid value fills
  the time before it). Settled with the owner, because filling the hour with
  the first value after a restart made the average consumption far too low:
  everything is turned off at start, so the first value is only the
  background. Without a recorder or any valid history, the missing past is
  filled with the first measured value. The regulation window is not affected: the first
  one starts at startup. The time HA was down counts with the last value
  recorded before it stopped.
- Validity is the state when a window closes. A gap inside a window is filled
  with the last valid value.
- One window closing without a valid value is tolerated (the last valid value
  is used). Two in a row make the averages unknown: the average sensors become
  unavailable until a valid value comes, also while the regulation is stopped.
  The history is kept, and the gap counts with the last valid value before
  it, like the time HA was down. Settled with the owner after the exploratory
  test (finding F3): discarding the history and filling the hour with the
  first value after the gap made the average consumption far too low (only the
  background, since everything is off in the safe state) or far too high (a
  value that lasted a millisecond while the appliances were turned off).
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
  6. Forced switch-offs: chargers not allowed to charge (all fictive off and
     deactivate), newly bypassed chargers down to one fictive appliance,
     appliances that switch variant.
  7. Build the ordered slots (current variants, fictive appliances in place of
     «EV charging»).
  8. Above the limit: switch off the lowest priority slot that is on and not a
     bypassed charger's, without waiting, and cancel any waiting.
  9. Turn on: only the first slot that is off and not skipped may be turned on.
- Only one appliance is turned on or off per decision based on free power.
  Several may be switched off at once only when consumption must drop at once
  or switching does not change consumption: start and stop, safe state,
  penalty, chargers not allowed to charge, bypassed chargers, variant switches.
- Turn on only when the regulation average is under the limit, and average plus
  power reserve is at most the limit. At exactly the limit nothing is turned on
  or off.
- Fixed order: an appliance is never turned on before all above it are on.
  Skipped: entries that are not the current variant, chargers not allowed to
  charge, bypassed and waiting chargers.

## Waiting time

- When the next slot may be turned on, its waiting time starts. It is turned on
  at the first decision after the waiting time has passed, if the conditions
  still hold. Waiting time 0 turns it on at the same decision. If the
  conditions fail, the waiting is cancelled and starts again later. Only the
  slot that is next can wait.
- Linear: waiting time = waiting time at the limit × min(1, average / limit),
  recalculated at each decision while it runs. Waiting time at the limit is
  0–10 min, default 5 min.
- Persistent cycling: when the same slot is turned on again without any other
  slot being switched in between, the counter grows. From the second time on
  the waiting time is fixed, independent of the average:
  min(cap, waiting at limit + step × (n − 2)). Appliances: step 2 min, cap
  15 min (5, 7, 9 … 15). Fictive appliances: step 5 min, cap 30 min. The first
  time again uses the linear time. Any command for another slot, also forced
  ones, resets the counter. Not configurable.

## Penalty

- Overconsumption state: starts when the average consumption is above the limit
  at a decision, with overconsumption 0 at that decision. Every regulation
  average closed after it adds (average − limit) × window. It ends when the
  overconsumption is ≤ 0 (rounding below 1e-9 kWh counts as 0), at the
  earliest at the next decision. If the average consumption is still above the
  limit, a new state starts at 0 at once.
- A penalty starts when the average consumption is above limit + threshold and
  the overconsumption is > 0. With threshold 0 it starts one decision after the
  state started. Everything is turned off at once, also chargers, with a
  turn-off command to every appliance in the configuration. Nothing is turned
  on while it lasts.
- During a penalty only positive contributions count until the first regulation
  average under the limit. From then on recovery counts net and does not stop
  again.
- The penalty ends only when the overconsumption is paid back (then the
  regulation starts again with everything off at that decision) or by a restart
  (stop, safe state, HA start). The current variants are still evaluated during
  a penalty; they give no commands since everything is off.

## Safe state

- Entered at the first decision where the power sensor was invalid at the last
  two window closes. Every appliance and charger is turned off at once, and
  nothing is turned on. The safe state binary sensor is on.
- When a valid value comes back, the averages are known again and the regulation
  starts again with everything off at the first decision.
- A sensor that never reports after startup also leads to the safe state.

## Start and stop

- Every start turns off every appliance in the configuration, once per
  appliance even with variants, and deactivates every charger. The current
  variant is found at the first decision.
- Starts: when HA has finished starting (so the appliances' integrations are
  loaded), at once after a reload of the integration, when the user starts it,
  when a penalty ends, and when the power sensor is back after the safe state.
  If the user starts or stops before HA has finished starting, that wins.
- After a reload, the turn-off commands wait until the previous runtime's
  actions are done (a lock shared over reloads).
- The user stops and starts from the panel or the regulation switch; they are
  the same function. Stopping turns everything off at once and makes no more
  decisions.
- The regulation starts by itself at HA/integration start, and can only be
  started when the configuration is complete: power sensor chosen; every
  appliance has entity, turn-on and turn-off action; with EV charging enabled,
  every charger has entity, activate, deactivate and set-current actions and a
  charging power sensor, and also «car connected» when only one charger may
  charge at a time.

## Variants

- Each ordinary appliance may have variants, sorted, each with a non-empty
  label unique for the appliance and an expression. Same actions and reserve as
  the appliance. Not for chargers or «EV charging».
- Evaluated at each decision. When an appliance switches variant: it is off
  afterwards at the new place and comes on again the normal way. If it was off
  and its new place is above the lowest slot that is on, that lowest slot is
  switched off to give room. Its waiting time and cycling counter are reset.
- Several switching at the same decision are handled one by one in the order of
  their new place, highest first. One that must go off anyway can be the one
  that gives room.

## EV charging

- Enabled or disabled, default disabled. While disabled, chargers stay in the
  configuration but are not regulated, not required for completeness, and their
  switches are unavailable (positions kept).
- «One charger at a time», default yes. Chargers are sorted in the configured
  charging priority.
- Each charger is split into fictive appliances, one per ampere from min to max
  current (whole amperes, 1 ≤ min ≤ max, default 6 and 16). Current = min +
  number on − 1. None on means deactivated. The fictive appliances sit at the
  place of «EV charging».
- First fictive on: set current to min, then activate, and only the first has
  the charger's power reserve (0–5 kW, default 4 kW). Later ones: set the new
  current. Switching off: set the lower current, or for the last one set
  current to min and then deactivate. Every deactivation sets min current
  first. The set-current action always gets a current between min and max.
- Actively charging: charging power > 100 W (not configurable), or an invalid
  charging power, also when deactivated.
- Bypassed: «car connected» is set and false, or not actively charging while
  the first fictive appliance has been on for at least two windows. Evaluated at
  each decision, ends as soon as neither holds. A bypassed charger keeps its
  first fictive appliance and stays activated, gets no more, is not switched
  off above the limit and does not stand in the way of others. When it becomes
  bypassed, all fictive appliances but the first are switched off at once.
- Rest (settled with the owner after the exploratory test, finding F5): a
  charger that becomes bypassed because it does not charge rests. It stays
  bypassed while it rests, also after it is deactivated, and may be tried
  again when the rest is over: 15 min the first time, then 30 min, then 60 min
  each time it is tried and still does not charge. The rest ends at once, and
  the next one is 15 min again, when «car connected» is false at a decision
  (a car that is connected again is tried at once) or when the charger
  charges actively while activated. Every start begins without rests. Without
  it, two chargers with full cars took turns being activated forever when only
  one may charge at a time, and the appliances below «EV charging» were never
  turned on.
- Current charging priority: equal to the configured one at each start.
  Newly bypassed chargers move to the back, keeping their order, and stay there
  even after they stop being bypassed, until it is corrected: when a charger has
  all its fictive appliances on, the priority is set to the configured order for
  the chargers that are not bypassed, bypassed ones stay at the back.
- Several at once: the fictive appliances of all allowed, not bypassed
  chargers are interleaved: the first of each charger in current priority, then
  the second, and so on.
- One at a time: an actively charging charger may go on charging, whatever the
  priority; others that want to charge are waiting. If several are actively
  charging, the activated one wins, otherwise the first in current priority.
  When none charges, the first allowed and not bypassed in current priority
  gets fictive appliances. Before a charger is activated, any other activated
  charger is deactivated at the same decision (never more than one activated).
- A charger charges only when the regulation has activated it, so a car that is
  connected to a deactivated charger never starts by itself.
- Allowed to charge: not excluded, and no charging window, inside it, or with
  an active override. A charger that is not allowed has all fictive appliances
  switched off at once and is deactivated at the first decision.
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
  take effect at the next decision. They do not restart the regulation.
