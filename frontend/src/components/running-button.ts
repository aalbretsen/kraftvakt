import { mdiPlay, mdiStop } from "@mdi/js";
import { LitElement, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { ERROR_CONFIG_INCOMPLETE, errorMessage, isCommandError, setRunning } from "../api";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/**
 * The button that starts or stops the regulation. A stop button is a danger
 * button, a start button a filled one.
 *
 * The new status comes with the status subscription. Fires `running-error`
 * with the text to show when the regulation cannot start or stop.
 */
@customElement("kraftvakt-running-button")
export class KraftvaktRunningButton extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  /** Whether the regulation runs, so the button stops it. */
  @property({ type: Boolean }) running = false;

  /** How a stop button looks, `plain` or `outlined`. */
  @property() appearance: "plain" | "outlined" = "plain";

  @property({ type: Boolean }) disabled = false;

  @state() private changing = false;

  protected render() {
    return this.running
      ? html`
          <ha-button
            variant="danger"
            appearance=${this.appearance}
            .disabled=${this.disabled || this.changing}
            @click=${this.toggle}
          >
            <ha-svg-icon slot="start" .path=${mdiStop}></ha-svg-icon>
            ${this.localize("status.stop")}
          </ha-button>
        `
      : html`
          <ha-button .disabled=${this.disabled || this.changing} @click=${this.toggle}>
            <ha-svg-icon slot="start" .path=${mdiPlay}></ha-svg-icon>
            ${this.localize("status.start")}
          </ha-button>
        `;
  }

  private async toggle(): Promise<void> {
    this.changing = true;
    this.fireError(undefined);
    try {
      await setRunning(this.hass, !this.running);
    } catch (error) {
      this.fireError(
        isCommandError(error) && error.code === ERROR_CONFIG_INCOMPLETE
          ? this.localize("status.start_refused")
          : this.localize("panel.error", { message: errorMessage(error) }),
      );
    } finally {
      this.changing = false;
    }
  }

  private fireError(message: string | undefined): void {
    this.dispatchEvent(new CustomEvent("running-error", { detail: message }));
  }

  static styles = css`
    ha-button::part(base) {
      white-space: nowrap;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-running-button": KraftvaktRunningButton;
  }
}
