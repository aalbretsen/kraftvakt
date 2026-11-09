// The same curve as WaitingCurve in regulation/waiting.py, so the panel can
// show it while the settings are changed; keep the two in step.
const WAITING_STARTS_AT_UTILIZATION = 0.5;
const SHARE_AT_PIVOT = 0.8;
const PIVOT_CAP_FACTOR = 0.999;

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
