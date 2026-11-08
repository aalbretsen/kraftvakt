import { LitElement, css, html, svg } from "lit";
import { customElement, property } from "lit/decorators.js";

const RADIUS = 7;
const LENGTH = 2 * Math.PI * RADIUS;

/**
 * A ring that empties counterclockwise towards the top from `start` to `end`
 * (milliseconds since the epoch).
 *
 * The browser animates it, so it needs no clock and never stops before `end`.
 * It starts again when `start` or `end` changes.
 */
@customElement("kraftvakt-countdown-ring")
export class KraftvaktCountdownRing extends LitElement {
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
    return html`
      <svg viewBox="0 0 18 18" aria-hidden="true">
        ${svg`
          <circle class="track" cx="9" cy="9" r=${RADIUS}></circle>
          <circle class="fill" cx="9" cy="9" r=${RADIUS} stroke-dasharray=${LENGTH} transform="rotate(-90 9 9)"></circle>
        `}
      </svg>
    `;
  }

  protected updated(changed: Map<string, unknown>): void {
    if (changed.has("start") || changed.has("end")) {
      this.startCountdown();
    }
  }

  private startCountdown(): void {
    this.countdown?.cancel();
    const fill = this.renderRoot.querySelector(".fill");
    if (!fill) {
      return;
    }
    const left = Math.max(0, this.end - Date.now());
    const share = Math.min(1, left / Math.max(1, this.end - this.start));
    this.countdown = fill.animate(
      [{ strokeDashoffset: `${LENGTH * (1 - share)}` }, { strokeDashoffset: `${LENGTH}` }],
      { duration: left, easing: "linear", fill: "forwards" },
    );
  }

  static styles = css`
    :host {
      display: inline-block;
      width: 20px;
      height: 20px;
    }
    svg {
      display: block;
      width: 100%;
      height: 100%;
    }
    circle {
      fill: none;
      stroke-width: 3;
    }
    .track {
      stroke: rgba(127, 127, 127, 0.24);
    }
    .fill {
      stroke: var(--primary-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-countdown-ring": KraftvaktCountdownRing;
  }
}
