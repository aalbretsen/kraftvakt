/**
 * Types and WebSocket calls for Kraftvakt's commands.
 *
 * The status subscription is the one source of how the regulation stands. Its
 * events may arrive before the reply to a command that changed the status, so
 * the replies are not used to update what the panel shows.
 */
import type { HomeAssistant } from "./types";

/** A validation error or a missing setting. */
export interface Issue {
  code: string;
  section: "general" | "appliances" | "priority" | "charger_groups" | "chargers";
  target?: string;
  field?: string;
}

export interface Condition {
  /** A power sensor is only used for whether an EV charger is actively charging. */
  type: "entity" | "template" | "power_sensor";
  value: string;
}

export interface ActionConfig {
  mode: "default" | "custom" | "entity" | "domain";
  action?: Record<string, unknown>[];
  entity_id?: string | null;
  /** The key of the domain action, and its value per parameter, null while not chosen. */
  domain_action?: string;
  data?: Record<string, ParameterValue>;
}

export type ParameterValue = string | number | null;

export interface GeneralConfig {
  power_sensor: string | null;
  power_limit_w: number;
  turn_on_margin_w: number;
  regulation_window_s: number;
  regulation_interval: number;
  wait_at_limit_s: number;
  wait_curve_steepness: number;
  wait_curve_pivot: number;
  appliance_cycling_step_factor: number;
  appliance_cycling_steps: number;
  charger_cycling_step_factor: number;
  charger_cycling_steps: number;
  penalty_threshold_w: number;
  command_repeat_interval_min: number;
}

export interface Variant {
  id: string;
  label: string;
  condition: Condition;
}

export interface ApplianceActions {
  turn_on: ActionConfig | null;
  turn_off: ActionConfig | null;
}

/** The key of the appliance's own actions in `Appliance.actions`. */
export const MAIN_ACTIONS = "main";

export interface Appliance {
  id: string;
  entity_id: string | null;
  /**
   * Both actions of the appliance under `MAIN_ACTIONS`, and under the id of a
   * variant the actions the variant overrides. A variant uses the
   * appliance's action for each action it does not override.
   */
  actions: Record<string, Partial<ApplianceActions>>;
  power_reserve_w: number | null;
  variants: Variant[];
}

export type PriorityEntry =
  | { type: "appliance"; appliance_id: string; variant_id: string | null }
  | { type: "charger_group"; group_id: string };

export interface ChargingWindow {
  start: string;
  end: string;
}

export interface Charger {
  id: string;
  entity_id: string | null;
  activate: ActionConfig | null;
  deactivate: ActionConfig | null;
  set_current: ActionConfig | null;
  min_current_a: number;
  max_current_a: number;
  power_reserve_w: number;
  car_connected: Condition | null;
  actively_charging: Condition | null;
  charging_window: ChargingWindow | null;
}

/** A named group of EV chargers with its own place in the priority list. */
export interface ChargerGroup {
  id: string;
  name: string;
  one_at_a_time: boolean;
  /** In the configured charging priority. */
  chargers: Charger[];
}

export interface KraftvaktConfig {
  general: GeneralConfig;
  appliances: Appliance[];
  priority: PriorityEntry[];
  charger_groups: ChargerGroup[];
}

export interface ConfigResponse {
  config: KraftvaktConfig;
  entity_names: Record<string, string>;
  missing: Issue[];
}

export type SaveResponse =
  | { saved: true; config: KraftvaktConfig; missing: Issue[] }
  | { saved: false; errors: Issue[] };

export interface Range {
  min: number | null;
  max: number | null;
  step: number;
}

/** The action used for the entity domains that have an obvious one. */
export interface DefaultAction {
  domains: string[];
  service: string;
  data: Record<string, string>;
}

/**
 * A value of a domain action. The options and the range are read from the
 * attributes of the entity, when it has them.
 */
export interface ActionParameter {
  name: string;
  type: "option" | "temperature";
  options_attribute: string | null;
  /** The default option is the first of these the entity supports. */
  preferred_options: string[];
  min_attribute: string | null;
  max_attribute: string | null;
  step_attribute: string | null;
  default: number | null;
}

