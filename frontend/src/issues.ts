import type { ConfigResponse, Issue } from "./api";
import type { Localize, TranslationKey } from "./localize";
import type { Page } from "./navigation";

const ISSUE_TEXTS: Record<string, TranslationKey> = {
  missing_power_sensor: "missing.missing_power_sensor",
  missing_entity: "missing.missing_entity",
  missing_action: "missing.missing_action",
  missing_charge_power_sensor: "missing.missing_charge_power_sensor",
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

/** Return the page where the issue is fixed (GUI-005). */
export function pageForIssue(issue: Issue): Page {
  return ISSUE_PAGES[issue.section];
}

/** Describe a missing setting or a validation error to the user (3.4, GUI-005). */
export function describeIssue(issue: Issue, config: ConfigResponse | undefined, localize: Localize): string {
  const params = {
    item: itemName(issue, config, localize),
    action: issue.field && ACTION_TEXTS[issue.field] ? localize(ACTION_TEXTS[issue.field]) : (issue.field ?? ""),
    code: issue.code,
  };
  return localize(ISSUE_TEXTS[issue.code] ?? "missing.unknown", params);
}

/** Return the name of the appliance or charger the issue is about (GEN-013). */
function itemName(issue: Issue, config: ConfigResponse | undefined, localize: Localize): string {
  const items = issue.section === "chargers" ? config?.config.charging.chargers : config?.config.appliances;
  const entityId = items?.find((item) => item.id === issue.target)?.entity_id;
  if (entityId) {
    return config?.entity_names[entityId] ?? entityId;
  }
  return localize(issue.section === "chargers" ? "missing.charger_without_entity" : "missing.appliance_without_entity");
}
