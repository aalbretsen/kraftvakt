import type { ReactiveController, ReactiveControllerHost } from "lit";

/**
 * Whether the host is at most `maxWidth` pixels wide, like a media query on the host instead of the
 * viewport, since Home Assistant's sidebar can take much of the viewport. The host is updated when
 * it crosses the width.
 */
export class WidthQuery implements ReactiveController {
  matches = false;

  private readonly observer = new ResizeObserver(([entry]) => {
    const matches = entry.contentRect.width <= this.maxWidth;
    if (matches !== this.matches) {
      this.matches = matches;
      this.host.requestUpdate();
    }
  });

  constructor(
    private readonly host: ReactiveControllerHost & Element,
    private readonly maxWidth: number,
  ) {
    host.addController(this);
  }

  hostConnected(): void {
    this.observer.observe(this.host);
  }

  hostDisconnected(): void {
    this.observer.disconnect();
  }
}
