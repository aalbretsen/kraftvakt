import { describe, expect, it } from "vitest";
import { pageForPath } from "../src/navigation";

describe("pages", () => {
  it.each([
    ["/advanced", "advanced"],
    ["/charging/extra", "charging"],
    ["", "status"],
    ["/unknown", "status"],
  ])("%s shows the page %s", (path, page) => {
    expect(pageForPath(path)).toBe(page);
  });
});
