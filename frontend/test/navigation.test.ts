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
  /** A row or tile that opens the dialog for its entity when it gets the event, as `type` with `detail`. */
  function activate(type: string, detail: number) {
    const element = Object.assign(new EventTarget(), { blurred: false, blur: () => (element.blurred = true) });
    const requests: CustomEvent[] = [];
    element.addEventListener("hass-more-info", (event) => requests.push(event as CustomEvent));
    element.addEventListener(type, (event) => showMoreInfo(event, "switch.heater"));
    element.dispatchEvent(new CustomEvent(type, { detail }));
    return { requests, blurred: element.blurred };
  }

  it("is asked for with an event that reaches Home Assistant outside the panel's shadow DOM", () => {
    const { requests } = activate("click", 1);
    expect(requests.map((event) => [event.detail, event.bubbles, event.composed])).toEqual([[{ entityId: "switch.heater" }, true, true]]);
  });

  it.each([
    ["a mouse click", "click", 1, true],
    ["Enter or Space on a button", "click", 0, false],
    ["a key press", "keydown", 0, false],
  ])("from %s takes the focus from the element: %s", (_how, type, detail, blurred) => {
    expect(activate(type, detail).blurred).toBe(blurred);
  });
});
