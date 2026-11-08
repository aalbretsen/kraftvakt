import { mdiEvStation, mdiPlay, mdiStop } from "@mdi/js";
import { LitElement, css, html, nothing, unsafeCSS } from "lit";
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
import "../components/countdown-ring";
import { measuredPowerKw } from "../entities";
import { formatClockTime, formatNumber, formatPower } from "../format";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import type { HomeAssistant } from "../types";

/** The width of the waiting column, and the blocks in it, in pixels. */
const WAITING_WIDTH = 88;
const WAITING_WIDTH_NARROW = 48;
const BLOCK_GAP = 2;
const SQUARE_SIZE = 8;
const BAR_WIDTH = 3;
const BAR_HEIGHT = 12;

/**
 * Return the size of `count` equal blocks that fill at most `available` pixels:
 * squares when they fit, otherwise thinner and taller, down to ampere-like bars.
 */
function blockSize(count: number, available: number): { width: number; height: number } {
  const room = Math.floor((available - (count - 1) * BLOCK_GAP) / count);
  const width = Math.max(BAR_WIDTH, Math.min(SQUARE_SIZE, room));
  const thinning = (SQUARE_SIZE - width) / (SQUARE_SIZE - BAR_WIDTH);
  return { width, height: Math.round(SQUARE_SIZE + thinning * (BAR_HEIGHT - SQUARE_SIZE)) };
}

