import { describe, expect, it } from "vitest";

import { reportedStates, stateEvidence } from "../src/entity-states";

describe("the states offered for an entity", () => {
  it("come from its options, its current state, its history and the chosen states, each once and without unknown or unavailable", () => {
    const stateObj = { state: "charging", attributes: { options: ["disconnected", "awaiting_start", "charging"] } };
    expect(reportedStates(stateObj, ["completed", "unavailable", "charging"], ["error", "completed"])).toEqual([
      "disconnected",
      "awaiting_start",
      "charging",
      "completed",
      "error",
    ]);
  });

  it("are only the history and the chosen states for an entity Home Assistant does not have", () => {
    expect(reportedStates(undefined, ["paused"], ["unknown"])).toEqual(["paused"]);
  });
});

describe("a state as evidence", () => {
  it("is true for a chosen state that counts as true, false for another state, and nothing without a state", () => {
    expect(stateEvidence("charging", ["charging", "awaiting_start"], true)).toBe(true);
    expect(stateEvidence("completed", ["charging"], true)).toBe(false);
    expect(stateEvidence("unavailable", ["charging"], true)).toBeNull();
    expect(stateEvidence(undefined, ["charging"], true)).toBeNull();
  });

  it("is true for any other state when the chosen states count as false, but never for unavailable", () => {
    expect(stateEvidence("charging", ["disconnected"], false)).toBe(true);
    expect(stateEvidence("disconnected", ["disconnected"], false)).toBe(false);
    expect(stateEvidence("unavailable", ["disconnected"], false)).toBeNull();
  });
});
