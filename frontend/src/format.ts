/** Format a number with a fixed number of decimals in the user's language. */
export function formatNumber(language: string, value: number, decimals: number): string {
  return new Intl.NumberFormat(language, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Format a power in kW with two decimals, or a dash when it is not known. */
export function formatPower(language: string, kilowatt: number | null): string {
  return kilowatt === null ? "–" : formatNumber(language, kilowatt, 2);
}

/** Format the time left until a moment as m:ss, or h:mm:ss for an hour or more. */
export function formatTimeLeft(until: string, now: number): string {
  const seconds = Math.max(0, Math.ceil((Date.parse(until) - now) / 1000));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = String(seconds % 60).padStart(2, "0");
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, "0")}:${rest}` : `${minutes}:${rest}`;
}
