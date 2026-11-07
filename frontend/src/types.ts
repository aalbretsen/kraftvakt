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

export interface HomeAssistant {
  language: string;
  states: Record<string, HassEntity>;
  locale: { language: string };
  connection: Connection;
  callWS<Result>(message: { type: string; [key: string]: unknown }): Promise<Result>;
}

/** The part of the address that belongs to the panel, like `/status`. */
export interface Route {
  prefix: string;
  path: string;
}
