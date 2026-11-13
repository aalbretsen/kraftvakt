/** Checks of the draft, so the user sees mistakes before saving. */
import {
  type ActionConfig,
  type Appliance,
  type ApplianceActions,
  type Capabilities,
  type Charger,
  type ChargerGroup,
  type Condition,
  type DefaultAction,
  type Issue,
  type KraftvaktConfig,
  type Range,
} from "./api";
import { chargerDeviceEntities } from "./charger-device";
import { allChargers } from "./draft";
import { availableDomainAction, parameterIssues } from "./domain-actions";
import type { HassEntity, HomeAssistant } from "./types";

type LimitSection = keyof Capabilities["limits"];
type ActionSection = keyof Capabilities["default_actions"];
type States = Record<string, HassEntity>;

export const APPLIANCE_ACTIONS = ["turn_on", "turn_off"] as const;
const CHARGER_ACTIONS = ["activate", "deactivate", "set_current"] as const;

/** An action of an appliance or a charger: its name, the field issues address, and its value. */
interface ActionEntry {
  name: string;
  field: string;
  action: ActionConfig | null;
}

/** Return the actions of the appliance and those the variants override, as the backend does. */
function applianceActions(appliance: Appliance): ActionEntry[] {
  return [
    ...APPLIANCE_ACTIONS.map((name) => ({ name, field: name, action: appliance[name] })),
    ...appliance.variants.flatMap((variant) =>
      APPLIANCE_ACTIONS.filter((name) => isOverridden(variant.actions, name)).map((name) => ({
        name,
        field: `variants.${variant.id}.${name}`,
        action: variant.actions[name] ?? null,
      })),
    ),
  ];
}

/** Return whether the actions hold the action `name`, also when it is not set yet. */
export function isOverridden(actions: Partial<ApplianceActions> | undefined, name: keyof ApplianceActions): boolean {
  return actions?.[name] !== undefined;
}

function chargerActions(charger: Charger): ActionEntry[] {
  return CHARGER_ACTIONS.map((name) => ({ name, field: name, action: charger[name] }));
}

/** Return the mistakes in the draft that stop it from being saved. */
export function draftErrors(config: KraftvaktConfig, capabilities: Capabilities, hass: HomeAssistant): Issue[] {
  return [
    ...rangeIssues("general", undefined, config.general, capabilities.limits.general, true),
    ...config.appliances.flatMap((appliance) => applianceErrors(appliance, capabilities, hass.states)),
    ...chargerGroupErrors(config.charger_groups),
    ...allChargers(config).flatMap((charger) => chargerErrors(charger, capabilities, hass)),
  ];
}

/** Return the groups whose names are empty or used by another group. */
function chargerGroupErrors(groups: ChargerGroup[]): Issue[] {
  const names = groups.map((group) => group.name.trim());
  return groups.flatMap((group, index): Issue[] => {
    const name = names[index];
    const code = !name ? "empty_name" : names.filter((other) => other === name).length > 1 ? "duplicate_name" : undefined;
    return code ? [{ code, section: "charger_groups", target: group.id, field: "name" }] : [];
  });
}

/** Return what is missing before the regulation can start, as the backend does. */
export function missingItems(config: KraftvaktConfig): Issue[] {
  const missing: Issue[] = [];
  if (!config.general.power_sensor) {
    missing.push({ code: "missing_power_sensor", section: "general", field: "power_sensor" });
  }
  missing.push(...config.appliances.flatMap(missingInAppliance));
  for (const group of config.charger_groups) {
    missing.push(...group.chargers.flatMap((charger) => missingInCharger(charger, group.one_at_a_time)));
  }
  return missing;
}

export function missingInAppliance(appliance: Appliance): Issue[] {
  return [
    ...missingEntityAndActions("appliances", appliance, applianceActions(appliance)),
    ...appliance.variants
      .filter((variant) => !isSet(variant.condition))
      .map((variant) => applianceIssue(appliance, "missing_condition", `variants.${variant.id}.condition`)),
  ];
}

export function carConnectedRequired(charger: Charger, oneAtATime: boolean): boolean {
  return oneAtATime || (charger.charging_window !== null && charger.override_ends === "car_disconnected");
}

export function missingInCharger(charger: Charger, oneAtATime: boolean): Issue[] {
  const missing: Issue[] = charger.device_id
    ? []
    : [{ code: "missing_device", section: "chargers", target: charger.id, field: "device_id" }];
  missing.push(...missingEntityAndActions("chargers", charger, chargerActions(charger)));
  if (!isSet(charger.actively_charging)) {
    missing.push({ code: "missing_actively_charging", section: "chargers", target: charger.id, field: "actively_charging" });
  }
  if (carConnectedRequired(charger, oneAtATime) && !isSet(charger.car_connected)) {
    missing.push({ code: "missing_car_connected", section: "chargers", target: charger.id, field: "car_connected" });
  }
  return missing;
}

export function defaultActionOf(capabilities: Capabilities, section: ActionSection, field: string): DefaultAction {
  return (capabilities.default_actions[section] as Record<string, DefaultAction>)[field];
}

/** Return whether the action, given as the default or a domain action, can run for the entity. */
export function isActionAvailable(
  capabilities: Capabilities,
  section: ActionSection,
  field: string,
  entityId: string | null,
  action: ActionConfig | null,
): boolean {
  switch (action?.mode) {
    case "default":
      return hasDefaultAction(capabilities, section, field, entityId);
    case "domain":
      return availableDomainAction(capabilities, section, field, entityId, action) !== undefined;
    default:
      return true;
  }
}

