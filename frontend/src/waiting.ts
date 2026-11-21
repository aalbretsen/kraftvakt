// The same waiting times as in regulation/waiting.py, so the panel can show
// them while the settings are changed; keep the two in step.
const WAITING_STARTS_AT_UTILIZATION = 0.5;
const SHARE_AT_PIVOT = 0.8;
const PIVOT_CAP_FACTOR = 0.999;

/** The first time a step is turned on, and the first time again, follow the curve. */
export const CURVE_TURN_ONS = 2;

function aboveStart(utilization: number): number {
  const span = 1 - WAITING_STARTS_AT_UTILIZATION;
  return Math.min(1, Math.max(0, (utilization - WAITING_STARTS_AT_UTILIZATION) / span));
}

/** Return the share of the waiting time at the limit, 0 to 1, by utilization of the limit. */
export function waitingCurve(steepness: number, pivotPercent: number): (utilization: number) => number {
  const pivot = Math.min(aboveStart(pivotPercent / 100), SHARE_AT_PIVOT ** (1 / steepness) * PIVOT_CAP_FACTOR);
  const pivotPower = pivot ** steepness;
  const shape = (pivotPower * (1 - SHARE_AT_PIVOT)) / (SHARE_AT_PIVOT - pivotPower);
  return (utilization) => {
    const power = aboveStart(utilization) ** steepness;
    return power === 0 ? 0 : (power * (1 + shape)) / (power + shape);
  };
}

/**
 * Return the waiting time in seconds of a turn-on after the first ones that follow the curve,
 * by its number in a row: it grows by one increment each time, up to the chosen number of increments.
 */
export function repeatedTurnOnWaiting(turnOn: number, waitAtLimit: number, incrementFactor: number, increments: number): number {
  const increment = waitAtLimit * incrementFactor;
  return waitAtLimit + increment * Math.min(increments, turnOn - CURVE_TURN_ONS - 1);
}

/**
 * Return how long a step actually waits: its waiting time is rounded to whole
 * seconds, half up, and it is turned on at the first decision after that has
 * passed, with decisions every `decisionInterval` seconds.
 */
export function untilDecision(waiting: number, decisionInterval: number): number {
  return Math.max(0, Math.ceil(Math.round(waiting) / decisionInterval - 1e-9)) * decisionInterval;
}
