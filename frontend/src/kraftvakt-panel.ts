import { LitElement, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { HomeAssistant, Route } from "./types";

/**
 * The Kraftvakt panel in the Home Assistant sidebar (GUI-001).
 *
 * Home Assistant sets `hass`, `narrow`, `route` and `panel` on the element.
 */
@customElement("kraftvakt-panel")
export class KraftvaktPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @property({ type: Boolean }) narrow = false;

  @property({ attribute: false }) route?: Route;

  protected render() {
    return html`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <span>Kraftvakt</span>
      </div>
    `;
  }

  static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: var(--header-height, 56px);
      padding: 0 16px;
      background: var(--app-header-background-color, var(--primary-color));
      color: var(--app-header-text-color, var(--text-primary-color));
      font-size: 20px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-panel": KraftvaktPanel;
  }
}
