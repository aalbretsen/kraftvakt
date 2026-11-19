// The same choices as regulation_window_options in config_model.py; keep the two in step.
import type { Capabilities, GeneralConfig } from "./api";

type WindowLimits = Capabilities["regulation_window"];

/**
 * Return the numbers of updates a regulation window may have, for a power sensor that reports every `intervalS` seconds:
 * multiples of the fewest updates that last the shortest window, as many as the choices allow within the longest window.
 */
export function regulationWindowOptions(intervalS: number, limits: WindowLimits): number[] {
  const shortest = limits.seconds.min ?? 0;
  const longest = limits.seconds.max ?? shortest;
  const fewest = Math.max(1, Math.ceil(shortest / intervalS - 1e-9));
  return Array.from({ length: limits.choices }, (_, index) => fewest * (index + 1)).filter((updates) => updates * intervalS <= longest + 1e-9);
}

/** Return the option whose window is closest to `seconds`, the shorter one when two are as close, or null when there is none. */
export function closestWindowUpdates(seconds: number, intervalS: number, limits: WindowLimits): number | null {
  const options = regulationWindowOptions(intervalS, limits);
  return options.reduce<number | null>(
    (best, updates) => (best === null || Math.abs(updates * intervalS - seconds) < Math.abs(best * intervalS - seconds) - 1e-9 ? updates : best),
    null,
  );
}

/** Return how long a regulation window lasts when the power sensor reports at its interval, or null while either is not set. */
export function windowSeconds(general: GeneralConfig): number | null {
  const { regulation_window_updates: updates, power_sensor_interval_s: interval } = general;
  return updates === null || interval === null ? null : updates * interval;
}
