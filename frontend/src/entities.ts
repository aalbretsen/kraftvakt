import type { Charger } from "./api";
import type { HomeAssistant } from "./types";

/** The domains whose entities are on or off, and so can be boolean entities. */
export const BOOLEAN_DOMAINS = ["binary_sensor", "input_boolean", "switch", "schedule"];

/** Return the name of an entity. An entity chosen in the draft uses its friendly name until it is saved. */
export function entityName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  return names[entityId] ?? hass.states[entityId]?.attributes.friendly_name ?? entityId;
}

/**
 * Return the name of a charger as the backend names it: its device's, or
 * else its entity's. Null when it has neither.
 */
export function chargerName(hass: HomeAssistant, names: Record<string, string>, charger: Charger): string | null {
  const device = charger.device_id ? hass.devices?.[charger.device_id] : undefined;
  const deviceName = device?.name_by_user ?? device?.name;
  if (deviceName) {
    return deviceName;
  }
  return charger.entity_id ? entityName(hass, names, charger.entity_id) : null;
}

/** Return Kraftvakt's own entities, left out where a sensor from another integration is chosen. */
export function ownEntities(hass: HomeAssistant): string[] {
  return Object.values(hass.entities ?? {})
    .filter((entry) => entry.platform === "kraftvakt")
    .map((entry) => entry.entity_id);
}

/** Return the power a power sensor measures now in W, read as the backend reads it. */
export function measuredPowerW(hass: HomeAssistant, entityId: string): number | null {
  const entity = hass.states[entityId];
  const value = Number(entity?.state);
  if (!entity || entity.state.trim() === "" || !Number.isFinite(value)) {
    return null;
  }
  const unit = entity.attributes.unit_of_measurement;
  const factor = unit === "kW" ? 1000 : !unit || unit === "W" ? 1 : null;
  return factor === null ? null : Math.max(0, value) * factor;
}
