/**
 * The device of an EV charger: the entities it offers, and guessing which of
 * them the charger needs from their names and types.
 */
import type { Capabilities, Charger, Condition } from "./api";
import { BOOLEAN_DOMAINS } from "./entities";
import type { HomeAssistant } from "./types";

/** What an entity must be to be guessed for a field, and the words that make it more likely. */
interface GuessRule {
  domains: string[];
  /** Required when set. */
  deviceClass?: string;
  /** Device classes and a unit that count more than a word. */
  likelyDeviceClasses?: string[];
  likelyUnit?: string;
  /** English and Norwegian words, matched anywhere in the name and the entity ID. */
  words: string[];
  /** An entity with one of these words is never guessed. */
  excludedWords?: string[];
  /** Whether the only entity of the type is guessed without a word. */
  onlyCandidateIsEnough: boolean;
  /** Whether the main entity of the device, which has no name of its own, counts as a word. */
  mainEntityMatches?: boolean;
}

interface Candidate {
  entityId: string;
  domain: string;
  deviceClass?: unknown;
  unit?: unknown;
  text: string;
  /** The words of the name without the device name, none for the main entity of the device. */
  ownWords: string[];
}

const LIKELY_TYPE_SCORE = 2;

const CAR_CONNECTED: GuessRule = {
  domains: BOOLEAN_DOMAINS,
  likelyDeviceClasses: ["plug", "connectivity"],
  words: ["connected", "plug", "cable", "car", "tilkoblet", "kabel", "bil"],
  excludedWords: ["unplugged", "allow", "enable", "full", "tillat"],
  onlyCandidateIsEnough: false,
};

const CHARGING_ENTITY: GuessRule = {
  domains: BOOLEAN_DOMAINS,
  likelyDeviceClasses: ["battery_charging", "running", "power"],
  words: ["charging", "lader", "lading"],
  excludedWords: ["allow", "enable", "connected", "full", "tillat", "tilkoblet"],
  onlyCandidateIsEnough: false,
};

const CHARGING_POWER: GuessRule = {
  domains: ["sensor"],
  deviceClass: "power",
  words: ["charging", "charger", "lade", "effekt"],
  onlyCandidateIsEnough: true,
};

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

/**
 * Return the changes that move the charger to a device: every entity that
 * is not on the device is cleared, and every field that is then empty gets
 * the entity of the device that it most likely is. `usedEntities` are the
 * entities of the other appliances and chargers, which the charger's own
 * entity cannot be.
 */
export function changesForDevice(
  charger: Charger,
  deviceId: string | null,
  hass: HomeAssistant,
  capabilities: Capabilities,
  usedEntities: string[],
): Partial<Charger> {
  const onDevice = new Set(deviceEntities(hass, deviceId));
  const kept = (entityId: string | null | undefined): string | null =>
    entityId && onDevice.has(entityId) ? entityId : null;
  const candidates = [...onDevice].map((entityId) => candidate(hass, entityId, deviceId));
  const taken = new Set(usedEntities);
  const guess = (rule: GuessRule): string | null => {
    const entityId = guessEntity(
      candidates.filter((item) => !taken.has(item.entityId)),
      rule,
    );
    if (entityId) {
      taken.add(entityId);
    }
    return entityId;
  };
  const defaults = capabilities.default_actions.chargers;

  const entityId =
    kept(charger.entity_id) ??
    guess({
      domains: defaults.activate.domains,
      words: ["charging", "allow", "enable", "lading", "tillat"],
      excludedWords: ["connected", "plug", "full", "lock", "offline", "phase", "tilkoblet", "fase"],
      onlyCandidateIsEnough: true,
      mainEntityMatches: true,
    });
  if (entityId) {
    taken.add(entityId);
  }

  let setCurrent = charger.set_current;
  if (setCurrent === null || (setCurrent.mode === "entity" && !kept(setCurrent.entity_id))) {
    const currentEntity = guess({
      domains: defaults.set_current.domains,
      likelyUnit: "A",
      words: ["current", "ampere", "limit", "charge", "strøm", "lade"],
      excludedWords: ["offline"],
      onlyCandidateIsEnough: true,
    });
    setCurrent = currentEntity
      ? { mode: "entity", entity_id: currentEntity }
      : setCurrent && { mode: "entity", entity_id: null };
  }

  const keptCondition = (condition: Condition | null): Condition | null =>
    condition && (condition.type === "template" || kept(condition.value)) ? condition : null;
  const asCondition = (type: Condition["type"], value: string | null): Condition | null =>
    value ? { type, value } : null;

  const carConnected = keptCondition(charger.car_connected) ?? asCondition("entity", guess(CAR_CONNECTED));
  const activelyCharging =
    keptCondition(charger.actively_charging) ??
    asCondition("entity", guess(CHARGING_ENTITY)) ??
    asCondition("power_sensor", guess(CHARGING_POWER));

  return {
    device_id: deviceId,
    entity_id: entityId,
    set_current: setCurrent,
    car_connected: carConnected,
    actively_charging: activelyCharging,
  };
}

