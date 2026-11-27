import { describe, expect, it } from "vitest";
import type { PowerSensorReports } from "../src/api";
import { localizer } from "../src/localize";
import { reportLines, reportText, updatesPerWindow, windowChoices } from "../src/power-sensor-reports";
import { CAPABILITIES } from "./builders";

const CHOICES = windowChoices(CAPABILITIES.limits.general.regulation_window_s);

function reports(changes: Partial<PowerSensorReports> = {}): PowerSensorReports {
  return { updates: 1440, update_interval_s: 2.5, steady: true, shortest_s: 2.4, longest_silence_s: 2.6, lost_updates: 0, suggested_timeout_s: 300, ...changes };
}

const keys = (lines: ReturnType<typeof reportLines>) => lines.map((line) => [line.key, line.warning]);

describe("window choices", () => {
  it("are the lengths in the range of the setting", () => {
    expect(CHOICES).toEqual([10, 20, 30, 40, 50, 60]);
  });
});

describe("updates per window", () => {
  it.each([
    [10, 2.5, 4],
    [30, 10, 3],
    [10, 10, 1],
    [10, 3, 3],
    [10, 4, 3],
    [10, 30, 1],
  ])("a window of %d s with updates every %d s lasts %d update intervals, as in the backend", (windowS, intervalS, expected) => {
    expect(updatesPerWindow(windowS, intervalS)).toBe(expected);
  });
});

describe("report lines", () => {
  it("tell the measurements per regulation window of steady reports", () => {
    expect(reportLines(reports(), 10, 300, CHOICES)).toEqual([{ key: "reports.steady", params: { interval: 2.5, updates: 4, seconds: 10 }, warning: false }]);
    expect(keys(reportLines(reports({ update_interval_s: 10 }), 10, 300, CHOICES))).toEqual([["reports.steady_one", false]]);
    expect(reportLines(reports({ update_interval_s: 4 }), 10, 300, CHOICES)[0]).toEqual({
      key: "reports.steady_longer",
      params: { interval: 4, updates: 3, seconds: 12 },
      warning: false,
    });
  });

  it("warn when steady reports come less often than the regulation window", () => {
    const lines = reportLines(reports({ update_interval_s: 30, longest_silence_s: 30 }), 10, 300, CHOICES);
    expect(lines[1]).toEqual({ key: "reports.longer_than_window", params: { interval: 30, seconds: 30, choice: 30 }, warning: true });
    expect(reportLines(reports({ update_interval_s: 90, longest_silence_s: 90 }), 10, 300, CHOICES)[1].params.choice).toBe(60);
  });

  it("explain uneven reports, and how to make them steadier", () => {
    const lines = reportLines(reports({ steady: false, longest_silence_s: 48 }), 10, 300, CHOICES);
    expect(lines).toEqual([
      { key: "reports.varies", params: { shortest: 2.4, longest: 48, window: 10 }, warning: false },
      { key: "reports.steadier", params: {}, warning: false },
    ]);
  });

  it("warn of silences longer than a minute, and of silences close to the timeout", () => {
    expect(keys(reportLines(reports({ steady: false, longest_silence_s: 75 }), 10, 300, CHOICES))).toEqual([
      ["reports.varies", false],
      ["reports.seldom", true],
    ]);
    expect(keys(reportLines(reports({ steady: false, longest_silence_s: 150 }), 10, 300, CHOICES))).toEqual([
      ["reports.varies", false],
      ["reports.seldom", true],
      ["reports.near_timeout", true],
    ]);
  });

  it("tell when nothing is known yet", () => {
    expect(keys(reportLines(reports({ updates: 0, update_interval_s: null }), 10, 300, CHOICES))).toEqual([["reports.no_updates", false]]);
    expect(keys(reportLines(reports({ updates: 3, update_interval_s: null }), 10, 300, CHOICES))).toEqual([["reports.not_known", false]]);
  });

  it("tell that updates without an update interval are uneven", () => {
    expect(keys(reportLines(reports({ updates: 5, update_interval_s: null, steady: false, longest_silence_s: 82.5 }), 10, 300, CHOICES))).toEqual([
      ["reports.varies", false],
      ["reports.seldom", true],
    ]);
  });
});

describe("report text", () => {
  it("shows whole numbers without decimals and the others with one, in the user's language", () => {
    const [line] = reportLines(reports(), 10, 300, CHOICES);
    expect(reportText(line, localizer("nb"), "nb")).toBe("Rapporterer jevnt hvert 2,5 s: 4 målinger per reguleringsvindu, med en beslutning rett etter den siste.");
  });
});
