/**
 * Checks of the draft in the panel, so the user sees mistakes before saving.
 *
 * The backend validates the configuration again when it is saved, and its
 * errors are shown the same way. The limits come from `kraftvakt/capabilities`,
 * so they are kept in one place.
 */
import type {
  ActionConfig,
  Appliance,
  Capabilities,
  Charger,
  Condition,
  Issue,
  KraftvaktConfig,
  Range,
} from "./api";

type LimitSection = keyof Capabilities["limits"];
type ActionSection = keyof Capabilities["default_actions"];

const APPLIANCE_ACTIONS = ["turn_on", "turn_off"] as const;
const CHARGER_ACTIONS = ["activate", "deactivate", "set_current"] as const;

/** Return the mistakes in the draft that stop it from being saved. */
export function draftErrors(config: KraftvaktConfig, capabilities: Capabilities): Issue[] {
  return [
    ...rangeIssues("general", undefined, config.general, capabilities.limits.general, true),
    ...config.appliances.flatMap((appliance) => applianceErrors(appliance, capabilities)),
    ...config.charging.chargers.flatMap((charger) => chargerErrors(charger, capabilities)),
  ];
}

/** Return what is missing before the regulation can start, as the backend does. */
export function missingItems(config: KraftvaktConfig): Issue[] {
  const missing: Issue[] = [];
  if (!config.general.power_sensor) {
    missing.push({ code: "missing_power_sensor", section: "general", field: "power_sensor" });
  }
  missing.push(...config.appliances.flatMap(missingInAppliance));
  if (config.charging.enabled) {
    missing.push(...config.charging.chargers.flatMap((charger) => missingInCharger(charger, config.charging.one_at_a_time)));
  }
  return missing;
}

/** Return what is missing in one appliance. */
export function missingInAppliance(appliance: Appliance): Issue[] {
  return missingEntityAndActions("appliances", appliance, APPLIANCE_ACTIONS);
}

/**
 * Return what is missing in one EV charger. «Car connected» is
 * required when only one EV charger may charge at a time.
 */
export function missingInCharger(charger: Charger, oneAtATime: boolean): Issue[] {
  const missing = missingEntityAndActions("chargers", charger, CHARGER_ACTIONS);
  if (!charger.charge_power_sensor) {
    missing.push({ code: "missing_charge_power_sensor", section: "chargers", target: charger.id, field: "charge_power_sensor" });
  }
  if (oneAtATime && !charger.car_connected) {
    missing.push({ code: "missing_car_connected", section: "chargers", target: charger.id, field: "car_connected" });
  }
  return missing;
}

/** Return whether the domain of the entity has a default action for the field. */
export function hasDefaultAction(
  capabilities: Capabilities,
  section: ActionSection,
  field: string,
  entityId: string | null,
): boolean {
  const domains: string[] = (capabilities.default_actions[section] as Record<string, string[]>)[field] ?? [];
  return entityId !== null && domains.includes(entityId.split(".")[0]);
}

/** Return the issues that belong to one appliance or charger. */
export function issuesFor(issues: Issue[], section: Issue["section"], target: string): Issue[] {
  return issues.filter((issue) => issue.section === section && issue.target === target);
}

export function isMissingAction(action: ActionConfig | null): boolean {
  return action === null || (action.mode === "custom" && (action.action ?? []).length === 0);
}

/** Return the mistakes in one appliance and its variants. */
export function applianceErrors(appliance: Appliance, capabilities: Capabilities): Issue[] {
  const labels = appliance.variants.map((variant) => variant.label.trim());
  return [
    ...rangeIssues("appliances", appliance.id, appliance, capabilities.limits.appliances, false),
    ...defaultActionIssues("appliances", appliance, APPLIANCE_ACTIONS, capabilities),
    ...appliance.variants.flatMap((variant, index) => {
      const prefix = `variants.${variant.id}.`;
      const issues: Issue[] = [];
      if (labels[index] === "") {
        issues.push(applianceIssue(appliance, "empty_label", `${prefix}label`));
      } else if (labels.filter((label) => label === labels[index]).length > 1) {
        issues.push(applianceIssue(appliance, "duplicate_label", `${prefix}label`));
      }
      return [...issues, ...conditionIssues("appliances", appliance.id, `${prefix}condition`, variant.condition)];
    }),
  ];
}

/** Return the mistakes in one EV charger. */
export function chargerErrors(charger: Charger, capabilities: Capabilities): Issue[] {
  const issue = (code: string, field: string): Issue => ({ code, section: "chargers", target: charger.id, field });
  const issues = [
    ...rangeIssues("chargers", charger.id, charger, capabilities.limits.chargers, true),
    ...defaultActionIssues("chargers", charger, CHARGER_ACTIONS, capabilities),
  ];
  if (charger.min_current_a > charger.max_current_a) {
    issues.push(issue("min_current_above_max", "min_current_a"));
  }
  if (charger.car_connected) {
    issues.push(...conditionIssues("chargers", charger.id, "car_connected", charger.car_connected));
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

function conditionIssues(section: Issue["section"], target: string, field: string, condition: Condition): Issue[] {
  return condition.value.trim() === "" ? [{ code: "required", section, target, field }] : [];
}

/**
 * Check the settings that have limits. Optional settings that are not given are
 * only checked when `required` is set.
 */
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
  const steps = value / range.step;
  return Math.abs(steps - Math.round(steps)) < 1e-6 ? undefined : "invalid_resolution";
}

function defaultActionIssues(
  section: ActionSection,
  item: Appliance | Charger,
  fields: readonly string[],
  capabilities: Capabilities,
): Issue[] {
  const actions = item as unknown as Record<string, ActionConfig | null>;
  return fields
    .filter(
      (field) =>
        actions[field]?.mode === "default" &&
        item.entity_id !== null &&
        !hasDefaultAction(capabilities, section, field, item.entity_id),
    )
    .map((field) => ({ code: "default_action_unavailable", section, target: item.id, field }));
}

function missingEntityAndActions(
  section: "appliances" | "chargers",
  item: Appliance | Charger,
  fields: readonly string[],
): Issue[] {
  const actions = item as unknown as Record<string, ActionConfig | null>;
  return [
    ...(item.entity_id ? [] : [{ code: "missing_entity", section, target: item.id, field: "entity_id" }]),
    ...fields
      .filter((field) => isMissingAction(actions[field]))
      .map((field) => ({ code: "missing_action", section, target: item.id, field })),
  ];
}
