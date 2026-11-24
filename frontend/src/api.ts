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

/**
 * Where an appliance's display temperature comes from: a temperature sensor,
 * or the current or set temperature of a thermostat, its climate entity.
 */
export interface TemperatureSource {
  type: "temperature_sensor" | "current_temperature" | "target_temperature";
  entityId: string;
}

export interface Condition {
  /**
   * A power sensor gives a power, for the charging power of an EV charger and the display power of an appliance.
   * A temperature sensor, or a thermostat's current or target temperature, gives the display temperature of an appliance.
   * A state is only for an EV charger.
   */
  type: "entity" | "state" | "template" | "power_sensor" | TemperatureSource["type"];
  /** The entity, or the template. */
  value: string;
  /** The chosen states of the entity, for a state. */
  states?: string[];
  /** Whether the chosen states count as true, or every other state does. */
  states_are_true?: boolean;
}

export interface ActionConfig {
  mode: "default" | "custom" | "entity" | "domain";
  action?: Record<string, unknown>[];
  entity_id?: string | null;
  /** The key of the domain action, and its value per parameter, null while not chosen. */
  domain_action?: string;
  data?: Record<string, ParameterValue>;
}

/**
 * A temperature given as a string is a template, rendered when the action runs,
 * and a temperature source is read when the action runs.
 */
export type ParameterValue = string | number | ParameterSource | null;

/** An entity whose temperature a domain action sets, of the same types as a display temperature; the entity is null until it is chosen. */
export interface ParameterSource {
  type: TemperatureSource["type"];
  value: string | null;
}

export interface GeneralConfig {
  power_sensor: string | null;
  power_limit_w: number;
  turn_on_margin_w: number;
  /** The number of updates of the power sensor in a regulation window, null until the power sensor is chosen and measured. */
  regulation_window_updates: number | null;
  /** How often the power sensor reports, in seconds, as the backend measured it when the sensor was chosen. */
  power_sensor_interval_s: number | null;
  wait_at_limit_s: number;
  wait_curve_steepness: number;
  wait_curve_pivot: number;
  appliance_repeat_increment_factor: number;
  appliance_repeat_increments: number;
  ampere_damping_s: number;
  /** How many times the waiting time of appliances an EV charger activated again waits. */
  charger_waiting_factor: number;
  penalty_threshold_w: number;
  command_repeat_interval_min: number;
  action_timeout_s: number;
  power_sensor_timeout_s: number;
}

export interface ApplianceActions {
  turn_on: ActionConfig | null;
  turn_off: ActionConfig | null;
}

export interface Variant {
  id: string;
  label: string;
  condition: Condition;
  /** Only the actions the variant overrides, null while one is not set. */
  actions: Partial<ApplianceActions>;
}

export interface Appliance extends ApplianceActions {
  id: string;
  entity_id: string | null;
  /** Kept on, and turned off only in a penalty. Has no variants, and sits above every other entry in the priority list. */
  essential: boolean;
  power_reserve_w: number | null;
  variants: Variant[];
  /** Only shown on the status page. */
  display_power: Condition | null;
  display_temperature: Condition | null;
}

export type PriorityEntry = { type: "appliance"; appliance_id: string; variant_id: string | null } | { type: "charger_group"; group_id: string };

export interface ChargingWindow {
  start: string;
  end: string;
}

export const SWITCHED_BY = ["on_off_entity", "current", "actions"] as const;
/** How the EV charger turns charging on and off: by the default actions of its on/off entity, by custom actions, or by the charging current, 0 A being off. */
export type SwitchedBy = (typeof SWITCHED_BY)[number];

/** An EV charger, a device in Home Assistant. Its on/off entity and actions are kept while it is switched another way. */
export interface Charger {
  id: string;
  device_id: string | null;
  switched_by: SwitchedBy;
  on_off_entity: string | null;
  /** Custom actions. */
  activate: ActionConfig | null;
  deactivate: ActionConfig | null;
  /** An entity or a custom action. */
  set_current: ActionConfig | null;
  min_current_a: number;
  max_current_a: number;
  /** What the car draws at the minimum current. */
  min_current_power_w: number;
  car_connected: Condition | null;
  /** An optional condition that is true while the car charges. */
  actively_charging: Condition | null;
  /** A power sensor or a template giving the charging power. Every EV charger needs one. */
  charging_power: Condition | null;
  charging_window: ChargingWindow | null;
  /** Whether a car that has used power within the charging window may go on charging after it until it is disconnected. */
  charge_until_disconnected: boolean;
  /** What ends the override of the charging window, besides the user. */
  override_ends: OverrideEnd;
  /** Whether the EV charger is controlled through a cloud service. */
  cloud_controlled: boolean;
  /** How long the car may take from activation until it draws power. Nothing below the EV charger is turned on meanwhile. */
  start_delay_s: number;
  /** Whether the EV charger is deactivated while a fault flag shows a fault. */
  deactivate_on_fault: boolean;
  /** Tells that the EV charger has a fault. Kept while deactivate on fault is off. */
  fault_flag: Condition | null;
}

