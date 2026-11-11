import { mdiLock } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { Localize } from "../localize";
import "./running-button";
import type { HomeAssistant } from "../types";

/**
 * Tells that the configuration is locked while the regulation runs, with a
 * shortcut to stop the regulation.
 */
@customElement("kraftvakt-locked-banner")
export class KraftvaktLockedBanner extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean }) narrow = false;

  @state() private error?: string;

  protected render() {
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("locked.title")} .narrow=${this.narrow}>
        <ha-svg-icon slot="icon" .path=${mdiLock}></ha-svg-icon>
        ${this.localize("locked.text")}
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
        <kraftvakt-running-button
          slot="action"
          .hass=${this.hass}
          .localize=${this.localize}
          running
          appearance="outlined"
          @running-error=${(event: CustomEvent<string | undefined>) => (this.error = event.detail)}
        ></kraftvakt-running-button>
      </ha-alert>
    `;
  }

  static styles = css`
    :host {
      display: block;
      margin-bottom: 16px;
    }
    .error {
      margin-top: 8px;
      color: var(--error-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-locked-banner": KraftvaktLockedBanner;
  }
}
