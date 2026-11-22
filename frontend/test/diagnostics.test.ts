import { describe, expect, it } from "vitest";
import type { ApplianceStatus, ChargerStatus, DecisionCommand, DecisionRecord, StatusSnapshot } from "../src/api";
import { lanes, logRows, mergePart, repeatsDue } from "../src/diagnostics";

const T0 = Date.parse("2026-01-05T12:00:00Z");

function at(seconds: number): string {
  return new Date(T0 + seconds * 1000).toISOString();
}

function decision(seconds: number, commands: DecisionCommand[] = [], parts: Partial<DecisionRecord> = {}): DecisionRecord {
  return {
    time: at(seconds),
    regulation_average_w: 5000,
    tariff_average_w: 4000,
    power_sensor_valid: true,
    safe_state: false,
    penalty_active: false,
    overconsumption_wh: 0,
    waiting: null,
    commands,
    ...parts,
  };
}

function applianceRow(id: string, on: boolean): ApplianceStatus {
  return {
    type: "appliance",
    id,
    name: id,
    essential: false,
    on,
    excluded: false,
    variant: null,
    power_w: null,
    temperature: null,
    waiting_since: null,
    waiting_until: null,
    waiting_ends_at: null,
    power_to_free_w: null,
  };
}

function chargerRow(id: string, currentA: number | null): ChargerStatus {
  return {
    id,
    name: id,
    state: currentA === null ? "deactivated" : "charging",
    activated: currentA !== null,
    current_a: currentA,
    power_w: null,
    bypassed: false,
    charging: currentA !== null,
    starting_until: null,
    waiting_since: null,
    waiting_until: null,
    waiting_ends_at: null,
    power_to_free_w: null,
  };
}

function status(appliances: ApplianceStatus[], chargers: ChargerStatus[] = []): StatusSnapshot {
  return {
    running: true,
    config_version: 0,
    missing: [],
    safe_state: false,
    penalty: { active: false, overconsumption_wh: 0, recovery_started: false },
    regulation_average_w: null,
    tariff_average_w: null,
    power_limit_w: 10000,
    regulation_window_s: 10,
    next_decision_at: null,
    priority: [...appliances, { type: "charger_group", id: "g", name: "EV chargers", chargers }],
  };
}

const turnOn = (id: string): DecisionCommand => ({ command: "TurnOnAppliance", appliance_id: id, variant_id: null });
const turnOff = (id: string): DecisionCommand => ({ command: "TurnOffAppliance", appliance_id: id, variant_id: null });
const setCurrent = (id: string, currentA: number): DecisionCommand => ({ command: "SetChargingCurrent", charger_id: id, current_a: currentA });

describe("merging the parts of the diagnostics", () => {
  const time = (item: { start: string }) => item.start;
  const held = [{ start: at(0) }, { start: at(10) }, { start: at(20) }];

  it("replaces what is held when the part says so", () => {
    expect(mergePart(held, { replace: true, kept_from: at(30), items: [{ start: at(30) }] }, time)).toEqual([{ start: at(30) }]);
  });

  it("forgets what is no longer kept, and what the part sends again", () => {
    const merged = mergePart(held, { replace: false, kept_from: at(10), items: [{ start: at(20) }, { start: at(30) }] }, time);

    expect(merged).toEqual([{ start: at(10) }, { start: at(20) }, { start: at(30) }]);
  });

  it("holds nothing when nothing is kept", () => {
    expect(mergePart(held, { replace: false, kept_from: null, items: [] }, time)).toEqual([]);
  });
});