/**
 * The name and the entity ID, in lower case and without the name of the
 * device, so the device name does not count as words in every entity.
 */
function candidate(hass: HomeAssistant, entityId: string, deviceId: string | null): Candidate {
  const device = deviceId ? hass.devices?.[deviceId] : undefined;
  const deviceName = (device?.name_by_user ?? device?.name ?? "").toLowerCase();
  const attributes = hass.states[entityId]?.attributes ?? {};
  const [domain, objectId] = entityId.split(".");
  const name = String(attributes.friendly_name ?? "").toLowerCase();
  const withoutDevice = (text: string, prefix: string) =>
    prefix && text.startsWith(prefix) ? text.slice(prefix.length) : text;
  const ownName = withoutDevice(name, deviceName);
  const ownObjectId = withoutDevice(objectId, deviceName.replace(/\W+/g, "_"));
  return {
    entityId,
    domain,
    deviceClass: attributes.device_class,
    unit: attributes.unit_of_measurement,
    text: `${ownName} ${ownObjectId}`.replace(/_/g, " "),
    ownWords: (name ? ownName : ownObjectId).split(/[^\p{L}\p{N}]+/u).filter(Boolean),
  };
}

/**
 * Return the entity with the highest score for the rule. Of those that share
 * it, the one with the fewest other words in its name is the most specific;
 * none when two share that too.
 */
function guessEntity(candidates: Candidate[], rule: GuessRule): string | null {
  const matching = candidates.filter(
    (item) =>
      rule.domains.includes(item.domain) &&
      (rule.deviceClass === undefined || item.deviceClass === rule.deviceClass) &&
      !rule.excludedWords?.some((word) => item.text.includes(word)),
  );
  if (matching.length === 1 && rule.onlyCandidateIsEnough) {
    return matching[0].entityId;
  }
  const ranked = matching
    .map((item) => ({ entityId: item.entityId, score: score(item, rule), otherWords: otherWords(item, rule) }))
    .filter((item) => item.score > 0)
    .sort((first, second) => second.score - first.score || first.otherWords - second.otherWords);
  const [best, next] = ranked;
  if (!best || (next && next.score === best.score && next.otherWords === best.otherWords)) {
    return null;
  }
  return best.entityId;
}

function score(item: Candidate, rule: GuessRule): number {
  const words = rule.words.filter((word) => item.text.includes(word)).length;
  const likelyClass = rule.likelyDeviceClasses?.includes(String(item.deviceClass)) ? LIKELY_TYPE_SCORE : 0;
  const likelyUnit = rule.likelyUnit !== undefined && item.unit === rule.likelyUnit ? LIKELY_TYPE_SCORE : 0;
  const mainEntity = rule.mainEntityMatches && item.ownWords.length === 0 ? 1 : 0;
  return words + likelyClass + likelyUnit + mainEntity;
}

function otherWords(item: Candidate, rule: GuessRule): number {
  return item.ownWords.filter((word) => !rule.words.some((ruleWord) => word.includes(ruleWord))).length;
}
