import type { PowerSensorReports, Range } from "./api";
import { formatNumber } from "./format";
import type { Localize, TranslationKey } from "./localize";

/** A line of the summary of how the power sensor reports. A warning tells the user what to change. */
export interface ReportLine {
  key: TranslationKey;
  params: Record<string, number>;
  warning: boolean;
}

/** Above this, a change in consumption can go unseen for a long time. */
const SELDOM_S = 60;

/** With more updates than this and no update interval, the updates are uneven: the same rule as ReportAnalysis.known in report_analysis.py. */
const FEWEST_INTERVALS = 3;

/** Return the lengths a regulation window may have, in seconds. */
export function windowChoices(limits: Range): number[] {
  const choices: number[] = [];
  for (let seconds = limits.min ?? limits.resolution; seconds <= (limits.max ?? seconds); seconds += limits.resolution) {
    choices.push(seconds);
  }
  return choices;
}

/** Return how many update intervals a regulation window lasts: the same rule as WindowClock in measurement.py. */
export function updatesPerWindow(windowS: number, intervalS: number): number {
  return Math.max(1, Math.floor(windowS / intervalS + 0.5));
}

/**
 * Return the summary of how the power sensor reports, for the regulation window and the power sensor timeout:
 * first how it reports and what that gives, then the warnings, each with what to change.
 */
export function reportLines(reports: PowerSensorReports, windowS: number, timeoutS: number, choices: number[]): ReportLine[] {
  const interval = reports.update_interval_s;
  const longest = reports.longest_silence_s;
  if (interval === null && reports.updates <= FEWEST_INTERVALS) {
    return [line(reports.updates === 0 ? "reports.no_updates" : "reports.not_known", { window: windowS })];
  }
  const lines: ReportLine[] = [];
  const warnings: ReportLine[] = [];
  if (interval !== null && reports.steady) {
    const updates = updatesPerWindow(windowS, interval);
    const seconds = round(updates * interval);
    if (interval > windowS * 1.25) {
      const choice = choices.find((length) => length >= interval) ?? choices[choices.length - 1];
      warnings.push(line("reports.longer_than_window", { interval, seconds, choice }, true));
    }
    const key = updates === 1 ? "reports.steady_one" : Math.abs(seconds - windowS) < 0.5 ? "reports.steady" : "reports.steady_longer";
    lines.push(line(key, { interval, updates, seconds }));
  } else {
    lines.push(line("reports.varies", { shortest: reports.shortest_s ?? 0, longest: longest ?? 0, window: windowS }));
  }
  if (longest !== null && longest > SELDOM_S) {
    warnings.push(line("reports.seldom", { longest }, true));
  }
  if (longest !== null && longest * 2 >= timeoutS) {
    warnings.push(line("reports.near_timeout", { longest, timeout: timeoutS }, true));
  }
  if (!reports.steady && warnings.length === 0) {
    lines.push(line("reports.steadier"));
  }
  return [...lines, ...warnings];
}

function line(key: TranslationKey, params: Record<string, number> = {}, warning = false): ReportLine {
  return { key, params, warning };
}

function round(seconds: number): number {
  return Math.round(seconds * 10) / 10;
}

/** Return the text of a line in the user's language, with whole numbers without decimals and the others with one. */
export function reportText(line: ReportLine, localize: Localize, language: string): string {
  const params = Object.fromEntries(Object.entries(line.params).map(([name, value]) => [name, formatNumber(language, value, Number.isInteger(value) ? 0 : 1)]));
  return localize(line.key, params);
}
