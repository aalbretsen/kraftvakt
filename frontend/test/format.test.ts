import { describe, expect, it, vi } from "vitest";
import { formatClockTime, formatDateTime, formatDuration, formatEnergy, formatMinutes, formatMoment, formatNumber, formatPercent, formatPower, timeLocale } from "../src/format";
import type { HomeAssistant } from "../src/types";

describe("formatting", () => {
  const GB = { language: "en-GB" };
  it("shows power and energy in kilo with two decimals in the user's language, and a dash for an unknown power", () => {
    expect(formatPower("en", 1500)).toBe("1.50");
    expect(formatPower("nb", 1500)).toBe("1,50");
    expect(formatPower("en", null)).toBe("–");
    expect(formatEnergy("en", 2345)).toBe("2.35");
    expect(formatNumber("en", 3, 1)).toBe("3.0");
  });

  it("shows durations as minutes and whole seconds", () => {
    expect(formatMinutes(375)).toBe("6:15");
    expect(formatMinutes(59.6)).toBe("1:00");
    expect(formatMinutes(null)).toBe("–");
  });

  it("shows shares as whole percentages", () => {
    expect(formatPercent("en", 0.504)).toBe("50%");
  });

  it("shows a moment as its clock time today, and with its date on another day", () => {
    const today = new Date(2026, 0, 5, 18, 0, 0);
    const morning = new Date(2026, 0, 5, 7, 30, 0).toISOString();
    const yesterday = new Date(2026, 0, 4, 7, 30, 0).toISOString();

    expect(formatClockTime(GB, morning)).toBe("07:30:00");
    expect(formatMoment(GB, morning, today)).toBe("07:30:00");
    expect(formatMoment(GB, yesterday, today)).toBe("04/01/2026, 07:30:00");
  });

  it("shows how long something has lasted in its largest whole unit, rounded down", () => {
    const minute = 60_000;
    expect(formatDuration("en", 0)).toBe("0 minutes");
    expect(formatDuration("en", 5 * minute + 59_000)).toBe("5 minutes");
    expect(formatDuration("en", 70 * minute)).toBe("1 hour");
    expect(formatDuration("en", ((20 * 24 + 7) * 60 + 15) * minute)).toBe("20 days");
    expect(formatDuration("nb", 24 * 60 * minute)).toBe("1 døgn");
  });

  it("shows a date and time without seconds", () => {
    expect(formatDateTime(GB, new Date(2026, 9, 22, 20, 57, 22).toISOString())).toBe("22/10/2026, 20:57");
  });
});

describe("times in the user's profile", () => {
  const moment = "2026-11-23T21:05:30Z";

  function profile(time_zone: "local" | "server", time_format: "language" | "system" | "12" | "24"): HomeAssistant {
    return { locale: { language: "en-GB", time_zone, time_format }, config: { time_zone: "Asia/Tokyo" } } as unknown as HomeAssistant;
  }

  it("are in the server's time zone when the user chose it", () => {
    expect(formatClockTime(timeLocale(profile("server", "language")), moment)).toBe("06:05:30");
    expect(formatMoment(timeLocale(profile("server", "language")), moment, new Date("2026-11-23T10:00:00Z"))).toBe("24/11/2026, 06:05:30");
  });

  it("have a 12-hour or a 24-hour clock when the user chose one", () => {
    expect(formatClockTime(timeLocale(profile("server", "12")), moment, false)).toBe("06:05 am");
    expect(formatClockTime(timeLocale({ ...profile("server", "24"), locale: { language: "en-US", time_zone: "server", time_format: "24" } } as HomeAssistant), moment, false)).toBe(
      "06:05",
    );
  });

  it("have the clock of the system when the user chose it", () => {
    const resolvedOptions = vi.spyOn(Intl.DateTimeFormat.prototype, "resolvedOptions");
    resolvedOptions.mockReturnValueOnce({ hour12: true } as Intl.ResolvedDateTimeFormatOptions);
    expect(timeLocale(profile("local", "system")).hourCycle).toBe("h12");
    resolvedOptions.mockReturnValueOnce({ hour12: false } as Intl.ResolvedDateTimeFormatOptions);
    expect(timeLocale(profile("local", "system")).hourCycle).toBe("h23");
    resolvedOptions.mockRestore();
  });

  it("are in the browser's time zone with the language's clock by default", () => {
    expect(timeLocale(profile("local", "language"))).toEqual({ language: "en-GB", timeZone: undefined, hourCycle: undefined });
  });
});
