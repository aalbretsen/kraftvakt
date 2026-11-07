import type { ReactiveController, ReactiveControllerHost } from "lit";

/** Updates its host every second while the host is connected, for countdowns. */
export class ClockController implements ReactiveController {
  now = Date.now();

  private timer?: number;

  constructor(private readonly host: ReactiveControllerHost) {
    host.addController(this);
  }

  hostConnected(): void {
    this.timer = window.setInterval(() => {
      this.now = Date.now();
      this.host.requestUpdate();
    }, 1000);
  }

  hostDisconnected(): void {
    window.clearInterval(this.timer);
  }
}
