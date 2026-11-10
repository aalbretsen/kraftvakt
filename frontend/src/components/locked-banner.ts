import { mdiLock, mdiStop } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { isCommandError, setRunning } from "../api";
import type { Localize } from "../localize";
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

  @state() private stopping = false;

  @state() private error?: string;

  protected render() {
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("locked.title")} .narrow=${this.narrow}>
        <ha-svg-icon slot="icon" .path=${mdiLock}></ha-svg-icon>
        ${this.localize("locked.text")}
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
        <ha-button slot="action" appearance="outlined" variant="danger" .disabled=${this.stopping} @click=${this.stop}>
          <ha-svg-icon slot="start" .path=${mdiStop}></ha-svg-icon>
          ${this.localize("locked.stop")}
        </ha-button>
      </ha-alert>
    `;
  }

  /** The status subscription unlocks the pages. */
  private async stop(): Promise<void> {
    this.stopping = true;
    this.error = undefined;
    try {
      await setRunning(this.hass, false);
    } catch (error) {
      this.error = this.localize("panel.error", { message: isCommandError(error) ? error.message : String(error) });
    } finally {
      this.stopping = false;
    }
  }

  static styles = css`
    :host {
      display: block;
      margin-bottom: 16px;
    }
    ha-button::part(base) {
      white-space: nowrap;
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