export const OVERRIDE_ENDS = ["manual", "charging_stopped", "car_disconnected"] as const;
export type OverrideEnd = (typeof OVERRIDE_ENDS)[number];

/** A named group of EV chargers with its own place in the priority list. */
export interface ChargerGroup {
  id: string;
  name: string;
  /** Always, never, or while the condition is true at a decision. */
  one_at_a_time: boolean | Condition;
  /** Whether a charger that charges keeps its place ahead of a car connected later. */
  dynamic_order: boolean;
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

export type SaveResponse = { saved: true; config: KraftvaktConfig; missing: Issue[] } | { saved: false; errors: Issue[] };

export interface Range {
  min: number | null;
  max: number | null;
  resolution: number;
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
  /** Whether the panel chooses it for a new entity of its domain, before the default action. */
  suggested: boolean;
}

type ApplianceActionFields<T> = Record<"turn_on" | "turn_off", T>;

export interface Capabilities {
  default_actions: { appliances: ApplianceActionFields<DefaultAction>; chargers: Record<"activate" | "deactivate" | "set_current", DefaultAction> };
  /** The domain actions of each field of an appliance, by key. */
  domain_actions: { appliances: ApplianceActionFields<Record<string, DomainAction>> };
  limits: Record<"general" | "appliances" | "chargers", Record<string, Range>>;
  /** The shortest and longest regulation window in seconds, and at most how many lengths to choose from. */
  regulation_window: { seconds: Range; choices: number };
  defaults: {
    general: GeneralConfig;
    appliances: { power_reserve_w: number | null };
    charger_groups: { one_at_a_time: boolean; dynamic_order: boolean };
    chargers: {
      switched_by: SwitchedBy;
      min_current_a: number;
      max_current_a: number;
      min_current_power_w: number;
      override_ends: OverrideEnd;
      cloud_controlled: boolean;
      start_delay_s: number;
    };
  };
}

/** Why the next step waits: its waiting time, the damping of an EV charger's ampere step, or the start delay of an EV charger above it. */
export type WaitingReason = "waiting_time" | "damping" | "start_delay";

/** When the next step started to wait, when it ends, and why: on the row of its appliance, or of the EV charger whose ampere step waits or whose start delay holds it back. */
export interface WaitingFields {
  waiting_since: string | null;
  waiting_until: string | null;
  /** The decision that ends the waiting: the first at or after `waiting_until`. */
  waiting_ends_at: string | null;
  waiting_reason: WaitingReason | null;
}

export interface ApplianceStatus extends WaitingFields {
  type: "appliance";
  id: string;
  name: string;
  essential: boolean;
  on: boolean;
  /** Excluded from the regulation at the last decision. */
  excluded: boolean;
  variant: string | null;
  /** The display power in W, null without one or without a valid value. */
  power_w: number | null;
  /** The display temperature, null without one or without a valid value. */
  temperature: { value: number; unit: string } | null;
  /** How far the regulation average must drop before the appliance, as the next step, may be turned on. */
  power_to_free_w: number | null;
}

/** How an EV charger stands after the last decision, the most important first. */
export type ChargerState =
  "stopped" | "fault" | "first_decision" | "no_car" | "excluded" | "outside_window" | "queued" | "starting" | "charging" | "activated" | "override" | "deactivated";

export interface ChargerStatus extends WaitingFields {
  id: string;
  name: string;
  state: ChargerState;
  activated: boolean;
  current_a: number | null;
  /** The charging power in W, null without one or without a valid value. */
  power_w: number | null;
  bypassed: boolean;
  /** Activated and actively charging at the last decision. */
  charging: boolean;
  /** When the start delay of a starting EV charger ends. Nothing below it is turned on until then. */
  starting_until: string | null;
  /** How far the regulation average must drop before the next ampere step of the EV charger, as the next step, may be turned on. */
  power_to_free_w: number | null;
}

/** How the regulation stands now. Times are ISO 8601. */
export interface StatusSnapshot {
  running: boolean;
  /** Changes each time the stored configuration changes. */
  config_version: number;
  missing: Issue[];
  safe_state: boolean;
  penalty: {
    active: boolean;
    overconsumption_wh: number;
    recovery_started: boolean;
  };
  regulation_average_w: number | null;
  tariff_average_w: number | null;
  power_limit_w: number;
  regulation_window_s: number;
  next_decision_at: string | null;
  /** The priority list, with each appliance at the entry of its current variant. */
  priority: (ApplianceStatus | ChargerGroupStatus)[];
}

export interface ChargerGroupStatus {
  type: "charger_group";
  id: string;
  name: string;
  /** Whether the group was restricted to one EV charger at a time at the last decision. */
  one_at_a_time: boolean;
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

export const fetchCapabilities = (hass: HomeAssistant) => hass.callWS<Capabilities>({ type: "kraftvakt/capabilities" });

/** The charger profile of a device, null without one, and the fields of a charger it fills: without one, those of the default profile. */
export interface ChargerProfileFields {
  profile: string | null;
  fields: Partial<Charger>;
}

export const fetchChargerProfile = (hass: HomeAssistant, deviceId: string) => hass.callWS<ChargerProfileFields>({ type: "kraftvakt/charger_profile/get", device_id: deviceId });

export const fetchConfig = (hass: HomeAssistant) => hass.callWS<ConfigResponse>({ type: "kraftvakt/config/get" });

/** Measure how often the power sensor reports, which may take up to 30 seconds. */
export const measurePowerSensorInterval = (hass: HomeAssistant, entityId: string) =>
  hass.callWS<{ interval_s: number | null }>({ type: "kraftvakt/power_sensor/interval", entity_id: entityId });

export const saveConfig = (hass: HomeAssistant, config: KraftvaktConfig) => hass.callWS<SaveResponse>({ type: "kraftvakt/config/save", config });

export const setRunning = (hass: HomeAssistant, running: boolean) => hass.callWS<{ running: boolean }>({ type: "kraftvakt/regulation/set_running", running });

/** Get the status now and at each change, until the returned function is called. */
export const subscribeStatus = (hass: HomeAssistant, onStatus: (status: StatusSnapshot) => void) =>
  hass.connection.subscribeMessage<StatusSnapshot>(onStatus, { type: "kraftvakt/status/subscribe" });

/** A command of a decision, as the backend keeps it. */
export type DecisionCommand =
  | { command: "TurnOnAppliance" | "TurnOffAppliance"; appliance_id: string; variant_id: string | null }
  | { command: "ActivateCharger" | "DeactivateCharger"; charger_id: string }
  | { command: "SetChargingCurrent"; charger_id: string; current_a: number };

/** The step that waits: an appliance, or an ampere step of an EV charger counted from 0. */
export type WaitingStep = { appliance_id: string } | { charger_id: string; index: number };

/** A decision, as the backend keeps the last ones. */
export interface DecisionRecord {
  time: string;
  regulation_average_w: number | null;
  tariff_average_w: number | null;
  power_sensor_valid: boolean;
  safe_state: boolean;
  penalty_active: boolean;
  overconsumption_wh: number;
  waiting: { key: WaitingStep; started_at: string; until: string; reason: WaitingReason } | null;
  commands: DecisionCommand[];
}

export interface FailedAction {
  time: string;
  /** What should have been done and to which entity, in English, like `turn_on light.hall`. */
  action: string;
  error: string;
}

/** The power in W from `start` until the next measurement starts. */
export interface Measurement {
  start: string;
  power_w: number;
}

/**
 * Items the backend keeps, sent in parts. A part replaces what the panel holds, or holds the items
 * from the first one that may have changed; items before `kept_from` are no longer kept.
 */
export interface DiagnosticsPart<Item> {
  replace: boolean;
  kept_from: string | null;
  items: Item[];
}

/** What the diagnostics page shows of what Kraftvakt holds in memory. Times are ISO 8601. */
export interface DiagnosticsEvent {
  /** When the regulation last started, null while it is stopped. */
  started_at: string | null;
  power_sensor: {
    valid: boolean;
    /** The update interval of the current window. */
    update_interval_s: number | null;
    /** How often the power sensor reports, when it no longer reports at its update interval. */
    reported_interval_s: number | null;
    last_missed_windows: { start: string; end: string } | null;
  };
  /** Commands that wait for an action that runs. */
  queued_commands: number;
  /** When each appliance and EV charger, by id, gets its command again. */
  repeats_due_at: { appliances: Record<string, string>; chargers: Record<string, string> };
  measurements: DiagnosticsPart<Measurement>;
  decisions: DiagnosticsPart<DecisionRecord>;
  /** The commands that set the appliances and EV chargers before the decisions kept: those of the last start, with the decisions that have left the hour. */
  commands_before_decisions: CommandsBefore | null;
  failed_actions: FailedAction[];
}

export interface CommandsBefore {
  /** When the last of the commands was sent. */
  time: string;
  commands: DecisionCommand[];
}

/** Get what the diagnostics page shows now and at each change of the status, until the returned function is called. */
export const subscribeDiagnostics = (hass: HomeAssistant, onEvent: (event: DiagnosticsEvent) => void) =>
  hass.connection.subscribeMessage<DiagnosticsEvent>(onEvent, { type: "kraftvakt/diagnostics/subscribe" });