/** Return how many blocks fit at their thinnest in `available` pixels. */
function maxBlocks(available: number): number {
  return Math.floor((available + BLOCK_GAP) / (BAR_WIDTH + BLOCK_GAP));
}

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

  protected render() {
    if (!this.status) {
      return nothing;
    }
    const status = this.status;
    return html`
      <div class="cards">
        ${this.renderRegulationCard(status)} ${status.running ? this.renderPriorityCard(status) : nothing}
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
        ${this.renderStat(
          "",
          "status.power_now",
          formatPower(language, measuredPowerKw(this.hass, this.config?.config.general.power_sensor ?? "")),
          this.localize("status.momentary"),
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
        <span class="spacer"></span>
        ${status.next_decision_at ? this.renderNextDecision(status, status.next_decision_at) : nothing}
      </div>
    `;
  }

  /** «Next decision» and a ring that empties until it, with the time as a tooltip. */
  private renderNextDecision(status: StatusSnapshot, nextDecisionAt: string) {
    const end = Date.parse(nextDecisionAt);
    const interval = status.regulation_window_s * status.regulation_interval * 1000;
    const time = formatClockTime(this.hass.language, nextDecisionAt);
    return html`
      <span class="next-decision" title=${this.localize("status.next_decision_at", { time })}>
        ${this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${end - interval} .end=${end}></kraftvakt-countdown-ring>
      </span>
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

  /** The appliances in order of priority, with the EV chargers grouped at the place of «EV charging». */
  private renderPriorityCard(status: StatusSnapshot) {
    const position = status.ev_charging_position;
    const appliances = status.appliances;
    const before = position === null ? appliances : appliances.slice(0, position);
    const after = position === null ? [] : appliances.slice(position);
    const empty = appliances.length === 0 && position === null;
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.priority_list")}</span>
        </div>
        ${empty
          ? html`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`
          : html`<div class="list">
              ${before.map((appliance, index) => this.renderApplianceRow(appliance, index + 1))}
              ${position === null ? nothing : this.renderEvCharging(status.chargers, position + 1)}
              ${after.map((appliance, index) => this.renderApplianceRow(appliance, before.length + index + 2))}
            </div>`}
      </ha-card>
    `;
  }

  private renderApplianceRow(appliance: ApplianceStatus, rank: number) {
    const variant = appliance.variant ? html`<span class="variant">${appliance.variant}</span>` : nothing;
    return html`
      <div class="row">
        <span class="rank">${rank}</span>
        <div class="row-main">
          <div class="row-title">${appliance.name} ${this.narrow ? variant : nothing}</div>
        </div>
        ${this.narrow ? nothing : html`<span>${variant}</span><span></span>`} ${this.renderWaiting(appliance)}
        ${this.renderOnOff(appliance.on, "status.on", "status.off")}
      </div>
    `;
  }

  /** The «EV charging» entry, with each EV charger in the current charging priority under it. */
  private renderEvCharging(chargers: ChargerStatus[], rank: number) {
    return html`
      <div class="row group">
        <span class="rank">${rank}</span>
        <div class="row-main">
          <div class="row-title">${this.localize("status.ev_charging")}</div>
          ${chargers.length === 0 ? html`<div class="row-sub">${this.localize("status.no_chargers")}</div>` : nothing}
        </div>
      </div>
      ${chargers.map((charger) => {
        const details = this.chargerDetails(charger);
        const amperes = this.renderAmperes(charger);
        return html`
          <div class="row charger">
            <span class="rank"></span>
            <div class="row-main">
              <div class="row-title">
                <ha-svg-icon .path=${mdiEvStation}></ha-svg-icon><span class="charger-name">${charger.name}</span>
              </div>
              ${this.narrow ? html`<div class="row-sub">${amperes}</div>` : nothing}
              ${details.length > 0 ? html`<div class="row-sub">${details.join(" · ")}</div>` : nothing}
            </div>
            ${this.narrow ? nothing : html`<span></span>${amperes}`} ${this.renderWaiting(charger)}
            ${this.renderOnOff(charger.activated, "status.activated", "status.deactivated")}
          </div>
        `;
      })}
    `;
  }

  /**
   * One block per regulation window left until the decision that ends the
   * waiting. The status comes at every window, so one block goes each time.
   * When more windows are left than blocks fit, each block stands for several.
   */
  private renderWaiting(item: ApplianceStatus | ChargerStatus) {
    if (!item.waiting_ends_at || !this.status) {
      return html`<span></span>`;
    }
    const left = Date.parse(item.waiting_ends_at) - Date.now();
    const windows = Math.max(1, Math.ceil(left / (this.status.regulation_window_s * 1000)));
    const available = this.narrow ? WAITING_WIDTH_NARROW : WAITING_WIDTH;
    const windowsPerBlock = Math.ceil(windows / maxBlocks(available));
    const blocks = Math.ceil(windows / windowsPerBlock);
    const size = blockSize(blocks, available);
    const time = formatClockTime(this.hass.language, item.waiting_ends_at);
    return html`
      <span class="waiting" title=${this.localize("status.waiting_ends_at", { time })}>
        <span class="indicator-label">${this.localize("status.turning_on_in")}</span>
        <span class="windows-left" style="--block-width: ${size.width}px; --block-height: ${size.height}px">
          ${Array.from({ length: blocks }, () => html`<span class="window-left"></span>`)}
        </span>
      </span>
    `;
  }

  /**
   * The charging level, and one bar per ampere from the minimum to the
   * maximum, filled up to the current.
   */
  private renderAmperes(charger: ChargerStatus) {
    const config = this.config?.config.charging.chargers.find((item) => item.id === charger.id);
    if (!config) {
      return html`<span></span>`;
    }
    const steps = config.max_current_a - config.min_current_a + 1;
    const on = charger.current_a === null ? 0 : charger.current_a - config.min_current_a + 1;
    return html`
      <span class="amperes">
        <span class="indicator-label">
          ${charger.current_a === null
            ? this.localize("status.charging_level_off")
            : this.localize("status.charging_level", { current: charger.current_a })}
        </span>
        <span class="ampere-steps ${steps > 16 ? "small" : ""}">
          ${Array.from({ length: steps }, (_, index) => html`<span class="ampere ${index < on ? "on" : ""}"></span>`)}
        </span>
      </span>
    `;
  }

  private chargerDetails(charger: ChargerStatus): string[] {
    const config = this.config?.config.charging.chargers.find((item) => item.id === charger.id);
    const details: string[] = [];
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
    return details;
  }

  private renderOnOff(on: boolean, onText: Parameters<Localize>[0], offText: Parameters<Localize>[0]) {
    return html`<span class="state chip ${on ? "on" : "off"}"><span class="dot"></span>${this.localize(on ? onText : offText)}</span>`;
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
      grid-template-columns: minmax(0, 1fr);
      gap: 16px;
    }
    :host([narrow]) .cards {
      gap: 8px;
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
      grid-template-columns: repeat(2, minmax(0, 1fr));
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
    .empty {
      color: var(--secondary-text-color);
    }
    .row {
      display: grid;
      grid-template-columns: 24px minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1.6fr) ${unsafeCSS(WAITING_WIDTH)}px 112px;
      align-items: center;
      gap: 12px;
      min-height: 56px;
      padding: 6px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
    }
    .row.group {
      min-height: 40px;
    }
    .row.charger {
      border-top-style: dashed;
    }
    .row.charger .row-main {
      padding-inline-start: 16px;
    }
    .rank {
      text-align: center;
      color: var(--secondary-text-color);
    }
    .row > .chip {
      justify-self: start;
    }
    .next-decision {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .waiting {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
    }
    .windows-left {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: ${unsafeCSS(BLOCK_GAP)}px;
    }
    .window-left {
      flex: none;
      width: var(--block-width);
      height: var(--block-height);
      border-radius: 1px;
      background: var(--primary-text-color);
    }
    .amperes {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
    .ampere-steps {
      display: inline-flex;
      gap: 2px;
    }
    .ampere {
      width: 3px;
      height: 12px;
      border-radius: 1px;
      background: rgba(127, 127, 127, 0.32);
    }
    .ampere-steps.small {
      gap: 1px;
    }
    .ampere-steps.small .ampere {
      width: 2px;
    }
    .ampere.on {
      background: var(--primary-color);
    }
    .indicator-label {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
      white-space: nowrap;
    }
    :host([narrow]) .amperes {
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: 4px 6px;
    }
    :host([narrow]) .ampere-steps {
      gap: 1px;
    }
    :host([narrow]) .ampere {
      width: 2px;
    }
    :host([narrow]) .waiting .indicator-label {
      white-space: normal;
      text-align: end;
    }
    :host([narrow]) .row {
      grid-template-columns: 20px minmax(0, 1fr) ${unsafeCSS(WAITING_WIDTH_NARROW)}px auto;
      gap: 8px;
      padding: 6px 12px;
    }
    .row-title {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      overflow-wrap: anywhere;
    }
    .charger-name {
      flex: 1;
      min-width: 0;
    }
    .row-title ha-svg-icon {
      flex: none;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
    }
    .row-sub {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .variant {
      display: inline-block;
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
