import { LitElement, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * A bar that empties smoothly towards the end side from `start` to `end`
 * (milliseconds since the epoch).
 *
 * The browser animates it, so it needs no clock and never stops before `end`.
 * It starts again when `start` or `end` changes.
 */
@customElement("kraftvakt-countdown-bar")
export class KraftvaktCountdownBar extends LitElement {
  @property({ type: Number }) start = 0;

  @property({ type: Number }) end = 0;

  private countdown?: Animation;

  connectedCallback(): void {
    super.connectedCallback();
    if (this.hasUpdated) {
      this.startCountdown();
    }
  }

  disconnectedCallback(): void {
    this.countdown?.cancel();
    super.disconnectedCallback();
  }

  protected render() {
    return html`<div class="fill"></div>`;
  }

  protected updated(changed: Map<string, unknown>): void {
    if (changed.has("start") || changed.has("end")) {
      this.startCountdown();
    }
  }

  private startCountdown(): void {
    this.countdown?.cancel();
    const fill = this.renderRoot.querySelector<HTMLElement>(".fill");
    if (!fill) {
      return;
    }
    const left = Math.max(0, this.end - Date.now());
    const share = Math.min(1, left / Math.max(1, this.end - this.start));
    this.countdown = fill.animate([{ transform: `scaleX(${share})` }, { transform: "scaleX(0)" }], {
      duration: left,
      easing: "linear",
      fill: "forwards",
    });
  }

  static styles = css`
    :host {
      display: block;
      height: 6px;
      border-radius: 3px;
      overflow: hidden;
      background: rgba(127, 127, 127, 0.24);
    }
    .fill {
      height: 100%;
      background: var(--primary-color);
      transform-origin: right;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-countdown-bar": KraftvaktCountdownBar;
  }
}
