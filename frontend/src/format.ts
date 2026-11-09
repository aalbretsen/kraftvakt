/** Format a number with a fixed number of decimals in the user's language. */
export function formatNumber(language: string, value: number, decimals: number): string {
  return new Intl.NumberFormat(language, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Format a power given in W as kW with two decimals, or a dash when it is not known. */
export function formatPower(language: string, watt: number | null): string {
  return watt === null ? "–" : formatNumber(language, watt / 1000, 2);
}

/** Format an energy given in Wh as kWh with two decimals. */
export function formatEnergy(language: string, wattHours: number): string {
  return formatNumber(language, wattHours / 1000, 2);
}

/** Format the clock time of a moment, like 14:05:30, in the user's language. */
export function formatClockTime(language: string, moment: string): string {
  return new Date(moment).toLocaleTimeString(language);
}
