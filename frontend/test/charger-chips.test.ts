import * as icons from "@mdi/js";
import { describe, expect, it } from "vitest";
import type { ChargerState } from "../src/api";
import { CHARGER_CHIPS, type ChipKind } from "../src/charger-chips";
import chargerStates from "./fixtures/charger_states.json";

/** The colour of the state sensor that each kind of chip stands for. */
const SENSOR_COLORS: Record<ChipKind, string> = { on: "green", off: "grey", outline: "grey", alarm: "red", info: "light-blue" };

/** The path in `@mdi/js` of an icon named as in Home Assistant, such as `mdi:alert-circle-outline`. */
function iconPath(name: string): string | undefined {
  const words = name.replace("mdi:", "").split("-");
  return (icons as Record<string, string>)[`mdi${words.map((word) => word[0].toUpperCase() + word.slice(1)).join("")}`];
}

describe("EV charger chips", () => {
  it("cover the states of the state sensor, in the order the backend checks them", () => {
    expect(Object.keys(CHARGER_CHIPS)).toEqual(Object.keys(chargerStates));
  });

  it.each(Object.entries(chargerStates))("%s has the icon and colour of the state sensor", (state, { icon, color }) => {
    const [chip] = CHARGER_CHIPS[state as ChargerState];
    expect(chip.icon).toBeDefined();
    expect(chip.icon).toBe(iconPath(icon));
    expect(SENSOR_COLORS[chip.kind]).toBe(color);
  });
});
