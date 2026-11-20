import { describe, expect, it } from "vitest";
import type { DomainAction } from "../src/api";
import { domainActionsFor, initialData, parameterIssues, parameterOptions, parameterRange, sourceTemperature } from "../src/domain-actions";
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

  it("check that a temperature source names an entity that gives a temperature, and leave one without an entity as missing", () => {
    const issues = (temperature: unknown) => parameterIssues(HVAC_MODE_AND_TEMPERATURE, { hvac_mode: "off", temperature } as never, undefined);
    expect(issues({ type: "temperature_sensor", value: "input_number.wanted" })).toEqual({});
    expect(issues({ type: "target_temperature", value: "climate.living_room" })).toEqual({});
    expect(issues({ type: "temperature_sensor", value: null })).toEqual({});
    expect(issues({ type: "temperature_sensor", value: "switch.heater" })).toEqual({ temperature: "unsupported_entity_domain" });
    expect(issues({ type: "current_temperature", value: "sensor.wanted" })).toEqual({ temperature: "not_a_thermostat" });
    expect(issues({ type: "template", value: "{{ 20 }}" })).toEqual({ temperature: "invalid_type" });
    expect(parameterIssues(HVAC_MODE_AND_TEMPERATURE, { hvac_mode: { type: "temperature_sensor", value: null }, temperature: 20 }, undefined)).toEqual({
      hvac_mode: "invalid_type",
    });
  });

  it("read the temperature of a source from the state of a sensor, or the attributes of a thermostat", () => {
    const thermostat = state("heat", { temperature: 22, current_temperature: 19.5 });
    expect(sourceTemperature({ type: "temperature_sensor", value: "input_number.wanted" }, state("21.5"))).toBe(21.5);
    expect(sourceTemperature({ type: "temperature_sensor", value: "sensor.wanted" }, state("unavailable"))).toBeNull();
    expect(sourceTemperature({ type: "temperature_sensor", value: "sensor.wanted" }, state(""))).toBeNull();
    expect(sourceTemperature({ type: "target_temperature", value: "climate.living_room" }, thermostat)).toBe(22);
    expect(sourceTemperature({ type: "current_temperature", value: "climate.living_room" }, thermostat)).toBe(19.5);
    expect(sourceTemperature({ type: "current_temperature", value: "climate.gone" }, undefined)).toBeNull();
  });
});