/** A service of an entity domain, called for the entity with the chosen values. */
export interface DomainAction {
  domain: string;
  service: string;
  parameters: ActionParameter[];
}

type ActionFields<T> = {
  appliances: Record<"turn_on" | "turn_off", T>;
  chargers: Record<"activate" | "deactivate" | "set_current", T>;
};

export interface Capabilities {
  default_actions: ActionFields<DefaultAction>;
  /** The domain actions of each field, by key. */
  domain_actions: ActionFields<Record<string, DomainAction>>;
  limits: Record<"general" | "appliances" | "chargers", Record<string, Range>>;
  defaults: {
    general: GeneralConfig;
    appliances: { power_reserve_w: number | null };
    charger_groups: { one_at_a_time: boolean };
    chargers: { min_current_a: number; max_current_a: number; power_reserve_w: number };
  };
}

export interface ApplianceStatus {
  id: string;
  name: string;
  on: boolean;
  /** Excluded from the regulation at the last decision. */
  excluded: boolean;
  variant: string | null;
  waiting_since: string | null;
  waiting_until: string | null;
  /** The decision that ends the waiting: the first at or after `waiting_until`. */
  waiting_ends_at: string | null;
}

export interface ChargerStatus {
  id: string;
  name: string;
  activated: boolean;
  current_a: number | null;
  bypassed: boolean;
  waiting: boolean;
  allowed: boolean;
  excluded: boolean | null;
  /** Activated and actively charging at the last decision. */
  charging: boolean;
  /** Allowed to charge only because its charging window is overridden. */
  window_overridden: boolean;
  /** «Car connected» at the last decision, null when it is not set or before the first decision. */
  car_connected: boolean | null;
  waiting_since: string | null;
  waiting_until: string | null;
  /** The decision that ends the waiting: the first at or after `waiting_until`. */
  waiting_ends_at: string | null;
}

/** How the regulation stands now. Times are ISO 8601. */
export interface StatusSnapshot {
  running: boolean;
  missing: Issue[];
  safe_state: boolean;
  penalty: {
    active: boolean;
    overconsumption_wh: number;
    recovery_started: boolean;
  };
  regulation_average_w: number | null;
  capacity_average_w: number | null;
  power_limit_w: number;
  regulation_window_s: number;
  regulation_interval: number;
  next_decision_at: string | null;
  appliances: ApplianceStatus[];
  /** The groups in the order of their entries. */
  charger_groups: ChargerGroupStatus[];
}

export interface ChargerGroupStatus {
  id: string;
  name: string;
  /** How many appliances come before the group. */
  position: number;
  /** In the current charging priority. */
  chargers: ChargerStatus[];
}

/** The error Home Assistant gives when a command fails. */
export interface CommandError {
  code: string;
  message: string;
}

/** The error codes of Kraftvakt's commands. */
export const ERROR_NOT_LOADED = "not_loaded";
export const ERROR_REGULATION_RUNNING = "regulation_running";
export const ERROR_CONFIG_INCOMPLETE = "config_incomplete";

export function isCommandError(error: unknown): error is CommandError {
  return typeof error === "object" && error !== null && "code" in error && "message" in error;
}

/** Return the message of an error from a command, or the error as text. */
export function errorMessage(error: unknown): string {
  return isCommandError(error) ? error.message : String(error);
}

export const fetchCapabilities = (hass: HomeAssistant) =>
  hass.callWS<Capabilities>({ type: "kraftvakt/capabilities" });

export const fetchConfig = (hass: HomeAssistant) => hass.callWS<ConfigResponse>({ type: "kraftvakt/config/get" });

export const saveConfig = (hass: HomeAssistant, config: KraftvaktConfig) =>
  hass.callWS<SaveResponse>({ type: "kraftvakt/config/save", config });

export const setRunning = (hass: HomeAssistant, running: boolean) =>
  hass.callWS<{ running: boolean }>({ type: "kraftvakt/regulation/set_running", running });

/** Get the status now and at each change, until the returned function is called. */
export const subscribeStatus = (hass: HomeAssistant, onStatus: (status: StatusSnapshot) => void) =>
  hass.connection.subscribeMessage<StatusSnapshot>(onStatus, { type: "kraftvakt/status/subscribe" });
