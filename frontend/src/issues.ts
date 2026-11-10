import type { Capabilities, ConfigResponse, Issue } from "./api";
import type { Localize, TranslationKey } from "./localize";
import type { Page } from "./navigation";

const ISSUE_TEXTS: Record<string, TranslationKey> = {
  missing_power_sensor: "missing.missing_power_sensor",
  missing_entity: "missing.missing_entity",
  missing_action: "missing.missing_action",
  missing_charge_power_sensor: "missing.missing_charge_power_sensor",
  missing_car_connected: "missing.missing_car_connected",
};

const ACTION_TEXTS: Record<string, TranslationKey> = {
  turn_on: "missing.actions.turn_on",
  turn_off: "missing.actions.turn_off",
  activate: "missing.actions.activate",
  deactivate: "missing.actions.deactivate",
  set_current: "missing.actions.set_current",
};

const ISSUE_PAGES: Record<Issue["section"], Page> = {
  general: "general",
  appliances: "appliances",
  priority: "appliances",
  charging: "charging",
  chargers: "charging",
};

/** The general settings that are on the advanced page. */
const ADVANCED_FIELDS = new Set([
  "wait_curve_steepness",
  "wait_curve_pivot",
  "appliance_cycling_step_factor",
  "appliance_cycling_steps",
  "charger_cycling_step_factor",
  "charger_cycling_steps",
]);

/** Return the page where the issue is fixed. */
export function pageForIssue(issue: Issue): Page {
  if (issue.section === "general" && issue.field && ADVANCED_FIELDS.has(issue.field)) {
    return "advanced";
  }
  return ISSUE_PAGES[issue.section];
}

/** Describe a missing setting or a validation error to the user. */
export function describeIssue(issue: Issue, config: ConfigResponse | undefined, localize: Localize): string {
  const params = {
    item: itemName(issue, config, localize),
    action: issue.field && ACTION_TEXTS[issue.field] ? localize(ACTION_TEXTS[issue.field]) : (issue.field ?? ""),
    code: issue.code,
  };
  return localize(ISSUE_TEXTS[issue.code] ?? "missing.unknown", params);
}

function itemName(issue: Issue, config: ConfigResponse | undefined, localize: Localize): string {
  const items = issue.section === "chargers" ? config?.config.charging.chargers : config?.config.appliances;
  const entityId = items?.find((item) => item.id === issue.target)?.entity_id;
  if (entityId) {
    return config?.entity_names[entityId] ?? entityId;
  }
  return localize(issue.section === "chargers" ? "missing.charger_without_entity" : "missing.appliance_without_entity");
}

const ERROR_TEXTS: Record<string, TranslationKey> = {
  required: "errors.required",
  missing_power_sensor: "errors.required",
  missing_entity: "errors.required",
  missing_action: "errors.required",
  missing_charge_power_sensor: "errors.required",
  missing_car_connected: "errors.car_connected_required",
  not_integer: "errors.not_integer",
  invalid_entity_id: "errors.invalid_entity_id",
  empty_label: "errors.empty_label",
  duplicate_label: "errors.duplicate_label",
  min_current_above_max: "errors.min_current_above_max",
  invalid_time: "errors.invalid_time",
  window_start_equals_end: "errors.window_start_equals_end",
  duplicate_entity: "errors.duplicate_entity",
  invalid_action: "errors.invalid_action",
  invalid_template: "errors.invalid_template",
  default_action_unavailable: "errors.default_action_unavailable",
  unsupported_entity_domain: "errors.unsupported_entity_domain",
};

const LIMIT_SECTIONS: Partial<Record<Issue["section"], keyof Capabilities["limits"]>> = {
  general: "general",
  appliances: "appliances",
  chargers: "chargers",
};

/** Describe what is wrong with a field, next to the field. */
export function fieldErrorText(
  issue: Issue,
  localize: Localize,
  capabilities: Capabilities | undefined,
  language: string,
): string {
  const limitSection = LIMIT_SECTIONS[issue.section];
  const range = limitSection && issue.field ? capabilities?.limits[limitSection][issue.field] : undefined;
  const number = (value: number | null) => (value === null ? "" : new Intl.NumberFormat(language).format(value));
  if (issue.code === "out_of_range" && range) {
    return range.max === null
      ? localize("errors.at_least", { min: number(range.min) })
      : localize("errors.out_of_range", { min: number(range.min), max: number(range.max) });
  }
  if (issue.code === "invalid_resolution" && range) {
    return localize("errors.invalid_resolution", { step: number(range.step) });
  }
  return localize(ERROR_TEXTS[issue.code] ?? "errors.unknown", { code: issue.code });
}

/**
 * Return the error text per field, for `ha-form`, of the issues whose field
 * starts with `prefix`. The prefix is left out of the field names.
 */
export function errorsByField(
  issues: Issue[],
  prefix: string,
  describe: (issue: Issue) => string,
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const issue of issues) {
    if (issue.field?.startsWith(prefix)) {
      errors[issue.field.slice(prefix.length)] ??= describe(issue);
    }
  }
  return errors;
}
