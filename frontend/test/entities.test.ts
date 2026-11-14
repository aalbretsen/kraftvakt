import { describe, expect, it } from "vitest";
import { chargerName, entityName, measuredPowerW, ownEntities } from "../src/entities";
import type { HomeAssistant } from "../src/types";
import { charger, hass, state } from "./builders";

describe("the power a sensor measures", () => {
  it.each([
    ["1500", "W", 1500],
    ["1.5", "kW", 1500],
    ["1500", undefined, 1500],
    ["-200", "W", 0],
    ["1.5", "MW", null],
    ["unavailable", "W", null],
    [" ", "W", null],
  ])("%s %s is read as the backend reads it, %s W", (value, unit, watt) => {
    expect(measuredPowerW(hass({ "sensor.power": state(value, { unit_of_measurement: unit }) }), "sensor.power")).toBe(watt);
  });

  it("is unknown for a sensor that does not exist", () => {
    expect(measuredPowerW(hass(), "sensor.gone")).toBeNull();
  });
});

describe("names", () => {
  const home = hass({ "switch.garage": state("on", { friendly_name: "Garage Charging allowed" }) }, [charger("garage")]);

  it("of an entity are the saved name, the friendly name, or the entity ID", () => {
    expect(entityName(home, { "switch.garage": "Saved" }, "switch.garage")).toBe("Saved");
    expect(entityName(home, {}, "switch.garage")).toBe("Garage Charging allowed");
    expect(entityName(home, {}, "switch.gone")).toBe("switch.gone");
  });

  it("of a charger are as the backend names it: the user's name for the device, its name, or else the entity's", () => {
    const named = { ...home, devices: { device_garage: { name: "Easee", name_by_user: "Garage" } } };
    expect(chargerName(named, {}, charger("garage"))).toBe("Garage");
    expect(chargerName(home, {}, charger("garage"))).toBe("garage");
    expect(chargerName(home, {}, charger("garage", { device_id: null }))).toBe("Garage Charging allowed");
    expect(chargerName(home, {}, charger("garage", { device_id: null, entity_id: null }))).toBeNull();
  });
});

describe("Kraftvakt's own entities", () => {
  it("are those of its platform", () => {
    const entities = {
      "sensor.kraftvakt_power_free": { entity_id: "sensor.kraftvakt_power_free", platform: "kraftvakt" },
      "sensor.house_power": { entity_id: "sensor.house_power", platform: "han" },
    };
    expect(ownEntities({ ...hass(), entities } as HomeAssistant)).toEqual(["sensor.kraftvakt_power_free"]);
  });
});
