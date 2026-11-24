import { describe, expect, it } from "vitest";
import type { ConfigResponse, Issue } from "../src/api";
import { describeIssue, errorsByField, fieldErrorText, pageForIssue } from "../src/issues";
import { localizer } from "../src/localize";
import { appliance, CAPABILITIES, charger, config, group, hass, variant } from "./builders";

const localize = localizer("en");

describe("the page of an issue", () => {
  it.each([
    [{ code: "required", section: "general", field: "power_limit_w" }, "general"],
    [{ code: "required", section: "general", field: "action_timeout_s" }, "advanced"],
    [{ code: "missing_action", section: "appliances", target: "a", field: "turn_on" }, "appliances"],
    [{ code: "duplicate_entity", section: "priority" }, "appliances"],
    [{ code: "empty_name", section: "charger_groups", target: "g", field: "name" }, "charging"],
    [{ code: "missing_device", section: "chargers", target: "c", field: "device_id" }, "charging"],
  ] as [Issue, string][])("%o is %s", (issue, page) => {
    expect(pageForIssue(issue)).toBe(page);
  });
});

describe("a missing item", () => {
  const response: ConfigResponse = {
    config: config({
      appliances: [appliance("heater", { variants: [variant("morning", { label: "Morning" })] }), appliance("new", { entity_id: null })],
      charger_groups: [group("garage", [charger("garage")])],
    }),
    entity_names: { "switch.heater": "Water heater", "switch.garage": "Garage" },
    missing: [],
  };
  const missingText = (issue: Issue) => describeIssue(issue, response, localize, hass());

  it("names the appliance or charger, the variant and the action", () => {
    const variantAction = missingText({ code: "missing_action", section: "appliances", target: "heater", field: "variants.morning.turn_on" });
    expect(variantAction).toContain("Water heater «Morning»");
    expect(variantAction).toContain(localize("missing.actions.turn_on"));
    expect(missingText({ code: "missing_charging_power", section: "chargers", target: "garage", field: "charging_power" })).toContain("Garage");
  });

  it("names the group of EV chargers, or tells that it has no name", () => {
    expect(missingText({ code: "missing_condition", section: "charger_groups", target: "garage", field: "one_at_a_time" })).toContain("garage");
    expect(missingText({ code: "missing_condition", section: "charger_groups", target: "other", field: "one_at_a_time" })).toContain(localize("charging.unnamed_group"));
  });

  it("names an appliance without an entity, and a charger without a device or an on/off entity, by what it is", () => {
    const issue: Issue = { code: "missing_action", section: "appliances", target: "new", field: "turn_off" };
    expect(missingText(issue)).toContain(localize("missing.appliance_without_entity"));
    expect(missingText({ code: "missing_device", section: "chargers", target: "other", field: "device_id" })).toContain(localize("missing.charger_without_device"));
  });

  it("with a code the panel does not know shows the code", () => {
    expect(missingText({ code: "something_new", section: "general" })).toContain("something_new");
  });
});

describe("the error at a field", () => {
  const text = (issue: Issue) => fieldErrorText(issue, localize, CAPABILITIES, "en");

  it("gives the range from the capabilities", () => {
    expect(text({ code: "out_of_range", section: "general", field: "power_limit_w" })).toBe(localize("errors.out_of_range", { min: "1,000", max: "50,000" }));
    expect(text({ code: "out_of_range", section: "chargers", target: "c", field: "max_current_a" })).toBe(localize("errors.at_least", { min: "1" }));
    expect(text({ code: "invalid_resolution", section: "general", field: "wait_curve_steepness" })).toBe(localize("errors.invalid_resolution", { resolution: "0.5" }));
  });

  it("has a text for each code, and shows a code it does not know", () => {
    expect(text({ code: "missing_car_connected", section: "chargers", target: "c", field: "car_connected" })).toBe(localize("errors.required"));
    expect(text({ code: "missing_fault_flag", section: "chargers", target: "c", field: "fault_flag" })).toBe(localize("errors.fault_flag_required"));
    expect(text({ code: "something_new", section: "general", field: "power_limit_w" })).toBe(localize("errors.unknown", { code: "something_new" }));
  });

  it("is given per field under a prefix, the first issue of each field", () => {
    const issues: Issue[] = [
      { code: "first", section: "chargers", field: "charging_window" },
      { code: "second", section: "chargers", field: "charging_window" },
      { code: "other", section: "chargers", field: "turn_on.hvac_mode" },
      { code: "outside", section: "chargers", field: "name" },
    ];
    expect(errorsByField(issues, "", (issue) => issue.code)).toEqual({ charging_window: "first", "turn_on.hvac_mode": "other", name: "outside" });
    expect(errorsByField(issues, "turn_on.", (issue) => issue.code)).toEqual({ hvac_mode: "other" });
  });
});
