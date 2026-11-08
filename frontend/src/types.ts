/** The parts of Home Assistant's frontend objects that the panel uses. */

export interface Connection {
  subscribeMessage<Event>(
    callback: (event: Event) => void,
    message: { type: string; [key: string]: unknown },
  ): Promise<() => Promise<void>>;
}

export interface HassEntity {
  state: string;
  attributes: { friendly_name?: string; [key: string]: unknown };
}

/** An entry of the entity registry, as the frontend has it. */
export interface EntityRegistryEntry {
  entity_id: string;
  platform?: string;
  device_id?: string | null;
}

/** An entry of the device registry, as the frontend has it. */
export interface DeviceRegistryEntry {
  name: string | null;
  name_by_user: string | null;
}

export interface HomeAssistant {
  language: string;
  states: Record<string, HassEntity>;
  entities: Record<string, EntityRegistryEntry>;
  devices: Record<string, DeviceRegistryEntry>;
  locale: { language: string };
  connection: Connection;
  callWS<Result>(message: { type: string; [key: string]: unknown }): Promise<Result>;
  loadFragmentTranslation(fragment: string): Promise<unknown>;
}

/** The part of the address that belongs to the panel, like `/status`. */
export interface Route {
  prefix: string;
  path: string;
}
