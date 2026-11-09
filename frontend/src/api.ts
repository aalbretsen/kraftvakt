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
  section: "general" | "appliances" | "priority" | "charging" | "chargers";
  target?: string;
  field?: string;
}

export interface Condition {
  type: "entity" | "template";
  value: string;
}

export interface ActionConfig {
  mode: "default" | "custom";
  action?: Record<string, unknown>[];
}

export interface GeneralConfig {
  power_sensor: string | null;
  power_limit_w: number;
  turn_on_margin_w: number;
  regulation_window_s: number;
  regulation_interval: number;
  wait_at_limit_s: number;
  wait_curve_steepness: number;
  wait_curve_pivot: number;
  appliance_cycling_step_s: number;
  appliance_cycling_cap_s: number;
  charger_cycling_step_s: number;
  charger_cycling_cap_s: number;
  penalty_threshold_w: number;
}

export interface Variant {
  id: string;
  label: string;
  condition: Condition;
}

export interface Appliance {
  id: string;
  entity_id: string | null;
  turn_on: ActionConfig | null;
  turn_off: ActionConfig | null;
  power_reserve_w: number | null;
  variants: Variant[];
}

export type PriorityEntry =
  | { type: "appliance"; appliance_id: string; variant_id: string | null }
  | { type: "ev_charging" };

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
  charge_power_sensor: string | null;
  power_reserve_w: number;
  car_connected: Condition | null;
  charging_window: ChargingWindow | null;
}

export interface KraftvaktConfig {
  general: GeneralConfig;
  appliances: Appliance[];
  priority: PriorityEntry[];
  charging: {
    enabled: boolean;
    one_at_a_time: boolean;
    chargers: Charger[];
  };
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

export interface Capabilities {
  default_actions: {
    appliances: Record<"turn_on" | "turn_off", string[]>;
    chargers: Record<"activate" | "deactivate" | "set_current", string[]>;
  };
  limits: Record<"general" | "appliances" | "chargers", Record<string, Range>>;
  defaults: {
    general: GeneralConfig;
    appliances: { power_reserve_w: number | null };
    charging: { enabled: boolean; one_at_a_time: boolean };
    chargers: { min_current_a: number; max_current_a: number; power_reserve_w: number };
  };
}

export interface ApplianceStatus {
  id: string;
  name: string;
  on: boolean;
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
  /** How many appliances come before «EV charging», null while EV charging is disabled. */
  ev_charging_position: number | null;
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
