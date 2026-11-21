import { describe, expect, it } from "vitest";
import { formatClockTime, formatEnergy, formatMinutes, formatMoment, formatNumber, formatPercent, formatPower } from "../src/format";

describe("formatting", () => {
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

    expect(formatClockTime("en-GB", morning)).toBe("07:30:00");
    expect(formatMoment("en-GB", morning, today)).toBe("07:30:00");
    expect(formatMoment("en-GB", yesterday, today)).toBe("04/01/2026, 07:30:00");
  });
});
