/** Moving a charger to a device, and the display sensors of an appliance. Filling a charger in from a charger profile is the backend's, and tested there. */
import { describe, expect, it } from "vitest";
import type { ActionConfig, Capabilities } from "../src/api";
import { changesForDevice, chargerProfileOf, deviceEntities, displaySensorScope, displaySensors, displayValuesForEntity } from "../src/devices";
import type { HomeAssistant } from "../src/types";
import { applianceErrors } from "../src/validation";
import { appliance, CAPABILITIES, charger } from "./builders";

/** A device `device_<id>` with the given entities. */
function device(id: string, entityIds: string[]): HomeAssistant {
  return {
    states: {},
    entities: Object.fromEntries(entityIds.map((entityId) => [entityId, { entity_id: entityId, device_id: `device_${id}` }])),
    devices: { [`device_${id}`]: { name: id, name_by_user: null } },
  } as unknown as HomeAssistant;
}

describe("moving a charger to a device", () => {
  const cabin = device("cabin", ["switch.cabin", "binary_sensor.cabin_charging", "binary_sensor.cabin_error"]);

  it("keeps the entities on the new device, the templates and the actions, and clears the other entities", () => {
    const garage = charger("garage", {
      on_off_entity: "switch.cabin",
      car_connected: { type: "template", value: "{{ true }}" },
      actively_charging: { type: "entity", value: "binary_sensor.cabin_charging" },
      charging_power: { type: "template", value: "{{ 2300 }}" },
      fault_flag: { type: "entity", value: "binary_sensor.garage_error" },
    });
    expect(changesForDevice(garage, "device_cabin", cabin)).toEqual({
      device_id: "device_cabin",
      on_off_entity: "switch.cabin",
      set_current: { mode: "entity", entity_id: null },
      car_connected: { type: "template", value: "{{ true }}" },
      actively_charging: { type: "entity", value: "binary_sensor.cabin_charging" },
      charging_power: { type: "template", value: "{{ 2300 }}" },
      fault_flag: null,
    });
  });

  it("keeps a custom action for the charging current", () => {
    const custom: ActionConfig = { mode: "custom", action: [{ action: "my_charger.set_current" }] };
    expect(changesForDevice(charger("garage", { set_current: custom }), "device_cabin", cabin).set_current).toEqual(custom);
  });

  it("clears every entity when the device is removed", () => {
    expect(changesForDevice(charger("garage"), null, cabin)).toEqual({
      device_id: null,
      on_off_entity: null,
      set_current: { mode: "entity", entity_id: null },
      car_connected: null,
      actively_charging: null,
      charging_power: null,
      fault_flag: null,
    });
    expect(deviceEntities(cabin, null)).toEqual([]);
  });
});

describe("the display sensors of an appliance", () => {
  const home = device("heater", ["climate.heater", "sensor.heater_power", "sensor.heater_temperature"]);
  const heater = appliance("heater", {
    entity_id: "climate.heater",
    display_power: { type: "power_sensor", value: "sensor.heater_power" },
    display_temperature: { type: "temperature_sensor", value: "sensor.outdoor" },
  });

  it("may use the entities of the device of the appliance's entity, or any when it has none", () => {
    expect(displaySensorScope(home, heater)).toEqual(["climate.heater", "sensor.heater_power", "sensor.heater_temperature"]);
    expect(displaySensorScope(home, { ...heater, entity_id: "switch.helper" })).toBeUndefined();
    expect(displaySensors(heater)).toEqual([
      ["display_power", "sensor.heater_power"],
      ["display_temperature", "sensor.outdoor"],
    ]);
  });

  it("keeps the sensors on the device of a new entity and the templates, and every sensor for an entity without a device", () => {
    const withTemplate = { ...heater, display_power: { type: "template" as const, value: "{{ 1000 }}" } };
    expect(displayValuesForEntity(withTemplate, "climate.heater", home)).toEqual({
      display_power: { type: "template", value: "{{ 1000 }}" },
      display_temperature: null,
    });
    expect(displayValuesForEntity(heater, "switch.helper", home)).toEqual({
      display_power: heater.display_power,
      display_temperature: heater.display_temperature,
    });
  });

  it("outside the device is an error, but not for an entity without a device", () => {
    const hass = { ...home, config: { unit_system: { temperature: "°C" } } } as HomeAssistant;
    const capabilities = { limits: { appliances: {} }, actions: {}, domain_actions: {} } as unknown as Capabilities;
    expect(applianceErrors({ ...heater, turn_on: null, turn_off: null }, capabilities, hass)).toEqual([
      { code: "entity_not_on_device", section: "appliances", target: "heater", field: "display_temperature" },
    ]);
    expect(applianceErrors({ ...heater, entity_id: "switch.helper", turn_on: null, turn_off: null }, capabilities, hass)).toEqual([]);
  });
});

describe("the charger profile of a device", () => {
  function answering(callWS: () => Promise<unknown>): HomeAssistant {
    return { callWS } as unknown as HomeAssistant;
  }

  it("is the backend's answer", async () => {
    const answer = { profile: "Easee", fields: { start_delay_s: 300 } };
    expect(
      await chargerProfileOf(
        answering(() => Promise.resolve(answer)),
        "device_a",
        CAPABILITIES,
      ),
    ).toEqual(answer);
  });

  it("is the default profile, which keeps the start delay, when the backend does not answer", async () => {
    expect(
      await chargerProfileOf(
        answering(() => Promise.reject(new Error("lost"))),
        "device_a",
        CAPABILITIES,
      ),
    ).toEqual({ profile: null, fields: { cloud_controlled: CAPABILITIES.defaults.chargers.cloud_controlled } });
  });
});
