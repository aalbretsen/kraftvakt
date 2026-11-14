/** Builders of complete configurations and of the parts of Home Assistant the panel reads, for the panel's tests. */
import type { ActionConfig, Appliance, Capabilities, Charger, ChargerGroup, KraftvaktConfig, Variant } from "../src/api";
import { chargerDeviceEntities } from "../src/charger-device";
import type { HassEntity, HomeAssistant } from "../src/types";
import capabilities from "./fixtures/capabilities.json";

/** The capabilities the backend sends, from the fixture its tests keep in step with it. */
export const CAPABILITIES = capabilities as unknown as Capabilities;

export const DEFAULT_ACTION: ActionConfig = { mode: "default" };

export function config(parts: Partial<KraftvaktConfig> = {}): KraftvaktConfig {
  return {
    general: { ...CAPABILITIES.defaults.general, power_sensor: "sensor.house_power" },
    appliances: [],
    priority: [],
    charger_groups: [],
    ...parts,
  };
}

export function appliance(id: string, parts: Partial<Appliance> = {}): Appliance {
  return { id, entity_id: `switch.${id}`, turn_on: DEFAULT_ACTION, turn_off: DEFAULT_ACTION, power_reserve_w: null, variants: [], ...parts };
}

export function variant(id: string, parts: Partial<Variant> = {}): Variant {
  return { id, label: id, condition: { type: "template", value: "{{ true }}" }, actions: {}, ...parts };
}

/** A complete charger, whose entities are on its device `device_<id>`. */
export function charger(id: string, parts: Partial<Charger> = {}): Charger {
  return {
    id,
    device_id: `device_${id}`,
    entity_id: `switch.${id}`,
    activate: DEFAULT_ACTION,
    deactivate: DEFAULT_ACTION,
    set_current: { mode: "entity", entity_id: `number.${id}_current` },
    min_current_a: 6,
    max_current_a: 16,
    power_reserve_w: 4000,
    car_connected: { type: "entity", value: `binary_sensor.${id}_car` },
    actively_charging: { type: "entity", value: `binary_sensor.${id}_charging` },
    charging_window: null,
    finish_after_window: false,
    override_ends: "manual",
    ...parts,
  };
}

export function group(id: string, chargers: Charger[], parts: Partial<ChargerGroup> = {}): ChargerGroup {
  return { id, name: id, one_at_a_time: true, chargers, ...parts };
}

/** Home Assistant with the given states, and the devices of the chargers with their entities on them. */
export function hass(states: Record<string, HassEntity> = {}, chargers: Charger[] = []): HomeAssistant {
  const onDevice = chargers.flatMap((item) => chargerDeviceEntities(item).map(([, entityId]) => [entityId, item.device_id] as const));
  return {
    language: "en",
    states,
    entities: Object.fromEntries(onDevice.map(([entityId, deviceId]) => [entityId, { entity_id: entityId, device_id: deviceId }])),
    devices: Object.fromEntries(chargers.map((item) => [item.device_id, { name: item.id, name_by_user: null }])),
  } as unknown as HomeAssistant;
}

export function state(value: string, attributes: Record<string, unknown> = {}): HassEntity {
  return { state: value, attributes };
}
