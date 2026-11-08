import type { HomeAssistant } from "./types";

/**
 * Return the name of an appliance's or charger's entity in Home Assistant.
 *
 * The backend gives the names of the saved entities. An entity chosen in the
 * draft uses its friendly name until it is saved.
 */
export function entityName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  return names[entityId] ?? hass.states[entityId]?.attributes.friendly_name ?? entityId;
}

/**
 * Return the name of a charger, as the backend names it: its device's name, or
 * else its entity's. The backend gives the names of the saved chargers.
 */
export function chargerName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  const deviceId = hass.entities?.[entityId]?.device_id;
  const device = deviceId ? hass.devices?.[deviceId] : undefined;
  return names[entityId] ?? device?.name_by_user ?? device?.name ?? entityName(hass, names, entityId);
}

/**
 * Return Kraftvakt's own entities. They are left out where a sensor from
 * another integration is chosen, like the power sensor.
 */
export function ownEntities(hass: HomeAssistant): string[] {
  return Object.values(hass.entities ?? {})
    .filter((entry) => entry.platform === "kraftvakt")
    .map((entry) => entry.entity_id);
}

/**
 * Return the power a power sensor measures now in kW, read as the backend reads
 * it: W or kW, W without a unit, negative as 0, and null for anything else.
 */
export function measuredPowerKw(hass: HomeAssistant, entityId: string): number | null {
  const entity = hass.states[entityId];
  const value = Number(entity?.state);
  if (!entity || entity.state.trim() === "" || !Number.isFinite(value)) {
    return null;
  }
  const unit = entity.attributes.unit_of_measurement;
  const divisor = unit === "kW" ? 1 : !unit || unit === "W" ? 1000 : null;
  return divisor === null ? null : Math.max(0, value) / divisor;
}
