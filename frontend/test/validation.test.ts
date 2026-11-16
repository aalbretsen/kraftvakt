/** The checks of the draft, which mirror what the backend validates and finds missing. */
import { describe, expect, it } from "vitest";
import type { Charger, KraftvaktConfig } from "../src/api";
import { draftErrors, isActionAvailable, isMissingAction, issuesFor, missingItems } from "../src/validation";
import { appliance, CAPABILITIES, charger, config, group, hass, state, variant } from "./builders";

const CLIMATE = state("heat", { hvac_modes: ["off", "heat"], min_temp: 7, max_temp: 35 });

function errors(draft: KraftvaktConfig, states = {}) {
  return draftErrors(draft, CAPABILITIES, hass(states, draft.charger_groups.flatMap((item) => item.chargers)));
}

function chargerErrors(item: Charger) {
  return errors(config({ charger_groups: [group("garage", [item])] }));
}

describe("a complete configuration", () => {
  const complete = config({
    appliances: [appliance("heater", { variants: [variant("morning")] })],
    charger_groups: [group("garage", [charger("garage")])],
  });

  it("has no errors and nothing missing", () => {
    expect(errors(complete)).toEqual([]);
    expect(missingItems(complete)).toEqual([]);
  });
});

describe("missing items", () => {
  it("are the power sensor, the entities, the actions and the conditions", () => {
    const draft = config({
      general: { ...config().general, power_sensor: null },
      appliances: [
        appliance("heater", {
          entity_id: null,
          turn_on: { mode: "custom", action: [] },
          turn_off: { mode: "domain", domain_action: "climate_hvac_mode", data: { hvac_mode: null } },
          variants: [variant("morning", { condition: { type: "template", value: " " }, actions: { turn_on: null } })],
        }),
      ],
      charger_groups: [
        group("garage", [
          charger("garage", { device_id: null, set_current: { mode: "entity", entity_id: null }, actively_charging: null, car_connected: null }),
        ]),
      ],
    });
    expect(missingItems(draft)).toEqual([
      { code: "missing_power_sensor", section: "general", field: "power_sensor" },
      { code: "missing_entity", section: "appliances", target: "heater", field: "entity_id" },
      { code: "missing_action", section: "appliances", target: "heater", field: "turn_on" },
      { code: "missing_action", section: "appliances", target: "heater", field: "turn_off" },
      { code: "missing_action", section: "appliances", target: "heater", field: "variants.morning.turn_on" },
      { code: "missing_condition", section: "appliances", target: "heater", field: "variants.morning.condition" },
      { code: "missing_device", section: "chargers", target: "garage", field: "device_id" },
      { code: "missing_action", section: "chargers", target: "garage", field: "set_current" },
      { code: "missing_car_connected", section: "chargers", target: "garage", field: "car_connected" },
      { code: "missing_actively_charging", section: "chargers", target: "garage", field: "actively_charging" },
    ]);
  });

  it("include car connected also for a charger that may charge with others, without cloud control or charging window", () => {
    const draft = config({ charger_groups: [group("garage", [charger("garage", { car_connected: null })], { one_at_a_time: false })] });
    expect(missingItems(draft)).toEqual([{ code: "missing_car_connected", section: "chargers", target: "garage", field: "car_connected" }]);
  });

  it("an action that is set is not missing", () => {
    expect(isMissingAction({ mode: "custom", action: [{ action: "light.turn_on" }] })).toBe(false);
    expect(isMissingAction({ mode: "domain", domain_action: "climate_hvac_mode", data: { hvac_mode: "heat" } })).toBe(false);
  });
});

describe("settings", () => {
  it("are required in general, and checked against the backend's limits and resolution", () => {
    const general = { ...config().general, power_limit_w: Number.NaN, turn_on_margin_w: 0, wait_curve_steepness: 2.25 };
    expect(errors(config({ general }))).toEqual([
      { code: "required", section: "general", field: "power_limit_w" },
      { code: "out_of_range", section: "general", field: "turn_on_margin_w" },
      { code: "invalid_resolution", section: "general", field: "wait_curve_steepness" },
    ]);
  });

  it("of an appliance are optional", () => {
    expect(errors(config({ appliances: [appliance("heater", { power_reserve_w: null })] }))).toEqual([]);
    expect(errors(config({ appliances: [appliance("heater", { power_reserve_w: -1 })] }))).toEqual([
      { code: "out_of_range", section: "appliances", target: "heater", field: "power_reserve_w" },
    ]);
  });

  it("of a charger have no upper limit for the current, but min must not be above max", () => {
    expect(chargerErrors(charger("garage", { max_current_a: 80, min_current_a: 6 }))).toEqual([]);
    expect(chargerErrors(charger("garage", { min_current_a: 20 }))).toEqual([
      { code: "min_current_above_max", section: "chargers", target: "garage", field: "min_current_a" },
    ]);
  });
});

