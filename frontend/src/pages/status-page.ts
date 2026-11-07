import { mdiPlay, mdiStop } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { ERROR_CONFIG_INCOMPLETE, isCommandError, setRunning, type ConfigResponse, type StatusSnapshot } from "../api";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import type { HomeAssistant } from "../types";

/** Shows how the regulation stands now, and starts and stops it (GUI-005 to GUI-007). */
@customElement("kraftvakt-status-page")
export class KraftvaktStatusPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status?: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  @state() private changingRunning = false;

  @state() private runningError?: string;

  protected render() {
    if (!this.status) {
      return nothing;
    }
    return html`<div class="cards">${this.renderRegulationCard(this.status)}</div>`;
  }

  private renderRegulationCard(status: StatusSnapshot) {
    return html`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${status.running ? "running" : "off"}">
            <span class="dot"></span>
            ${this.localize(status.running ? "status.running" : "status.stopped")}
          </span>
          <span class="spacer"></span>
          ${this.narrow ? nothing : this.renderStartStop(status)}
        </div>
        <div class="card-content">
          ${this.runningError ? html`<ha-alert alert-type="error">${this.runningError}</ha-alert>` : nothing}
          ${status.running ? nothing : this.renderStopped(status)}
        </div>
        ${this.narrow ? html`<div class="card-actions">${this.renderStartStop(status)}</div>` : nothing}
      </ha-card>
    `;
  }

  private renderStartStop(status: StatusSnapshot) {
    if (status.running) {
      return html`
        <ha-button
          variant="danger"
          appearance="outlined"
          .disabled=${this.changingRunning}
          @click=${() => this.changeRunning(false)}
        >
          <ha-svg-icon slot="start" .path=${mdiStop}></ha-svg-icon>
          ${this.localize("status.stop")}
        </ha-button>
      `;
    }
    return html`
      <ha-button
        .disabled=${this.changingRunning || status.missing.length > 0}
        @click=${() => this.changeRunning(true)}
      >
        <ha-svg-icon slot="start" .path=${mdiPlay}></ha-svg-icon>
        ${this.localize("status.start")}
      </ha-button>
    `;
  }

  private renderStopped(status: StatusSnapshot) {
    if (status.missing.length === 0) {
      return html`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`;
    }
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${status.missing.map((issue) => {
            const page = pageForIssue(issue);
            return html`
              <li>
                ${describeIssue(issue, this.config, this.localize)}
                <a href="${PANEL_PATH}/${page}" @click=${(event: Event) => this.openPage(event, page)}>
                  ${this.localize(`tabs.${page}`)}
                </a>
              </li>
            `;
          })}
        </ul>
      </ha-alert>
    `;
  }

  /** Start or stop the regulation. The new status comes with the status subscription (GUI-007). */
  private async changeRunning(running: boolean): Promise<void> {
    this.changingRunning = true;
    this.runningError = undefined;
    try {
      await setRunning(this.hass, running);
    } catch (error) {
      this.runningError =
        isCommandError(error) && error.code === ERROR_CONFIG_INCOMPLETE
          ? this.localize("status.start_refused")
          : this.localize("panel.error", { message: isCommandError(error) ? error.message : String(error) });
    } finally {
      this.changingRunning = false;
    }
  }

  private openPage(event: Event, page: Parameters<typeof navigateToPage>[0]): void {
    event.preventDefault();
    navigateToPage(page);
  }

  static styles = css`
    :host {
      display: block;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      align-items: start;
    }
    :host([narrow]) .cards {
      grid-template-columns: minmax(0, 1fr);
      gap: 8px;
    }
    .regulation {
      grid-column: 1 / -1;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .spacer {
      flex: 1;
    }
    .card-content {
      display: grid;
      gap: 12px;
      padding: 0 16px 16px;
    }
    .card-content:empty {
      display: none;
    }
    .card-actions {
      display: flex;
      justify-content: flex-end;
      padding: 8px 16px;
      border-top: 1px solid var(--divider-color);
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      font-weight: 500;
      line-height: 20px;
      white-space: nowrap;
      background: var(--kraftvakt-chip-off-background, rgba(127, 127, 127, 0.16));
      color: var(--secondary-text-color);
    }
    .chip .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .chip.running,
    .chip.on {
      background: rgba(var(--rgb-success-color, 67, 160, 71), 0.16);
      color: var(--success-color, #43a047);
    }
    ul.missing {
      margin: 6px 0 0;
      padding-inline-start: 18px;
    }
    ul.missing a {
      color: var(--primary-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-status-page": KraftvaktStatusPage;
  }
}
