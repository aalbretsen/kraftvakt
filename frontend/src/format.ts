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

/** Format a duration in seconds as minutes and whole seconds, like 6:15, or a dash when it is not known. */
export function formatMinutes(seconds: number | null): string {
  if (seconds === null) {
    return "–";
  }
  const whole = Math.round(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

/** Format a share between 0 and 1 as a whole percentage, like 50 %, in the user's language. */
export function formatPercent(language: string, share: number): string {
  return new Intl.NumberFormat(language, { style: "percent", maximumFractionDigits: 0 }).format(share);
}

/** Format an energy given in Wh as kWh with two decimals. */
export function formatEnergy(language: string, wattHours: number): string {
  return formatNumber(language, wattHours / 1000, 2);
}

/** Format the clock time of a moment, like 14:05:30, in the user's language. */
export function formatClockTime(language: string, moment: string): string {
  return new Date(moment).toLocaleTimeString(language);
}

/** Format a moment as its clock time when it is today, and with its date before otherwise, in the user's language. */
export function formatMoment(language: string, moment: string, today = new Date()): string {
  const date = new Date(moment);
  return date.toDateString() === today.toDateString() ? date.toLocaleTimeString(language) : date.toLocaleString(language);
}

/** Format a moment as its date and time without seconds, like 22.10.2026, 20:57, in the user's language. */
export function formatDateTime(language: string, moment: string): string {
  return new Date(moment).toLocaleString(language, { dateStyle: "short", timeStyle: "short" });
}

/** Format a duration in ms with its two largest units, days and hours, hours and minutes, or minutes, in the user's language. */
export function formatDuration(language: string, milliseconds: number): string {
  const minutes = Math.floor(milliseconds / 60_000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const unit = (value: number, name: "day" | "hour" | "minute") => new Intl.NumberFormat(language, { style: "unit", unit: name, unitDisplay: "long" }).format(value);
  if (days > 0) {
    return `${unit(days, "day")} ${unit(hours % 24, "hour")}`;
  }
  if (hours > 0) {
    return `${unit(hours, "hour")} ${unit(minutes % 60, "minute")}`;
  }
  return unit(minutes, "minute");
}
