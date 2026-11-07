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
