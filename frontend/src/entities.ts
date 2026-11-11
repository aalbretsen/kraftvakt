import type { HomeAssistant } from "./types";

/** Return the name of an entity. An entity chosen in the draft uses its friendly name until it is saved. */
export function entityName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  return names[entityId] ?? hass.states[entityId]?.attributes.friendly_name ?? entityId;
}

/** Return the name of a charger as the backend names it: its device's, or else its entity's. */
export function chargerName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  const deviceId = hass.entities?.[entityId]?.device_id;
  const device = deviceId ? hass.devices?.[deviceId] : undefined;
  return names[entityId] ?? device?.name_by_user ?? device?.name ?? entityName(hass, names, entityId);
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
