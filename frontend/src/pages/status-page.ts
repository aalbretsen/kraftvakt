import { mdiEvStation, mdiPlay, mdiStop } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
  ERROR_CONFIG_INCOMPLETE,
  isCommandError,
  setRunning,
  type ApplianceStatus,
  type ChargerStatus,
  type ConfigResponse,
  type StatusSnapshot,
} from "../api";
import { ClockController } from "../clock";
import { formatNumber, formatPower, formatTimeLeft } from "../format";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import type { HomeAssistant } from "../types";

/** Shows how the regulation stands now, and starts and stops it. */
@customElement("kraftvakt-status-page")
export class KraftvaktStatusPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status?: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  @state() private changingRunning = false;

  @state() private runningError?: string;

  private clock = new ClockController(this);

  protected render() {
    if (!this.status) {
      return nothing;
    }
    const status = this.status;
    return html`
      <div class="cards">
        ${this.renderRegulationCard(status)} ${status.running ? this.renderAppliancesCard(status.appliances) : nothing}
        ${status.running && status.chargers.length > 0 ? this.renderChargersCard(status.chargers) : nothing}
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
          <span class="spacer"></span>
          ${this.narrow ? nothing : this.renderStartStop(status)}
        </div>
        <div class="card-content">
          ${this.runningError ? html`<ha-alert alert-type="error">${this.runningError}</ha-alert>` : nothing}
          ${status.running ? this.renderRunning(status) : this.renderStopped(status)}
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

  /** What the status page shows in addition while the regulation runs. */
  private renderRunning(status: StatusSnapshot) {
    const language = this.hass.language;
    const overLimit = (value: number | null) => value !== null && value > status.power_limit_kw;
    return html`
      ${status.safe_state ? this.renderSafeState() : nothing} ${status.penalty.active ? this.renderPenalty(status) : nothing}
      <div class="stats">
        ${this.renderStat(
          "capacity-average",
          "status.capacity_average",
          formatPower(language, status.capacity_average_kw),
          this.localize("status.average_over_hour"),
          overLimit(status.capacity_average_kw),
        )}
        ${this.renderStat(
          "regulation-average",
          "status.regulation_average",
          formatPower(language, status.regulation_average_kw),
          this.localize("status.average_over_seconds", { seconds: status.regulation_window_s }),
        )}
        ${this.renderStat("", "status.power_limit", formatPower(language, status.power_limit_kw))}
      </div>
      ${this.renderMeter(status)}
      <div class="facts">
        <span class="chip ${status.safe_state ? "alarm" : "off"}">
          ${this.localize("status.safe_state_chip", { value: this.yesNo(status.safe_state) })}
        </span>
        <span class="chip ${status.penalty.active ? "alarm" : "off"}">
          ${this.localize("status.penalty_chip", { value: this.yesNo(status.penalty.active) })}
        </span>
        ${status.next_decision_at
          ? html`<span>
              ${this.localize("status.next_decision", { time: formatTimeLeft(status.next_decision_at, this.clock.now) })}
            </span>`
          : nothing}
      </div>
    `;
  }

  private renderSafeState() {
    const sensor = this.config?.config.general.power_sensor ?? "";
    const name = this.hass.states[sensor]?.attributes.friendly_name ?? sensor;
    return html`
      <ha-alert alert-type="error" .title=${this.localize("status.safe_state_title")}>
        ${this.localize("status.safe_state_text", { sensor: name })}
      </ha-alert>
    `;
  }

  private renderPenalty(status: StatusSnapshot) {
    const energy = formatNumber(this.hass.language, Math.max(0, status.penalty.overconsumption_kwh), 2);
    const recovery = status.penalty.recovery_started ? "status.recovery_started" : "status.recovery_not_started";
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left", { energy })} · ${this.localize(recovery)}</div>
      </ha-alert>
    `;
  }

  private renderStat(swatch: string, label: Parameters<Localize>[0], value: string, period?: string, alarm = false) {
    return html`
      <div class="stat">
        <div class="stat-label">${swatch ? html`<span class="swatch ${swatch}"></span>` : nothing}${this.localize(label)}</div>
        <div class="stat-value ${alarm ? "alarm" : ""}">${value} <small>kW</small></div>
        ${period ? html`<div class="stat-period">${period}</div>` : nothing}
      </div>
    `;
  }

  /** The averages as bars against the power limit. */
  private renderMeter(status: StatusSnapshot) {
    const regulation = status.regulation_average_kw;
    const capacity = status.capacity_average_kw;
    if (regulation === null || capacity === null) {
      return nothing;
    }
    const scale = Math.max(status.power_limit_kw * 1.2, regulation, capacity);
    const percent = (value: number) => `${(100 * value) / scale}%`;
    const language = this.hass.language;
    return html`
      <div class="meter">
        <div class="limit-label">
          <span style="left: ${percent(status.power_limit_kw)}">
            ${this.localize("status.scale_limit", { power: formatNumber(language, status.power_limit_kw, 1) })}
          </span>
        </div>
        <div class="bar">
          <div class="fill capacity-average" style="width: ${percent(capacity)}"></div>
          <div class="fill regulation-average" style="width: ${percent(regulation)}"></div>
          <div class="limit" style="left: ${percent(status.power_limit_kw)}"></div>
        </div>
        <div class="scale">
          <span>0 kW</span>
          <span>${formatNumber(language, scale, 1)} kW</span>
        </div>
      </div>
    `;
  }

  /** Each appliance with on or off, its current variant and its waiting time. */
  private renderAppliancesCard(appliances: ApplianceStatus[]) {
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.appliances")}</span>
          <span class="sub">${this.localize("status.appliances_order")}</span>
        </div>
        ${appliances.length === 0
          ? html`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`
          : html`<div class="list">
              ${appliances.map(
                (appliance, index) => html`
                  <div class="row">
                    <span class="rank">${index + 1}</span>
                    <div class="row-main">
                      <div class="row-title">
                        ${appliance.name}
                        ${appliance.variant ? html`<span class="variant">${appliance.variant}</span>` : nothing}
                      </div>
                      ${appliance.waiting_until
                        ? html`<div class="row-sub">
                            ${this.localize("status.waiting_to_turn_on", {
                              time: formatTimeLeft(appliance.waiting_until, this.clock.now),
                            })}
                          </div>`
                        : nothing}
                    </div>
                    ${this.renderOnOff(appliance.on, "status.on", "status.off")}
                  </div>
                `,
              )}
            </div>`}
      </ha-card>
    `;
  }

  /** Each EV charger with whether it is activated, and why it charges or not. */
  private renderChargersCard(chargers: ChargerStatus[]) {
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.chargers")}</span>
          <span class="sub">${this.localize("status.chargers_order")}</span>
        </div>
        <div class="list">
          ${chargers.map((charger) => {
            const details = this.chargerDetails(charger);
            return html`
              <div class="row">
                <ha-svg-icon class="rank" .path=${mdiEvStation}></ha-svg-icon>
                <div class="row-main">
                  <div class="row-title">${charger.name}</div>
                  ${details.length > 0 ? html`<div class="row-sub">${details.join(" · ")}</div>` : nothing}
                </div>
                ${this.renderOnOff(charger.activated, "status.activated", "status.deactivated")}
              </div>
            `;
          })}
        </div>
      </ha-card>
    `;
  }

  private chargerDetails(charger: ChargerStatus): string[] {
    const config = this.config?.config.charging.chargers.find((item) => item.id === charger.id);
    const details: string[] = [];
    if (charger.current_a !== null && config) {
      details.push(
        this.localize("status.charging_current", {
          current: charger.current_a,
          min: config.min_current_a,
          max: config.max_current_a,
        }),
      );
    }
    if (charger.bypassed) {
      details.push(this.localize("status.bypassed"));
    }
    if (charger.waiting) {
      details.push(this.localize("status.waiting_charger"));
    }
    if (!charger.allowed && charger.excluded) {
      details.push(this.localize("status.excluded"));
    } else if (!charger.allowed && charger.excluded === false && config?.charging_window) {
      details.push(this.localize("status.outside_window", { ...config.charging_window }));
    }
    if (charger.waiting_until) {
      const time = formatTimeLeft(charger.waiting_until, this.clock.now);
      details.push(
        this.localize(charger.activated ? "status.waiting_to_increase" : "status.waiting_to_activate", { time }),
      );
    }
    return details;
  }

  private renderOnOff(on: boolean, onText: Parameters<Localize>[0], offText: Parameters<Localize>[0]) {
    return html`<span class="chip ${on ? "on" : "off"}"><span class="dot"></span>${this.localize(on ? onText : offText)}</span>`;
  }

  private yesNo(value: boolean): string {
    return this.localize(value ? "status.yes" : "status.no");
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

  /** Start or stop the regulation. The new status comes with the status subscription. */
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
    .chip.alarm {
      background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
      color: var(--error-color, #db4437);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }
    .stat {
      padding: 10px 12px;
      border-radius: var(--ha-border-radius-lg, 12px);
      background: var(--secondary-background-color);
    }
    .stat-label {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value {
      font-size: 26px;
    }
    .stat-period {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value small {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    :host([narrow]) .stats {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }
    :host([narrow]) .stat {
      padding: 8px;
    }
    :host([narrow]) .stat-value {
      font-size: 20px;
    }
    .stat-value.alarm {
      color: var(--error-color);
    }
    .swatch {
      display: inline-block;
      width: 12px;
      height: 8px;
      border-radius: 4px;
    }
    .capacity-average {
      background: var(--primary-color);
    }
    .regulation-average {
      background: var(--primary-text-color);
    }
    .meter .bar {
      position: relative;
      height: 12px;
      border-radius: 6px;
      background: var(--secondary-background-color);
    }
    .meter .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 6px;
    }
    .meter .fill.regulation-average {
      top: 4px;
      bottom: 4px;
    }
    .meter .limit {
      position: absolute;
      top: -4px;
      bottom: -4px;
      width: 2px;
      margin-left: -1px;
      background: var(--error-color);
    }
    .meter .scale {
      display: flex;
      justify-content: space-between;
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .limit-label {
      position: relative;
      height: 18px;
      margin-bottom: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .limit-label span {
      position: absolute;
      transform: translateX(-100%);
      padding-inline-end: 6px;
      white-space: nowrap;
    }
    .facts {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--secondary-text-color);
    }
    .penalty-details {
      margin-top: 8px;
    }
    .card-header .sub {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .empty {
      color: var(--secondary-text-color);
    }
    .row {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 56px;
      padding: 6px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
    }
    .rank {
      flex: none;
      width: 24px;
      text-align: center;
      color: var(--secondary-text-color);
    }
    .row-main {
      flex: 1;
      min-width: 0;
    }
    .row-title {
      overflow-wrap: anywhere;
    }
    .row-sub {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .variant {
      display: inline-block;
      margin-inline-start: 6px;
      padding: 0 8px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
      color: var(--primary-color);
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
