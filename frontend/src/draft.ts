/**
 * The draft that the configuration pages edit. It is never changed in place:
 * each change makes a new configuration.
 */
import type { Charger, KraftvaktConfig, PriorityEntry } from "./api";

export const DRAFT_CHANGED = "draft-changed";

/** Ask the panel to replace the draft with a changed configuration. */
export function fireDraftChanged(element: HTMLElement, config: KraftvaktConfig): void {
  element.dispatchEvent(new CustomEvent(DRAFT_CHANGED, { detail: config, bubbles: true, composed: true }));
}

/**
 * Return a short unique id for an appliance, variant, charger or group of chargers.
 *
 * `crypto.randomUUID` needs a secure context, which Home Assistant on plain HTTP
 * in the local network is not, so the id is made from random bytes.
 */
export function newId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(6));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

/** Return whether two configurations are the same. */
export function sameConfig(first: KraftvaktConfig | undefined, second: KraftvaktConfig | undefined): boolean {
  return JSON.stringify(first) === JSON.stringify(second);
}

/** Return the items with the item at `from` moved to `to`, as `ha-sortable` reports it. */
export function moveItem<T>(items: readonly T[], from: number, to: number): T[] {
  const moved = [...items];
  const [item] = moved.splice(from, 1);
  moved.splice(to, 0, item);
  return moved;
}

/** Return a key that identifies an entry in the priority list. */
export function priorityKey(entry: PriorityEntry): string {
  return entry.type === "charger_group" ? `group/${entry.group_id}` : `${entry.appliance_id}/${entry.variant_id ?? ""}`;
}

/** Return the configuration with exactly one priority entry per appliance and variant. */
export function withCompletePriority(config: KraftvaktConfig): KraftvaktConfig {
  const expected = expectedPriority(config);
  const expectedKeys = new Set(expected.map(priorityKey));
  const seen = new Set<string>();
  const kept = config.priority.filter((entry) => {
    const key = priorityKey(entry);
    if (!expectedKeys.has(key) || seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
  const missing = expected.filter((entry) => !seen.has(priorityKey(entry)));
  return { ...config, priority: [...kept, ...missing] };
}

function expectedPriority(config: KraftvaktConfig): PriorityEntry[] {
  const entries: PriorityEntry[] = config.appliances.flatMap((appliance) => [
    { type: "appliance", appliance_id: appliance.id, variant_id: null },
    ...appliance.variants.map(
      (variant): PriorityEntry => ({ type: "appliance", appliance_id: appliance.id, variant_id: variant.id }),
    ),
  ]);
  entries.push(...config.charger_groups.map((group): PriorityEntry => ({ type: "charger_group", group_id: group.id })));
  return entries;
}

/** Return the chargers of every group. */
export function allChargers(config: KraftvaktConfig): Charger[] {
  return config.charger_groups.flatMap((group) => group.chargers);
}
