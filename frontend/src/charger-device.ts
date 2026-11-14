/** The device of an EV charger and the entities it offers. */
import type { Charger, Condition } from "./api";
import type { HomeAssistant } from "./types";

/** Return the entities of the device, none without a device. */
export function deviceEntities(hass: HomeAssistant, deviceId: string | null): string[] {
  if (!deviceId) {
    return [];
  }
  return Object.values(hass.entities ?? {})
    .filter((entry) => entry.device_id === deviceId)
    .map((entry) => entry.entity_id);
}

/** Return each field of the charger that names an entity, which must belong to its device. */
export function chargerDeviceEntities(charger: Charger): [string, string][] {
  const entities: [string, string | null | undefined][] = [
    ["entity_id", charger.entity_id],
    ["set_current", charger.set_current?.mode === "entity" ? charger.set_current.entity_id : null],
    ["car_connected", entityOfCondition(charger.car_connected)],
    ["actively_charging", entityOfCondition(charger.actively_charging)],
  ];
  return entities.filter((entry): entry is [string, string] => !!entry[1]);
}

function entityOfCondition(condition: Condition | null): string | null {
  return condition && condition.type !== "template" ? condition.value : null;
}

/** Return the changes that move the charger to a device: every entity that is not on the device is cleared, and templates are kept. */
export function changesForDevice(charger: Charger, deviceId: string | null, hass: HomeAssistant): Partial<Charger> {
  const onDevice = new Set(deviceEntities(hass, deviceId));
  const kept = (entityId: string | null | undefined): string | null => (entityId && onDevice.has(entityId) ? entityId : null);
  const keptCondition = (condition: Condition | null): Condition | null =>
    condition && (condition.type === "template" || kept(condition.value)) ? condition : null;
  const setCurrent = charger.set_current;
  return {
    device_id: deviceId,
    entity_id: kept(charger.entity_id),
    set_current: setCurrent?.mode === "entity" && !kept(setCurrent.entity_id) ? { mode: "entity", entity_id: null } : setCurrent,
    car_connected: keptCondition(charger.car_connected),
    actively_charging: keptCondition(charger.actively_charging),
  };
}
