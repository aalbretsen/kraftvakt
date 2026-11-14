import { describe, expect, it } from "vitest";
import type { PriorityEntry } from "../src/api";
import { allChargers, moveItem, newId, priorityKey, sameConfig, withCompletePriority } from "../src/draft";
import { appliance, charger, config, group, variant } from "./builders";

const entry = (applianceId: string, variantId: string | null = null): PriorityEntry => ({
  type: "appliance",
  appliance_id: applianceId,
  variant_id: variantId,
});
const groupEntry = (groupId: string): PriorityEntry => ({ type: "charger_group", group_id: groupId });

describe("the priority list", () => {
  it("is completed as the backend does: unknown and repeated entries are left out, and missing ones are added at the bottom", () => {
    const draft = config({
      appliances: [appliance("heater", { variants: [variant("morning")] }), appliance("pool")],
      charger_groups: [group("garage", [])],
      priority: [entry("pool"), entry("gone"), entry("heater", "morning"), entry("pool")],
    });
    expect(withCompletePriority(draft).priority.map(priorityKey)).toEqual(["pool/", "heater/morning", "heater/", "group/garage"]);
  });

  it("moves an item as ha-sortable reports it", () => {
    expect(moveItem(["a", "b", "c"], 0, 2)).toEqual(["b", "c", "a"]);
    expect(moveItem(["a", "b", "c"], 2, 0)).toEqual(["c", "a", "b"]);
  });

  it("has distinct keys for an appliance, its variant and a group", () => {
    expect([entry("a"), entry("a", "b"), groupEntry("a")].map(priorityKey)).toEqual(["a/", "a/b", "group/a"]);
  });
});

describe("the draft", () => {
  it("is the same as another with the same content", () => {
    expect(sameConfig(config(), config())).toBe(true);
    expect(sameConfig(config(), config({ appliances: [appliance("heater")] }))).toBe(false);
  });

  it("gets new ids of twelve hexadecimal digits", () => {
    expect(newId()).toMatch(/^[0-9a-f]{12}$/);
    expect(newId()).not.toBe(newId());
  });

  it("has the chargers of every group", () => {
    const draft = config({ charger_groups: [group("a", [charger("x")]), group("b", [charger("y"), charger("z")])] });
    expect(allChargers(draft).map((item) => item.id)).toEqual(["x", "y", "z"]);
  });
});
