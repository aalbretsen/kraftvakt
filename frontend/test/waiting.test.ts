import { describe, expect, it } from "vitest";
import { repeatedTurnOnWaiting, untilDecision, waitingCurve } from "../src/waiting";
import waiting from "./fixtures/waiting.json";

describe("waiting curve", () => {
  it.each(waiting.curves)("with steepness $steepness and pivot $pivot gives the backend's shares", ({ steepness, pivot, shares }) => {
    const curve = waitingCurve(steepness, pivot);
    for (const [utilization, share] of shares) {
      expect(curve(utilization), `at ${utilization}`).toBeCloseTo(share, 12);
    }
  });
});

describe("repeated turn-on", () => {
  const { wait_at_limit_s, increment_factor, increments, waiting_s } = waiting.repeated_turn_on;

  it.each(waiting_s)("the turn-on %i in a row waits as in the backend", (turnOn, seconds) => {
    expect(repeatedTurnOnWaiting(turnOn, wait_at_limit_s, increment_factor, increments)).toBe(seconds);
  });

  it("does not grow without a waiting time at the limit", () => {
    expect(repeatedTurnOnWaiting(9, 0, increment_factor, increments)).toBe(0);
  });
});

describe("actual waiting", () => {
  it.each([
    [0, 0],
    [0.002, 0],
    [0.5, 10],
    [1, 10],
    [10, 10],
    [10.000000001, 10],
    [11, 20],
  ])("of %f s is the first decision after it, %i s", (waitingS, actual) => {
    expect(untilDecision(waitingS, 10)).toBe(actual);
  });
});
