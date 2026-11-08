import { LitElement, css, html, svg } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * A countdown from `start` to `end` (milliseconds since the epoch).
 *
 * The browser animates it, so it needs no clock and never stops before `end`.
 * It starts again when `start` or `end` changes.
 */
abstract class KraftvaktCountdown extends LitElement {
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

  protected updated(changed: Map<string, unknown>): void {
    if (changed.has("start") || changed.has("end")) {
      this.startCountdown();
    }
  }

  /** The keyframes from the share of the time left now down to nothing left. */
  protected abstract keyframes(share: number): Keyframe[];

  private startCountdown(): void {
    this.countdown?.cancel();
    const fill = this.renderRoot.querySelector<Element>(".fill");
    if (!fill) {
      return;
    }
    const left = Math.max(0, this.end - Date.now());
    const share = Math.min(1, left / Math.max(1, this.end - this.start));
    this.countdown = fill.animate(this.keyframes(share), { duration: left, easing: "linear", fill: "forwards" });
  }
}

/** A bar that empties towards the right. */
@customElement("kraftvakt-countdown-bar")
export class KraftvaktCountdownBar extends KraftvaktCountdown {
  protected render() {
    return html`<div class="fill"></div>`;
  }

  protected keyframes(share: number): Keyframe[] {
    return [{ transform: `scaleX(${share})` }, { transform: "scaleX(0)" }];
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

const RING_RADIUS = 7;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;

/** A ring that empties counterclockwise towards the top. */
@customElement("kraftvakt-countdown-ring")
export class KraftvaktCountdownRing extends KraftvaktCountdown {
  protected render() {
    return html`
      <svg viewBox="0 0 18 18" aria-hidden="true">
        ${svg`
          <circle class="track" cx="9" cy="9" r=${RING_RADIUS}></circle>
          <circle
            class="fill"
            cx="9"
            cy="9"
            r=${RING_RADIUS}
            stroke-dasharray=${RING_LENGTH}
            transform="rotate(-90 9 9)"
          ></circle>
        `}
      </svg>
    `;
  }

  protected keyframes(share: number): Keyframe[] {
    return [{ strokeDashoffset: `${RING_LENGTH * (1 - share)}` }, { strokeDashoffset: `${RING_LENGTH}` }];
  }

  static styles = css`
    :host {
      display: inline-block;
      width: 18px;
      height: 18px;
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
    "kraftvakt-countdown-bar": KraftvaktCountdownBar;
    "kraftvakt-countdown-ring": KraftvaktCountdownRing;
  }
}
