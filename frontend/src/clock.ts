import type { ReactiveController, ReactiveControllerHost } from "lit";

/**
 * Updates its host every second while the host is connected, for countdowns.
 * `now` is read when the host renders, so a countdown is right also when the
 * host renders between the ticks, for example for a new status.
 */
export class ClockController implements ReactiveController {
  private timer?: number;

  constructor(private readonly host: ReactiveControllerHost) {
    host.addController(this);
  }

  hostConnected(): void {
    this.timer = window.setInterval(() => this.host.requestUpdate(), 1000);
  }

  get now(): number {
    return Date.now();
  }

  hostDisconnected(): void {
    window.clearInterval(this.timer);
  }
}
