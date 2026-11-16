/** The states an entity reports, offered when a condition counts some of them as true. */
import type { HassEntity, HomeAssistant } from "./types";

const NO_STATE = new Set(["unknown", "unavailable", ""]);

const HISTORY_DAYS = 7;

/**
 * Return the states to offer: the entity's own options first, then its current state, the states in its history
 * and the states already chosen, each once, without unknown and unavailable.
 */
export function reportedStates(stateObj: HassEntity | undefined, history: string[], chosen: string[]): string[] {
  const options = stateObj?.attributes.options;
  const candidates = [...(Array.isArray(options) ? options.map(String) : []), stateObj?.state ?? "", ...history, ...chosen];
  return [...new Set(candidates.filter((state) => !NO_STATE.has(state)))];
}

/** Return whether the state is one of the chosen ones, or null when the entity has no state, as the backend reads it. */
export function stateEvidence(state: string | undefined, chosen: string[]): boolean | null {
  return state === undefined || NO_STATE.has(state) ? null : chosen.includes(state);
}

/** Return the states the entity has reported in Home Assistant's history over the last days. */
export async function stateHistory(hass: HomeAssistant, entityId: string): Promise<string[]> {
  const start = new Date(Date.now() - HISTORY_DAYS * 24 * 60 * 60 * 1000);
  const result = await hass.callWS<Record<string, { s: string }[]>>({
    type: "history/history_during_period",
    start_time: start.toISOString(),
    entity_ids: [entityId],
    minimal_response: true,
    no_attributes: true,
    significant_changes_only: false,
  });
  return [...new Set((result[entityId] ?? []).map((entry) => entry.s))];
}
