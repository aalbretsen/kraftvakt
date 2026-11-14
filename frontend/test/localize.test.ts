import { describe, expect, it } from "vitest";
import { localizer } from "../src/localize";

describe("translations", () => {
  it("follow the language, its base language, or English", () => {
    expect(localizer("nb")("tabs.general")).toBe("Generelt");
    expect(localizer("nb-NO")("tabs.general")).toBe("Generelt");
    expect(localizer("de")("tabs.general")).toBe("General");
  });

  it("fill in the parameters they are given and keep the others", () => {
    expect(localizer("en")("errors.at_least", { min: 5 })).toContain("5");
    expect(localizer("en")("errors.at_least")).toContain("{min}");
  });
});
