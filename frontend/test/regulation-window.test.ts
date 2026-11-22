import { describe, expect, it } from "vitest";
import { closestWindowUpdates, regulationWindowOptions, windowSeconds } from "../src/regulation-window";
import { CAPABILITIES, config } from "./builders";
import regulationWindow from "./fixtures/regulation_window.json";

const LIMITS = CAPABILITIES.regulation_window;

describe("regulation window options", () => {
  it.each(regulationWindow.options)("for a power sensor that reports every %s s are the backend's", (interval, options) => {
    expect(regulationWindowOptions(interval as number, LIMITS)).toEqual(options);
  });
});

describe("closest window", () => {
  it.each([
    [10, 2, 5],
    [30, 2.5, 12],
    [17, 2, 10],
    [15, 10, 1],
    [60, 15, 4],
  ])("to %s s with updates every %s s is %s updates", (seconds, interval, updates) => {
    expect(closestWindowUpdates(seconds, interval, LIMITS)).toBe(updates);
  });

  it("is none when the power sensor reports too seldom", () => {
    expect(closestWindowUpdates(10, 130, LIMITS)).toBeNull();
  });
});

describe("window seconds", () => {
  it("are the updates at the interval, unknown while either is not set", () => {
    expect(windowSeconds({ ...config().general, regulation_window_updates: 5, power_sensor_interval_s: 2.5 })).toBe(12.5);
    expect(windowSeconds({ ...config().general, power_sensor_interval_s: null })).toBeNull();
  });
});
