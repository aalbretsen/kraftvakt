import type { HomeAssistant } from "./types";

/**
 * Return the name of an appliance's or charger's entity in Home Assistant (GEN-013).
 *
 * The backend gives the names of the saved entities. An entity chosen in the
 * draft uses its friendly name until it is saved.
 */
export function entityName(hass: HomeAssistant, names: Record<string, string>, entityId: string): string {
  return names[entityId] ?? hass.states[entityId]?.attributes.friendly_name ?? entityId;
}

/**
 * Return Kraftvakt's own entities. They are left out where a sensor from
 * another integration is chosen, like the power sensor (GEN-003).
 */
export function ownEntities(hass: HomeAssistant): string[] {
  return Object.values(hass.entities ?? {})
    .filter((entry) => entry.platform === "kraftvakt")
    .map((entry) => entry.entity_id);
}
