import type { HomeAssistant } from "./types";

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

/** How times are shown: in the user's language, time zone and clock, as in the rest of Home Assistant. Without a time zone, the browser's. */
export interface TimeLocale {
  language: string;
  timeZone?: string;
  hourCycle?: "h12" | "h23";
}

/** Return how times are shown from the user's profile in Home Assistant. */
export function timeLocale(hass: HomeAssistant): TimeLocale {
  const { language, time_zone, time_format } = hass.locale;
  const twelveHours = time_format === "system" ? new Intl.DateTimeFormat(undefined, { hour: "numeric" }).resolvedOptions().hour12 : time_format === "12";
  return {
    language,
    timeZone: time_zone === "server" ? hass.config.time_zone : undefined,
    hourCycle: time_format === "language" ? undefined : twelveHours ? "h12" : "h23",
  };
}

function options(locale: TimeLocale): Intl.DateTimeFormatOptions {
  return { timeZone: locale.timeZone, hourCycle: locale.hourCycle };
}

/** Format the clock time of a moment, like 14:05:30, or 14:05 without seconds. */
export function formatClockTime(locale: TimeLocale, moment: string | number, seconds = true): string {
  const parts: Intl.DateTimeFormatOptions = seconds ? {} : { hour: "2-digit", minute: "2-digit" };
  return new Date(moment).toLocaleTimeString(locale.language, { ...options(locale), ...parts });
}

/** Format a moment as its clock time when it is today, and with its date before otherwise. */
export function formatMoment(locale: TimeLocale, moment: string, today = new Date()): string {
  const date = new Date(moment);
  const day = (value: Date) => value.toLocaleDateString("en-CA", { timeZone: locale.timeZone });
  return day(date) === day(today) ? formatClockTime(locale, moment) : date.toLocaleString(locale.language, options(locale));
}

/** Format a moment as its date and time without seconds, like 22.10.2026, 20:57. */
export function formatDateTime(locale: TimeLocale, moment: string): string {
  return new Date(moment).toLocaleString(locale.language, { ...options(locale), dateStyle: "short", timeStyle: "short" });
}

/** Format a duration in ms as whole days, or else whole hours, or else whole minutes, rounded down, in the user's language. */
export function formatDuration(language: string, milliseconds: number): string {
  const minutes = Math.floor(milliseconds / 60_000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const [value, unit] = days > 0 ? [days, "day"] : hours > 0 ? [hours, "hour"] : [minutes, "minute"];
  return new Intl.NumberFormat(language, { style: "unit", unit, unitDisplay: "long" }).format(value);
}
