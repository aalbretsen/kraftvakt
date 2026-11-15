import { describe, expect, it } from "vitest";
import { pageForPath, showMoreInfo } from "../src/navigation";

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

describe("the more-info dialog", () => {
  it("is asked for with an event that reaches Home Assistant outside the panel's shadow DOM", () => {
    const element = new EventTarget();
    const events: CustomEvent[] = [];
    element.addEventListener("hass-more-info", (event) => events.push(event as CustomEvent));
    showMoreInfo(element, "switch.heater");
    expect(events.map((event) => [event.detail, event.bubbles, event.composed])).toEqual([[{ entityId: "switch.heater" }, true, true]]);
  });
});
