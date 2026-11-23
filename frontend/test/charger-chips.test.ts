import * as icons from "@mdi/js";
import { describe, expect, it } from "vitest";
import type { ChargerState } from "../src/api";
import { CHARGER_CHIPS, type ChipKind, chargerChip } from "../src/charger-chips";
import { formatClockTime } from "../src/format";
import { chargerStatus } from "./builders";
import chargerStates from "./fixtures/charger_states.json";

/** The colour of the state sensor that each kind of chip stands for. */
const SENSOR_COLORS: Record<ChipKind, string> = { on: "green", off: "grey", outline: "grey", alarm: "red", info: "light-blue", waiting: "amber" };

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

describe("the chip of an EV charger", () => {
  const startingUntil = "2026-11-23T12:03:00+00:00";

  it("tells when the start delay of a starting EV charger ends", () => {
    const chip = chargerChip(chargerStatus("c", { state: "starting", activated: true, current_a: 6, starting_until: startingUntil }), "en", null, false);
    expect(chip.sentence).toBe("status.starting_until");
    expect(chip.sentenceParams).toEqual({ time: formatClockTime("en", startingUntil) });
  });

  it("tells the current of an EV charger that charges within its start delay", () => {
    const charging = chargerStatus("c", { state: "charging", activated: true, charging: true, current_a: 6, starting_until: startingUntil });
    const chip = chargerChip(charging, "en", null, false);
    expect(chip.sentence).toBe("status.charging_at");
    expect(chip.sentenceParams).toEqual({ current: 6 });
  });

  it("shows the charging window short in the word and in full in the sentence", () => {
    const chip = chargerChip(chargerStatus("c", { state: "outside_window" }), "en", { start: "22:00", end: "06:30" }, false);
    expect(chip.wordParams).toEqual({ start: "22", end: "06:30" });
    expect(chip.sentenceParams).toEqual({ start: "22:00", end: "06:30" });
  });

  it("tells a queued EV charger of a group that shares the power that it waits for room", () => {
    expect(chargerChip(chargerStatus("c", { state: "queued" }), "en", null, true).sentence).toBe("status.queued_for_room");
    expect(chargerChip(chargerStatus("c", { state: "queued" }), "en", null, false).sentence).toBe("status.waiting_charger");
  });
});
