/**
 * The history the diagnostics page draws, worked out from what the backend keeps: the last
 * decisions with their commands, and the state now.
 */
import type {
  ApplianceStatus,
  ChargerStatus,
  CommandsBefore,
  DecisionCommand,
  DecisionRecord,
  DiagnosticsEvent,
  DiagnosticsPart,
  FailedAction,
  StatusSnapshot,
  WaitingStep,
} from "./api";

/** A time span in ms since the epoch, with what held over it. */
export interface Segment<Value> {
  start: number;
  end: number;
  value: Value;
}

/**
 * What each appliance and EV charger was set to, by id, from `from` to `to`. An appliance is on or
 * off, and an EV charger has its current, null while deactivated. Where it is not known, it has no
 * segment.
 */
export interface Lanes {
  from: number;
  to: number;
  appliances: Record<string, Segment<boolean>[]>;
  chargers: Record<string, Segment<number | null>[]>;
  /** The waiting of the next step, by the id of its appliance or EV charger. */
  waiting: Record<string, Segment<null>[]>;
}

/** Return what the panel holds after a part: the part's items, after the held items that are still kept and come before them. */
export function mergePart<Item>(held: Item[], part: DiagnosticsPart<Item>, time: (item: Item) => string): Item[] {
  if (part.replace) {
    return part.items;
  }
  const keptFrom = part.kept_from === null ? Infinity : Date.parse(part.kept_from);
  const resentFrom = part.items.length > 0 ? Date.parse(time(part.items[0])) : Infinity;
  const stillHeld = held.filter((item) => {
    const moment = Date.parse(time(item));
    return moment >= keptFrom && moment < resentFrom;
  });
  return [...stillHeld, ...part.items];
}

/**
 * Return what each appliance and EV charger was set to from the commands before the decisions kept
 * until now, or until the last decision while stopped.
 *
 * After a command, it is what the command set. One without a command in that time is as it is now,
 * while the regulation runs. Before the last start, and while stopped, it is not known, since the
 * commands of a stop are not kept.
 */
export function lanes(decisions: DecisionRecord[], before: CommandsBefore | null, status: StatusSnapshot, startedAt: string | null, now: number): Lanes {
  const running = startedAt !== null;
  const from = before === null ? now : Date.parse(before.time);
  const kept = decisions.filter((decision) => Date.parse(decision.time) > from);
  const latestKept = kept.length > 0 ? Date.parse(kept[kept.length - 1].time) : from;
  const to = running ? now : latestKept;
  const commands = before === null ? kept : [{ time: before.time, commands: before.commands }, ...kept];
  const appliances: Record<string, Segment<boolean>[]> = {};
  for (const appliance of applianceRows(status)) {
    appliances[appliance.id] = segments(commands, from, to, running, appliance.on, (command) => applianceValue(command, appliance.id));
  }
  const chargers: Record<string, Segment<number | null>[]> = {};
  for (const charger of chargerRows(status)) {
    chargers[charger.id] = segments(commands, from, to, running, charger.activated ? charger.current_a : null, (command) => chargerValue(command, charger.id));
  }
  return { from, to, appliances, chargers, waiting: waitingSegments(kept, from, to, running) };
}

/** What a command sets the item to: undefined when it is not for the item, or does not tell. */
type CommandValue<Value> = (command: DecisionCommand) => Value | undefined;

function segments<Value>(
  decisions: Pick<DecisionRecord, "time" | "commands">[],
  from: number,
  to: number,
  running: boolean,
  now: Value,
  valueOf: CommandValue<Value>,
): Segment<Value>[] {
  const changes: { time: number; value: Value }[] = [];
  for (const decision of decisions) {
    let value: Value | undefined;
    for (const command of decision.commands) {
      const set = valueOf(command);
      value = set === undefined ? value : set;
    }
    if (value !== undefined) {
      changes.push({ time: Date.parse(decision.time), value });
    }
  }
  if (changes.length === 0) {
    return running && to > from ? [{ start: from, end: to, value: now }] : [];
  }
  return changes.map((change, index) => ({ start: change.time, end: changes[index + 1]?.time ?? to, value: change.value }));
}