describe("lanes", () => {
  const started = { time: at(-100), commands: [] };

  it("shows what each command set until the next", () => {
    const decisions = [decision(0), decision(10, [turnOn("a")]), decision(20, [turnOn("b"), setCurrent("c", 6)]), decision(30, [turnOff("a")])];

    const result = lanes(decisions, started, status([applianceRow("a", false)]), at(-100), T0 + 40_000);

    expect(result.from).toBe(T0 - 100_000);
    expect(result.appliances.a).toEqual([
      { start: T0 + 10_000, end: T0 + 30_000, value: true },
      { start: T0 + 30_000, end: T0 + 40_000, value: false },
    ]);
  });

  it("starts with what the commands before the decisions set", () => {
    const before = { time: at(-100), commands: [turnOff("a"), setCurrent("c", 6), { command: "DeactivateCharger" as const, charger_id: "c" }] };

    const result = lanes([decision(0, [turnOn("a")])], before, status([applianceRow("a", true)], [chargerRow("c", null)]), at(-200), T0 + 10_000);

    expect(result.appliances.a).toEqual([
      { start: T0 - 100_000, end: T0, value: false },
      { start: T0, end: T0 + 10_000, value: true },
    ]);
    expect(result.chargers.c).toEqual([{ start: T0 - 100_000, end: T0 + 10_000, value: null }]);
  });

  it("shows an appliance without commands as it is now while the regulation runs, and not while it is stopped", () => {
    const decisions = [decision(0), decision(10)];

    expect(lanes(decisions, started, status([applianceRow("a", true)]), at(-100), T0 + 20_000).appliances.a).toEqual([{ start: T0 - 100_000, end: T0 + 20_000, value: true }]);
    expect(lanes(decisions, started, status([applianceRow("a", true)]), null, T0 + 20_000).appliances.a).toEqual([]);
  });

  it("leaves out the decisions before the commands before the decisions, since they are from before the last start", () => {
    const decisions = [decision(0, [turnOn("a")]), decision(10)];

    const result = lanes(decisions, { time: at(5), commands: [turnOff("a")] }, status([applianceRow("a", true)]), at(5), T0 + 20_000);

    expect(result.from).toBe(T0 + 5_000);
    expect(result.appliances.a).toEqual([{ start: T0 + 5_000, end: T0 + 20_000, value: false }]);
  });

  it("knows nothing before the first start", () => {
    const result = lanes([], null, status([applianceRow("a", false)]), null, T0);

    expect(result).toMatchObject({ from: T0, to: T0, appliances: { a: [] } });
  });

  it("ends at the last decision while the regulation is stopped, or at the start without one", () => {
    const result = lanes([decision(0, [turnOn("a")]), decision(10)], started, status([applianceRow("a", false)]), null, T0 + 60_000);

    expect(result.to).toBe(T0 + 10_000);
    expect(result.appliances.a).toEqual([{ start: T0, end: T0 + 10_000, value: true }]);
    expect(lanes([], started, status([applianceRow("a", false)]), null, T0 + 60_000).to).toBe(T0 - 100_000);
  });

  it("gives an EV charger the current of its commands, and none while deactivated", () => {
    const decisions = [
      decision(0, [setCurrent("c", 6), { command: "ActivateCharger", charger_id: "c" }]),
      decision(10, [setCurrent("c", 7)]),
      decision(20, [setCurrent("c", 6), { command: "DeactivateCharger", charger_id: "c" }]),
      decision(30, [setCurrent("c", 6)]),
      decision(40, [setCurrent("c", 0), setCurrent("d", 8), turnOn("a")]),
    ];

    const result = lanes(decisions, started, status([], [chargerRow("c", null)]), at(-100), T0 + 50_000);

    expect(result.chargers.c.map((segment) => segment.value)).toEqual([6, 7, null, 6, null]);
  });

  it("shows an EV charger without commands with its current now", () => {
    const result = lanes([decision(0)], started, status([], [chargerRow("c", 8), chargerRow("d", null)]), at(-100), T0 + 10_000);

    expect(result.chargers.c).toEqual([{ start: T0 - 100_000, end: T0 + 10_000, value: 8 }]);
    expect(result.chargers.d).toEqual([{ start: T0 - 100_000, end: T0 + 10_000, value: null }]);
  });

  it("shows the waiting from when it started until the decision where it no longer waits, or until now", () => {
    const waitingA = { key: { appliance_id: "a" }, started_at: at(-130), until: at(60) };
    const waitingC = { key: { charger_id: "c", index: 3 }, started_at: at(20), until: at(50) };
    const decisions = [
      decision(0, [], { waiting: waitingA }),
      decision(10, [], { waiting: waitingA }),
      decision(20, [], { waiting: waitingC }),
      decision(30, [], { waiting: waitingC }),
    ];

    const result = lanes(decisions, started, status([applianceRow("a", false)], [chargerRow("c", 6)]), at(-100), T0 + 40_000);

    expect(result.waiting).toEqual({
      a: [{ start: T0 - 100_000, end: T0 + 20_000, value: null }],
      c: [{ start: T0 + 20_000, end: T0 + 40_000, value: null }],
    });
  });

  it("ends a waiting that starts again at the decision where the new one starts", () => {
    const first = { key: { appliance_id: "a" }, started_at: at(0), until: at(20) };
    const second = { key: { appliance_id: "a" }, started_at: at(10), until: at(40) };

    const result = lanes([decision(0, [], { waiting: first }), decision(10, [], { waiting: second })], started, status([applianceRow("a", false)]), null, T0 + 60_000);

    expect(result.waiting.a).toEqual([
      { start: T0, end: T0 + 10_000, value: null },
      { start: T0 + 10_000, end: T0 + 10_000, value: null },
    ]);
  });
});

describe("the event log", () => {
  it("lists the commands and the failed actions newest first, with the commands of a decision in their order", () => {
    const first = decision(0, [turnOn("a")]);
    const second = decision(20, [turnOff("b"), turnOff("a")]);
    const failed = { time: at(10), action: "turn_on light.a", error: "Light is gone" };

    const rows = logRows([first, second], [failed]);

    expect(rows).toEqual([
      { time: at(20), command: turnOff("b"), decision: second },
      { time: at(20), command: turnOff("a"), decision: second },
      { time: at(10), failed },
      { time: at(0), command: turnOn("a"), decision: first },
    ]);
  });
});

describe("command repeats", () => {
  it("lists the appliances and EV chargers by when their command is repeated", () => {
    expect(repeatsDue({ appliances: { a: at(30), b: at(10) }, chargers: { c: at(20) } })).toEqual([
      { type: "appliance", id: "b", dueAt: at(10) },
      { type: "charger", id: "c", dueAt: at(20) },
      { type: "appliance", id: "a", dueAt: at(30) },
    ]);
  });
});
