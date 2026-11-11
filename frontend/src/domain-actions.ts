/**
 * Domain actions: services of the entity's domain with values the user
 * chooses. The checks are the same as in the backend's `domain_actions.py`.
 */
import type { ActionConfig, ActionParameter, Capabilities, DomainAction, ParameterValue } from "./api";
import type { HassEntity } from "./types";

type ActionSection = keyof Capabilities["domain_actions"];

export interface ParameterRange {
  min?: number;
  max?: number;
  step?: number;
}

/** Return the domain actions of the field that belong to the domain of the entity, by key. */
export function domainActionsFor(
  capabilities: Capabilities,
  section: ActionSection,
  field: string,
  entityId: string | null,
): Record<string, DomainAction> {
  const actions = (capabilities.domain_actions[section] as Record<string, Record<string, DomainAction>>)[field];
  const domain = entityId?.split(".")[0];
  return Object.fromEntries(Object.entries(actions).filter(([, action]) => action.domain === domain));
}

/** Return the domain action the action is, when it is available for the entity. */
export function availableDomainAction(
  capabilities: Capabilities,
  section: ActionSection,
  field: string,
  entityId: string | null,
  action: ActionConfig | null,
): DomainAction | undefined {
  return action?.domain_action ? domainActionsFor(capabilities, section, field, entityId)[action.domain_action] : undefined;
}

/**
 * Return a value for each parameter: the one in `previous` when it has one,
 * otherwise the default for the entity.
 */
export function initialData(
  action: DomainAction,
  stateObj: HassEntity | undefined,
  previous: Record<string, ParameterValue> = {},
): Record<string, ParameterValue> {
  return Object.fromEntries(
    action.parameters.map((parameter) => [
      parameter.name,
      previous[parameter.name] ?? defaultValue(parameter, stateObj),
    ]),
  );
}

/** Return the options the entity supports, or the preferred ones when it does not tell. */
export function parameterOptions(parameter: ActionParameter, stateObj: HassEntity | undefined): string[] {
  const options = attribute(stateObj, parameter.options_attribute);
  return Array.isArray(options) ? options.map(String) : parameter.preferred_options;
}

/** Return the range of the parameter from the attributes of the entity. */
export function parameterRange(parameter: ActionParameter, stateObj: HassEntity | undefined): ParameterRange {
  return {
    min: numberAttribute(stateObj, parameter.min_attribute),
    max: numberAttribute(stateObj, parameter.max_attribute),
    step: numberAttribute(stateObj, parameter.step_attribute),
  };
}

/** Return the code of what is wrong with each parameter of the action, by name. */
export function parameterIssues(
  action: DomainAction,
  data: Record<string, ParameterValue>,
  stateObj: HassEntity | undefined,
): Record<string, string> {
  const issues: Record<string, string> = {};
  for (const parameter of action.parameters) {
    const code = !(parameter.name in data) ? "required" : valueIssue(parameter, data[parameter.name], stateObj);
    if (code) {
      issues[parameter.name] = code;
    }
  }
  return issues;
}

function valueIssue(
  parameter: ActionParameter,
  value: ParameterValue,
  stateObj: HassEntity | undefined,
): string | undefined {
  if (value === null) {
    return undefined;
  }
  if (parameter.type === "option") {
    const options = attribute(stateObj, parameter.options_attribute);
    return Array.isArray(options) && !options.includes(value) ? "unsupported_option" : undefined;
  }
  const { min, max } = parameterRange(parameter, stateObj);
  return typeof value === "number" && ((min !== undefined && value < min) || (max !== undefined && value > max))
    ? "outside_entity_range"
    : undefined;
}

function defaultValue(parameter: ActionParameter, stateObj: HassEntity | undefined): ParameterValue {
  if (parameter.type === "option") {
    const options = attribute(stateObj, parameter.options_attribute);
    const supported = Array.isArray(options) ? options : parameter.preferred_options;
    return parameter.preferred_options.find((option) => supported.includes(option)) ?? null;
  }
  return parameter.default;
}

function attribute(stateObj: HassEntity | undefined, name: string | null): unknown {
  return name ? stateObj?.attributes[name] : undefined;
}

function numberAttribute(stateObj: HassEntity | undefined, name: string | null): number | undefined {
  const value = attribute(stateObj, name);
  return typeof value === "number" ? value : undefined;
}