function applianceValue(command: DecisionCommand, applianceId: string): boolean | undefined {
  if ("appliance_id" in command && command.appliance_id === applianceId) {
    return command.command === "TurnOnAppliance";
  }
  return undefined;
}

/** An EV charger gets its current before it is activated or deactivated; 0 A deactivates one switched by its current. */
function chargerValue(command: DecisionCommand, chargerId: string): number | null | undefined {
  if (!("charger_id" in command) || command.charger_id !== chargerId) {
    return undefined;
  }
  switch (command.command) {
    case "SetChargingCurrent":
      return command.current_a > 0 ? command.current_a : null;
    case "DeactivateCharger":
      return null;
    case "ActivateCharger":
      return undefined;
  }
}

/** The waiting of each step, from when it started, or `from`, until the decision where it no longer waits, or `to` when it still waits. */
function waitingSegments(decisions: DecisionRecord[], from: number, to: number, running: boolean): Record<string, Segment<null>[]> {
  const waiting: Record<string, Segment<null>[]> = {};
  let open: { id: string; startedAt: string; segment: Segment<null> } | undefined;
  for (const decision of decisions) {
    const time = Date.parse(decision.time);
    const current = decision.waiting && { id: waitingItem(decision.waiting.key), startedAt: decision.waiting.started_at };
    if (open && current?.id === open.id && current.startedAt === open.startedAt) {
      open.segment.end = time;
      continue;
    }
    if (open) {
      open.segment.end = time;
    }
    open = undefined;
    if (current) {
      const segment = { start: Math.max(Date.parse(current.startedAt), from), end: time, value: null };
      (waiting[current.id] ??= []).push(segment);
      open = { ...current, segment };
    }
  }
  if (open && running) {
    open.segment.end = to;
  }
  return waiting;
}

function waitingItem(step: WaitingStep): string {
  return "appliance_id" in step ? step.appliance_id : step.charger_id;
}

export function applianceRows(status: StatusSnapshot): ApplianceStatus[] {
  return status.priority.filter((row): row is ApplianceStatus => row.type === "appliance");
}

export function chargerRows(status: StatusSnapshot): ChargerStatus[] {
  return status.priority.flatMap((row) => (row.type === "charger_group" ? row.chargers : []));
}

/** A row of the event log: a command of a decision, or a failed action. */
export type LogRow = { time: string; command: DecisionCommand; decision: DecisionRecord } | { time: string; failed: FailedAction };

/** Return the commands of the decisions and the failed actions, newest first, with the commands of a decision in their order. */
export function logRows(decisions: DecisionRecord[], failed: FailedAction[]): LogRow[] {
  const rows: LogRow[] = [
    ...decisions.flatMap((decision) => decision.commands.map((command) => ({ time: decision.time, command, decision }))),
    ...failed.map((action) => ({ time: action.time, failed: action })),
  ];
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => Date.parse(b.row.time) - Date.parse(a.row.time) || a.index - b.index)
    .map(({ row }) => row);
}

/** A command repeat that is due: the appliance or EV charger and when. */
export interface RepeatDue {
  type: "appliance" | "charger";
  id: string;
  dueAt: string;
}

/** Return the command repeats, the first due first. */
export function repeatsDue(repeats: DiagnosticsEvent["repeats_due_at"]): RepeatDue[] {
  return [
    ...Object.entries(repeats.appliances).map(([id, dueAt]) => ({ type: "appliance" as const, id, dueAt })),
    ...Object.entries(repeats.chargers).map(([id, dueAt]) => ({ type: "charger" as const, id, dueAt })),
  ].sort((a, b) => Date.parse(a.dueAt) - Date.parse(b.dueAt));
}
