import { describe, expect, it } from "vitest";
import type { DomainAction } from "../src/api";
import { domainActionsFor, initialData, parameterOptions, parameterRange } from "../src/domain-actions";
import { CAPABILITIES, state } from "./builders";

const actions = (field: "turn_on" | "turn_off") => domainActionsFor(CAPABILITIES, field, "climate.heater");
const HVAC_MODE_AND_TEMPERATURE: DomainAction = actions("turn_off").climate_hvac_mode_and_temperature;
const [HVAC_MODE, TEMPERATURE] = HVAC_MODE_AND_TEMPERATURE.parameters;

describe("domain actions", () => {
  it("are those of the entity's domain", () => {
    expect(Object.keys(actions("turn_on"))).toEqual(["climate_hvac_mode", "climate_temperature", "climate_hvac_mode_and_temperature"]);
    expect(domainActionsFor(CAPABILITIES, "turn_on", "switch.heater")).toEqual({});
  });

  it("start with the first preferred option the entity supports, the default temperature, or the values chosen before", () => {
    const heatOnly = state("heat", { hvac_modes: ["heat", "auto"] });
    expect(initialData(HVAC_MODE_AND_TEMPERATURE, heatOnly)).toEqual({ hvac_mode: "auto", temperature: 0 });
    expect(initialData(HVAC_MODE_AND_TEMPERATURE, state("heat", { hvac_modes: ["heat"] }))).toEqual({ hvac_mode: null, temperature: 0 });
    expect(initialData(HVAC_MODE_AND_TEMPERATURE, undefined, { temperature: 8 })).toEqual({ hvac_mode: "off", temperature: 8 });
  });

  it("offer the options of the entity, or the preferred ones when it does not tell", () => {
    expect(parameterOptions(HVAC_MODE, state("heat", { hvac_modes: ["off", "heat", "cool"] }))).toEqual(["off", "heat", "cool"]);
    expect(parameterOptions(HVAC_MODE, undefined)).toEqual(["off", "auto"]);
  });

  it("read the range of a temperature from the entity", () => {
    expect(parameterRange(TEMPERATURE, state("heat", { min_temp: 7, max_temp: 35, target_temp_step: "0.5" }))).toEqual({
      min: 7,
      max: 35,
      step: undefined,
    });
  });
});