describe("names and labels", () => {
  it("of groups are not empty and unique, without surrounding spaces", () => {
    const groups = [group("a", [], { name: " " }), group("b", [], { name: "Garage" }), group("c", [], { name: "Garage " })];
    expect(errors(config({ charger_groups: groups }))).toEqual([
      { code: "empty_name", section: "charger_groups", target: "a", field: "name" },
      { code: "duplicate_name", section: "charger_groups", target: "b", field: "name" },
      { code: "duplicate_name", section: "charger_groups", target: "c", field: "name" },
    ]);
  });

  it("of variants are not empty and unique in the appliance", () => {
    const variants = [variant("a", { label: "" }), variant("b", { label: "Morning" }), variant("c", { label: "Morning" })];
    expect(errors(config({ appliances: [appliance("heater", { variants })] }))).toEqual([
      { code: "empty_label", section: "appliances", target: "heater", field: "variants.a.label" },
      { code: "duplicate_label", section: "appliances", target: "heater", field: "variants.b.label" },
      { code: "duplicate_label", section: "appliances", target: "heater", field: "variants.c.label" },
    ]);
  });
});

describe("charging window", () => {
  it.each([
    [{ start: "", end: "06:00" }, "invalid_time"],
    [{ start: "06:00", end: "06:00" }, "window_start_equals_end"],
  ])("%o is an error: %s", (window, code) => {
    expect(chargerErrors(charger("garage", { charging_window: window }))).toEqual([
      { code, section: "chargers", target: "garage", field: "charging_window" },
    ]);
  });
});

describe("the device of a charger", () => {
  it("is not checked before it is chosen", () => {
    expect(chargerErrors(charger("garage", { device_id: null }))).toEqual([]);
  });

  it("must exist", () => {
    const item = charger("garage");
    const draft = config({ charger_groups: [group("garage", [item])] });
    expect(draftErrors(draft, CAPABILITIES, hass())).toEqual([
      { code: "unknown_device", section: "chargers", target: "garage", field: "device_id" },
    ]);
  });

  it("holds every entity the charger names, but templates are not checked", () => {
    const item = charger("garage", { car_connected: { type: "template", value: "{{ true }}" } });
    const onDevice = hass({}, [item]);
    const elsewhere = { ...onDevice, entities: { ...onDevice.entities, "number.garage_current": { entity_id: "number.garage_current", device_id: "other" } } };
    expect(draftErrors(config({ charger_groups: [group("garage", [item])] }), CAPABILITIES, elsewhere)).toEqual([
      { code: "entity_not_on_device", section: "chargers", target: "garage", field: "set_current" },
    ]);
  });
});

describe("actions", () => {
  it("default needs a domain with a default action", () => {
    expect(errors(config({ appliances: [appliance("heater", { entity_id: "sensor.heater" })] }))).toEqual([
      { code: "default_action_unavailable", section: "appliances", target: "heater", field: "turn_on" },
      { code: "default_action_unavailable", section: "appliances", target: "heater", field: "turn_off" },
    ]);
  });

  it("of a domain belongs to the domain of the entity, also when a variant overrides it", () => {
    const hvacMode = { mode: "domain", domain_action: "climate_hvac_mode", data: { hvac_mode: "heat" } } as const;
    const heater = appliance("heater", { turn_on: hvacMode, variants: [variant("morning", { actions: { turn_off: hvacMode } })] });
    expect(errors(config({ appliances: [heater] }))).toEqual([
      { code: "domain_action_unavailable", section: "appliances", target: "heater", field: "turn_on" },
      { code: "domain_action_unavailable", section: "appliances", target: "heater", field: "variants.morning.turn_off" },
    ]);
  });

  it("of a domain has every parameter, with a value the entity supports", () => {
    const heater = appliance("heater", {
      entity_id: "climate.heater",
      turn_on: { mode: "domain", domain_action: "climate_hvac_mode_and_temperature", data: { hvac_mode: "auto", temperature: 40 } },
      turn_off: { mode: "domain", domain_action: "climate_hvac_mode_and_temperature", data: { hvac_mode: null } },
    });
    expect(errors(config({ appliances: [heater] }), { "climate.heater": CLIMATE })).toEqual([
      { code: "unsupported_option", section: "appliances", target: "heater", field: "turn_on.hvac_mode" },
      { code: "outside_entity_range", section: "appliances", target: "heater", field: "turn_on.temperature" },
      { code: "required", section: "appliances", target: "heater", field: "turn_off.temperature" },
    ]);
  });

  it("are not checked before the entity is chosen, and a custom action is always available", () => {
    expect(errors(config({ appliances: [appliance("heater", { entity_id: null })] }))).toEqual([]);
    expect(isActionAvailable(CAPABILITIES, "appliances", "turn_on", "sensor.heater", { mode: "custom", action: [] })).toBe(true);
    expect(isActionAvailable(CAPABILITIES, "appliances", "turn_on", null, { mode: "default" })).toBe(false);
  });
});

describe("issues for an item", () => {
  it("are those of its section and target", () => {
    const issues = errors(config({ appliances: [appliance("a", { entity_id: "sensor.a" }), appliance("b", { entity_id: "sensor.b" })] }));
    expect(issuesFor(issues, "appliances", "b").map((issue) => issue.target)).toEqual(["b", "b"]);
  });
});
