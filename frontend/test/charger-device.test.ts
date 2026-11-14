/** Moving a charger to a device. Filling it in from a charger profile is the backend's, and tested there. */
import { describe, expect, it } from "vitest";
import type { ActionConfig } from "../src/api";
import { changesForDevice, deviceEntities } from "../src/charger-device";
import type { HomeAssistant } from "../src/types";
import { charger } from "./builders";

/** A device `device_<id>` with the given entities. */
function device(id: string, entityIds: string[]): HomeAssistant {
  return {
    states: {},
    entities: Object.fromEntries(entityIds.map((entityId) => [entityId, { entity_id: entityId, device_id: `device_${id}` }])),
    devices: { [`device_${id}`]: { name: id, name_by_user: null } },
  } as unknown as HomeAssistant;
}

describe("moving a charger to a device", () => {
  const cabin = device("cabin", ["switch.cabin", "binary_sensor.cabin_charging"]);

  it("keeps the entities on the new device, the templates and the actions, and clears the other entities", () => {
    const garage = charger("garage", {
      entity_id: "switch.cabin",
      car_connected: { type: "template", value: "{{ true }}" },
      actively_charging: { type: "entity", value: "binary_sensor.cabin_charging" },
    });
    expect(changesForDevice(garage, "device_cabin", cabin)).toEqual({
      device_id: "device_cabin",
      entity_id: "switch.cabin",
      set_current: { mode: "entity", entity_id: null },
      car_connected: { type: "template", value: "{{ true }}" },
      actively_charging: { type: "entity", value: "binary_sensor.cabin_charging" },
    });
  });

  it("keeps a custom action for the charging current", () => {
    const custom: ActionConfig = { mode: "custom", action: [{ action: "my_charger.set_current" }] };
    expect(changesForDevice(charger("garage", { set_current: custom }), "device_cabin", cabin).set_current).toEqual(custom);
  });

  it("clears every entity when the device is removed", () => {
    expect(changesForDevice(charger("garage"), null, cabin)).toEqual({
      device_id: null,
      entity_id: null,
      set_current: { mode: "entity", entity_id: null },
      car_connected: null,
      actively_charging: null,
    });
    expect(deviceEntities(cabin, null)).toEqual([]);
  });
});
