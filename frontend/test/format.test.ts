import { describe, expect, it } from "vitest";
import { formatEnergy, formatMinutes, formatNumber, formatPercent, formatPower } from "../src/format";

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
});
