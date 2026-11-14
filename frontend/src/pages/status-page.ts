import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { type ConfigResponse, type StatusSnapshot } from "../api";
import "../components/countdown";
import "../components/power-overview";
import "../components/priority-list";
import "../components/running-button";
import { measuredPowerW } from "../entities";
import { formatClockTime, formatEnergy } from "../format";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import { cardHeaderStyles, chipStyles } from "../status-styles";
import type { HomeAssistant } from "../types";

/** Shows how the regulation stands now, and starts and stops it. */
@customElement("kraftvakt-status-page")
export class KraftvaktStatusPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status?: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  @state() private runningError?: string;

  protected render() {
    if (!this.status) {
      return nothing;
    }
    const status = this.status;
    return html`
      <div class="cards">
        ${this.renderRegulationCard(status)}
        ${status.running
          ? html`<kraftvakt-priority-list
              .hass=${this.hass}
              .localize=${this.localize}
              .narrow=${this.narrow}
              .status=${status}
              .config=${this.config}
            ></kraftvakt-priority-list>`
          : nothing}
      </div>
    `;
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
          ${status.running && status.safe_state
            ? html`<span class="chip alarm">${this.localize("status.safe_state_chip")}</span>`
            : nothing}
          ${status.running && status.penalty.active
            ? html`<span class="chip alarm">${this.localize("status.penalty_chip")}</span>`
            : nothing}
          <span class="spacer"></span>
          ${status.running && status.next_decision_at ? this.renderNextDecision(status, status.next_decision_at) : nothing}
        </div>
        <div class="card-content">
          ${this.runningError ? html`<ha-alert alert-type="error">${this.runningError}</ha-alert>` : nothing}
          ${status.running ? this.renderRunning(status) : this.renderStopped(status)}
        </div>
        <div class="card-actions">${this.renderStartStop(status)}</div>
      </ha-card>
    `;
  }

  private renderStartStop(status: StatusSnapshot) {
    return html`
      <kraftvakt-running-button
        .hass=${this.hass}
        .localize=${this.localize}
        .running=${status.running}
        .disabled=${!status.running && status.missing.length > 0}
        @running-error=${(event: CustomEvent<string | undefined>) => (this.runningError = event.detail)}
      ></kraftvakt-running-button>
    `;
  }

  private renderRunning(status: StatusSnapshot) {
    const powerNow = measuredPowerW(this.hass, this.config?.config.general.power_sensor ?? "");
    return html`
      ${status.safe_state ? this.renderSafeState(powerNow !== null) : nothing} ${status.penalty.active ? this.renderPenalty(status) : nothing}
      <kraftvakt-power-overview
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .status=${status}
        .powerNowW=${powerNow}
      ></kraftvakt-power-overview>
    `;
  }

  private renderNextDecision(status: StatusSnapshot, nextDecisionAt: string) {
    const end = Date.parse(nextDecisionAt);
    const interval = status.regulation_window_s * status.regulation_interval * 1000;
    const time = formatClockTime(this.hass.language, nextDecisionAt);
    return html`
      <span class="next-decision" title=${this.localize("status.next_decision_at", { time })}>
        ${this.narrow ? nothing : this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${end - interval} .end=${end}></kraftvakt-countdown-ring>
      </span>
    `;
  }

  /**
   * The safe state lasts until the next decision, also after the sensor gives
   * a valid value again.
   */
  private renderSafeState(sensorBack: boolean) {
    const sensor = this.config?.config.general.power_sensor ?? "";
    const name = this.hass.states[sensor]?.attributes.friendly_name ?? sensor;
    return html`
      <ha-alert alert-type=${sensorBack ? "info" : "error"} .title=${this.localize("status.safe_state_title")}>
        ${this.localize(sensorBack ? "status.safe_state_back_text" : "status.safe_state_text", { sensor: name })}
      </ha-alert>
    `;
  }

  private renderPenalty(status: StatusSnapshot) {
    const energy = formatEnergy(this.hass.language, Math.max(0, status.penalty.overconsumption_wh));
    const recovery = status.penalty.recovery_started ? "status.recovery_started" : "status.recovery_not_started";
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left", { energy })} · ${this.localize(recovery)}</div>
      </ha-alert>
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

  private openPage(event: Event, page: Parameters<typeof navigateToPage>[0]): void {
    event.preventDefault();
    navigateToPage(page);
  }

  static styles = [
    cardHeaderStyles,
    chipStyles,
    css`
      :host {
        display: block;
        --kraftvakt-grid-color: var(--energy-grid-consumption-color, #488fc2);
        --kraftvakt-now-color: var(--secondary-text-color);
        --kraftvakt-ev-color: var(--teal-color, #009688);
        --kraftvakt-on-color: var(--state-active-color, var(--amber-color, #ffc107));
      }
      .cards {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 16px;
      }
      :host([narrow]) .cards {
        gap: 8px;
      }
      .spacer {
        flex: 1;
      }
      .card-content {
        display: grid;
        gap: 16px;
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
      .next-decision {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: var(--ha-font-size-m, 14px);
        color: var(--secondary-text-color);
      }
      .penalty-details {
        margin-top: 8px;
      }
      ul.missing {
        margin: 6px 0 0;
        padding-inline-start: 18px;
      }
      ul.missing a {
        color: var(--primary-color);
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-status-page": KraftvaktStatusPage;
  }
}
