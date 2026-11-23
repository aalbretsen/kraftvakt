/** The devices of EV chargers and appliances, and the entities they offer. */
import { type Appliance, type Capabilities, type Charger, type ChargerProfileFields, type Condition, fetchChargerProfile } from "./api";
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

/** Return the device of the entity, null when it has none. */
export function deviceOfEntity(hass: HomeAssistant, entityId: string | null): string | null {
  return (entityId && hass.entities?.[entityId]?.device_id) || null;
}

/** Return the entities the display sensors of the appliance may use: those of the device of its entity, or any when it has none. */
export function displaySensorScope(hass: HomeAssistant, appliance: Appliance): string[] | undefined {
  const deviceId = deviceOfEntity(hass, appliance.entity_id);
  return deviceId ? deviceEntities(hass, deviceId) : undefined;
}

/** Return each display value of the appliance given as a sensor, with its field. */
export function displaySensors(appliance: Appliance): [string, string][] {
  const entities: [string, string | null][] = [
    ["display_power", entityOfCondition(appliance.display_power)],
    ["display_temperature", entityOfCondition(appliance.display_temperature)],
  ];
  return entities.filter((entry): entry is [string, string] => !!entry[1]);
}

/**
 * Return the display values that may stay when the appliance gets the entity:
 * the sensors outside the device of the entity are cleared, and templates are kept.
 */
export function displayValuesForEntity(appliance: Appliance, entityId: string | null, hass: HomeAssistant): Pick<Appliance, "display_power" | "display_temperature"> {
  const deviceId = deviceOfEntity(hass, entityId);
  const allowed = deviceId ? new Set(deviceEntities(hass, deviceId)) : undefined;
  return {
    display_power: keptCondition(appliance.display_power, allowed),
    display_temperature: keptCondition(appliance.display_temperature, allowed),
  };
}

/** Return each field of the charger that names an entity, which must belong to its device. */
export function chargerDeviceEntities(charger: Charger): [string, string][] {
  const entities: [string, string | null | undefined][] = [
    ["on_off_entity", charger.switched_by === "on_off_entity" ? charger.on_off_entity : null],
    ["set_current", charger.set_current?.mode === "entity" ? charger.set_current.entity_id : null],
    ["car_connected", entityOfCondition(charger.car_connected)],
    ["actively_charging", entityOfCondition(charger.actively_charging)],
    ["charging_power", entityOfCondition(charger.charging_power)],
    ["fault_flag", entityOfCondition(charger.fault_flag)],
  ];
  return entities.filter((entry): entry is [string, string] => !!entry[1]);
}

function entityOfCondition(condition: Condition | null): string | null {
  return condition && condition.type !== "template" ? condition.value : null;
}

/** Return the condition when it is a template, has no entity yet, or names an allowed entity; without `allowed`, every entity is. */
function keptCondition(condition: Condition | null, allowed: Set<string> | undefined): Condition | null {
  const entityId = entityOfCondition(condition);
  return !entityId || !allowed || allowed.has(entityId) ? condition : null;
}

/**
 * Return the changes that move the charger to a device: every entity that is not on the device is cleared, and templates are kept.
 */
export function changesForDevice(charger: Charger, deviceId: string | null, hass: HomeAssistant): Partial<Charger> {
  const onDevice = new Set(deviceEntities(hass, deviceId));
  const kept = (entityId: string | null | undefined): string | null => (entityId && onDevice.has(entityId) ? entityId : null);
  const setCurrent = charger.set_current;
  return {
    device_id: deviceId,
    on_off_entity: kept(charger.on_off_entity),
    set_current: setCurrent?.mode === "entity" && !kept(setCurrent.entity_id) ? { mode: "entity", entity_id: null } : setCurrent,
    car_connected: keptCondition(charger.car_connected, onDevice),
    actively_charging: keptCondition(charger.actively_charging, onDevice),
    charging_power: keptCondition(charger.charging_power, onDevice),
    fault_flag: keptCondition(charger.fault_flag, onDevice),
  };
}

/** The charger profile of a device, and without an answer from the backend the default profile, which only resets cloud-controlled. */
export function chargerProfileOf(hass: HomeAssistant, deviceId: string, capabilities: Capabilities): Promise<ChargerProfileFields> {
  return fetchChargerProfile(hass, deviceId).catch(() => ({ profile: null, fields: { cloud_controlled: capabilities.defaults.chargers.cloud_controlled } }));
}