/** Return whether the domain of the entity has a default action for the field. */
export function hasDefaultAction(
  capabilities: Capabilities,
  section: ActionSection,
  field: string,
  entityId: string | null,
): boolean {
  return entityId !== null && defaultActionOf(capabilities, section, field).domains.includes(entityId.split(".")[0]);
}

/** Return the issues that belong to one appliance or charger. */
export function issuesFor(issues: Issue[], section: Issue["section"], target: string): Issue[] {
  return issues.filter((issue) => issue.section === section && issue.target === target);
}

export function isMissingAction(action: ActionConfig | null): boolean {
  return (
    action === null ||
    (action.mode === "custom" && (action.action ?? []).length === 0) ||
    (action.mode === "entity" && !action.entity_id) ||
    (action.mode === "domain" && Object.values(action.data ?? {}).includes(null))
  );
}

export function applianceErrors(appliance: Appliance, capabilities: Capabilities, states: States): Issue[] {
  const labels = appliance.variants.map((variant) => variant.label.trim());
  return [
    ...rangeIssues("appliances", appliance.id, appliance, capabilities.limits.appliances, false),
    ...actionIssues("appliances", appliance, applianceActions(appliance), capabilities, states),
    ...appliance.variants.flatMap((variant, index): Issue[] => {
      const field = `variants.${variant.id}.label`;
      if (labels[index] === "") {
        return [applianceIssue(appliance, "empty_label", field)];
      }
      if (labels.filter((label) => label === labels[index]).length > 1) {
        return [applianceIssue(appliance, "duplicate_label", field)];
      }
      return [];
    }),
  ];
}

export function chargerErrors(charger: Charger, capabilities: Capabilities, hass: HomeAssistant): Issue[] {
  const issue = (code: string, field: string): Issue => ({ code, section: "chargers", target: charger.id, field });
  const issues = [
    ...rangeIssues("chargers", charger.id, charger, capabilities.limits.chargers, true),
    ...actionIssues("chargers", charger, chargerActions(charger), capabilities, hass.states),
    ...deviceIssues(charger, hass).map(([code, field]) => issue(code, field)),
  ];
  if (charger.min_current_a > charger.max_current_a) {
    issues.push(issue("min_current_above_max", "min_current_a"));
  }
  const window = charger.charging_window;
  if (window && (!window.start || !window.end)) {
    issues.push(issue("invalid_time", "charging_window"));
  } else if (window && window.start === window.end) {
    issues.push(issue("window_start_equals_end", "charging_window"));
  }
  return issues;
}

function applianceIssue(appliance: Appliance, code: string, field: string): Issue {
  return { code, section: "appliances", target: appliance.id, field };
}

/** An empty condition is missing, not a mistake. */
function isSet(condition: Condition | null): boolean {
  return condition !== null && condition.value.trim() !== "";
}

/** Optional settings that are not given are only checked when `required` is set. */
function rangeIssues(
  section: LimitSection,
  target: string | undefined,
  item: object,
  limits: Record<string, Range>,
  required: boolean,
): Issue[] {
  const values = item as Record<string, unknown>;
  return Object.entries(limits).flatMap(([field, range]) => {
    const value = values[field];
    const code =
      typeof value !== "number" || Number.isNaN(value) ? (required ? "required" : undefined) : rangeCode(value, range);
    return code ? [{ code, section, target, field }] : [];
  });
}

function rangeCode(value: number, range: Range): string | undefined {
  if ((range.min !== null && value < range.min) || (range.max !== null && value > range.max)) {
    return "out_of_range";
  }
  const multiple = value / range.resolution;
  return Math.abs(multiple - Math.round(multiple)) < 1e-6 ? undefined : "invalid_resolution";
}

/** The actions that cannot run for the entity of the item, as the backend checks them. */
function actionIssues(
  section: ActionSection,
  item: Appliance | Charger,
  entries: ActionEntry[],
  capabilities: Capabilities,
  states: States,
): Issue[] {
  const entityId = item.entity_id;
  if (entityId === null) {
    return [];
  }
  return entries.flatMap(({ name, field, action }): Issue[] => {
    const issue = (code: string, parameter?: string): Issue => ({
      code,
      section,
      target: item.id,
      field: parameter ? `${field}.${parameter}` : field,
    });
    if (!isActionAvailable(capabilities, section, name, entityId, action)) {
      return [issue(action?.mode === "default" ? "default_action_unavailable" : "domain_action_unavailable")];
    }
    const domainAction = availableDomainAction(capabilities, section, name, entityId, action);
    if (!domainAction) {
      return [];
    }
    return Object.entries(parameterIssues(domainAction, action?.data ?? {}, states[entityId])).map(
      ([parameter, code]) => issue(code, parameter),
    );
  });
}

function missingEntityAndActions(
  section: "appliances" | "chargers",
  item: Appliance | Charger,
  entries: ActionEntry[],
): Issue[] {
  return [
    ...(item.entity_id ? [] : [{ code: "missing_entity", section, target: item.id, field: "entity_id" }]),
    ...entries
      .filter(({ action }) => isMissingAction(action))
      .map(({ field }) => ({ code: "missing_action", section, target: item.id, field })),
  ];
}

/** Return a device that does not exist, or the fields whose entities are not on the charger's device. */
function deviceIssues(charger: Charger, hass: HomeAssistant): [string, string][] {
  if (!charger.device_id) {
    return [];
  }
  if (!hass.devices?.[charger.device_id]) {
    return [["unknown_device", "device_id"]];
  }
  return chargerDeviceEntities(charger)
    .filter(([, entityId]) => hass.entities?.[entityId]?.device_id !== charger.device_id)
    .map(([field]) => ["entity_not_on_device", field]);
}
