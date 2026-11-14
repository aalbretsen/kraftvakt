import { describe, expect, it } from "vitest";
import { actionForEntity } from "../src/actions";
import type { ActionConfig } from "../src/api";
import { CAPABILITIES, state } from "./builders";

const forEntity = (field: string, action: ActionConfig | null, entityId: string | null, attributes?: Record<string, unknown>) =>
  actionForEntity(CAPABILITIES, "appliances", field, action, entityId, attributes && state("heat", attributes));

describe("a thermostat that is not set up yet", () => {
  it("gets its HVAC mode set, with the modes it supports", () => {
    const thermostat = { hvac_modes: ["off", "heat", "auto"] };
    expect(forEntity("turn_on", null, "climate.hall", thermostat)).toEqual({
      mode: "domain",
      domain_action: "climate_hvac_mode",
      data: { hvac_mode: "heat" },
    });
    expect(forEntity("turn_off", null, "climate.hall", thermostat)).toEqual({
      mode: "domain",
      domain_action: "climate_hvac_mode",
      data: { hvac_mode: "off" },
    });
  });

  it("without off is turned off to auto, and without either the mode is left for the user", () => {
    expect(forEntity("turn_off", null, "climate.hall", { hvac_modes: ["heat", "auto"] })).toMatchObject({ data: { hvac_mode: "auto" } });
    expect(forEntity("turn_off", null, "climate.hall", { hvac_modes: ["heat"] })).toMatchObject({ data: { hvac_mode: null } });
  });

  it("whose state is not known gets the first preferred mode", () => {
    expect(forEntity("turn_on", null, "climate.hall")).toMatchObject({ data: { hvac_mode: "heat" } });
  });
});

describe("other entities", () => {
  it("get the default action when their domain has one, and nothing otherwise", () => {
    expect(forEntity("turn_on", null, "switch.heater")).toEqual({ mode: "default" });
    expect(forEntity("turn_on", null, "sensor.heater")).toBeNull();
    expect(forEntity("turn_on", null, null)).toBeNull();
  });
});

describe("an action that is set", () => {
  it("is kept while it is available for the new entity", () => {
    const custom: ActionConfig = { mode: "custom", action: [{ action: "light.turn_on" }] };
    expect(forEntity("turn_on", { mode: "default" }, "climate.hall")).toEqual({ mode: "default" });
    expect(forEntity("turn_on", custom, "sensor.heater")).toEqual(custom);
  });

  it("becomes an empty custom action when it is not available for the new entity", () => {
    const hvacMode: ActionConfig = { mode: "domain", domain_action: "climate_hvac_mode", data: { hvac_mode: "heat" } };
    expect(forEntity("turn_on", hvacMode, "switch.heater")).toEqual({ mode: "custom", action: [] });
    expect(forEntity("turn_on", { mode: "default" }, "sensor.heater")).toEqual({ mode: "custom", action: [] });
  });
});
