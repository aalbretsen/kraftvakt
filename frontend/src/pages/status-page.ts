import { mdiCarElectric, mdiEvStation, mdiFlash, mdiPlay, mdiStop } from "@mdi/js";
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
import "../components/countdown";
import { measuredPowerKw } from "../entities";
import { formatClockTime, formatNumber, formatPower } from "../format";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import type { HomeAssistant } from "../types";

/** The width of the waiting column in pixels. */
const WAITING_WIDTH = 88;
const WAITING_WIDTH_NARROW = 48;

/** The kW steps the meter's scale may use, and how many ticks it may have at most. */
const TICK_STEPS = [1, 2, 5, 10, 20, 50];
const MAX_TICKS = 15;

/** Return the step between ticks and the end of a scale that reaches at least `reach` kW. */
function meterScale(reach: number): { step: number; end: number } {
  const step = TICK_STEPS.find((candidate) => reach / candidate <= MAX_TICKS) ?? TICK_STEPS[TICK_STEPS.length - 1];
  return { step, end: Math.ceil(reach / step) * step };
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
    const powerNow = measuredPowerKw(this.hass, this.config?.config.general.power_sensor ?? "");
    return html`
      ${status.safe_state ? this.renderSafeState(powerNow !== null) : nothing} ${status.penalty.active ? this.renderPenalty(status) : nothing}
      <div class="stats">
        ${this.renderStat("power-now", "status.power_now", formatPower(language, powerNow), this.localize("status.momentary"))}
        ${this.renderStat(
          "regulation-average",
          "status.regulation_average",
          formatPower(language, status.regulation_average_kw),
          this.localize("status.average_over_seconds", { seconds: status.regulation_window_s }),
        )}
        ${this.renderStat(
          "capacity-average",
          "status.capacity_average",
          formatPower(language, status.capacity_average_kw),
          this.localize("status.average_over_hour"),
          overLimit(status.capacity_average_kw),
        )}
        ${this.renderStat("power-limit", "status.power_limit", formatPower(language, status.power_limit_kw))}
      </div>
      ${this.renderMeter(status, powerNow)}
      <div class="facts">
        ${status.safe_state ? html`<span class="chip alarm">${this.localize("status.safe_state_chip")}</span>` : nothing}
        ${status.penalty.active ? html`<span class="chip alarm">${this.localize("status.penalty_chip")}</span>` : nothing}
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
  /**
   * The consumption now as a bar, with a triangle for each average and the
   * power limit, and a scale in whole kW with a value at every second tick
   * (every third on a narrow screen).
   */
  private renderMeter(status: StatusSnapshot, powerNow: number | null) {
    const limit = status.power_limit_kw;
    const values = [powerNow, status.capacity_average_kw, status.regulation_average_kw];
    const { step, end } = meterScale(Math.max(limit * 1.2, ...values.map((value) => value ?? 0)));
    const percent = (value: number) => `${(100 * Math.min(value, end)) / end}%`;
    const language = this.hass.language;
    const ticks = Array.from({ length: end / step + 1 }, (_, index) => index * step);
    const labelEvery = this.narrow ? 3 : 2;
    const labelled = ticks.filter((_, index) => index % labelEvery === 0);
    const marker = (kind: string, label: Parameters<Localize>[0], value: number | null) =>
      value === null
        ? nothing
        : html`<span
            class="marker ${kind}"
            style="left: ${percent(value)}"
            title="${this.localize(label)} ${formatPower(language, value)} kW"
          ></span>`;
    return html`
      <div class="meter">
        <div class="markers">
          ${marker("power-limit", "status.power_limit", limit)}
          ${marker("capacity-average", "status.capacity_average", status.capacity_average_kw)}
          ${marker("regulation-average", "status.regulation_average", status.regulation_average_kw)}
        </div>
        <div class="bar">
          ${powerNow === null ? nothing : html`<div class="fill power-now" style="width: ${percent(powerNow)}"></div>`}
        </div>
        <div class="ticks">${ticks.map((tick) => html`<span style="left: ${percent(tick)}"></span>`)}</div>
        <div class="scale">
          ${labelled.map(
            (tick, index) =>
              html`<span class=${tick === 0 ? "start" : tick === end ? "end" : ""} style="left: ${percent(tick)}"
                >${formatNumber(language, tick, 0)}${index === labelled.length - 1 ? " kW" : ""}</span
              >`,
          )}
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
      <div class="row ${appliance.on ? "" : "off"}">
        <span class="rank">${rank}</span>
        <div class="row-main">
          <div class="row-title">
            ${this.renderApplianceIcon(appliance)}<span class="name">${appliance.name}</span>
            ${this.narrow ? variant : nothing}
          </div>
        </div>
        ${this.narrow ? nothing : html`<span>${variant}</span><span></span>`} ${this.renderWaiting(appliance)}
        ${this.renderOnOff(appliance.on, "status.on", "status.off")}
      </div>
    `;
  }

  /** The icon of the appliance's entity, coloured like Home Assistant colours a switch that is on. */
  private renderApplianceIcon(appliance: ApplianceStatus) {
    const entityId = this.config?.config.appliances.find((item) => item.id === appliance.id)?.entity_id;
    const stateObj = entityId ? this.hass.states[entityId] : undefined;
    const on = appliance.on ? "on" : "";
    return stateObj
      ? html`<ha-state-icon class="device-icon ${on}" .hass=${this.hass} .stateObj=${stateObj}></ha-state-icon>`
      : html`<ha-svg-icon class="device-icon ${on}" .path=${mdiFlash}></ha-svg-icon>`;
  }

  /** The «EV charging» entry, with each EV charger in the current charging priority under it. */
  private renderEvCharging(chargers: ChargerStatus[], rank: number) {
    return html`
      <div class="row group">
        <span class="rank">${rank}</span>
        <div class="row-main">
          <div class="row-title">
            <ha-svg-icon class="ev-icon" .path=${mdiCarElectric}></ha-svg-icon>
            <span class="name">${this.localize("status.ev_charging")}</span>
          </div>
          ${chargers.length === 0 ? html`<div class="row-sub">${this.localize("status.no_chargers")}</div>` : nothing}
        </div>
      </div>
      ${chargers.map((charger) => {
        const details = this.chargerDetails(charger);
        const amperes = this.renderAmperes(charger);
        return html`
          <div class="row charger ${charger.activated ? "" : "off"}">
            <span class="rank"></span>
            <div class="row-main">
              <div class="row-title">
                <ha-svg-icon class="device-icon ev ${charger.activated ? "on" : ""}" .path=${mdiEvStation}></ha-svg-icon>
                <span class="name charger-name">${charger.name}</span>
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

  /** A bar that empties from when the waiting started until the decision that ends it. */
  private renderWaiting(item: ApplianceStatus | ChargerStatus) {
    if (!item.waiting_since || !item.waiting_ends_at) {
      return html`<span></span>`;
    }
    const time = formatClockTime(this.hass.language, item.waiting_ends_at);
    return html`
      <span class="waiting" title=${this.localize("status.waiting_ends_at", { time })}>
        <span class="indicator-label">${this.localize("status.delayed_turn_on")}</span>
        <kraftvakt-countdown-bar
          .start=${Date.parse(item.waiting_since)}
          .end=${Date.parse(item.waiting_ends_at)}
        ></kraftvakt-countdown-bar>
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
            ? this.localize("status.not_charging")
            : this.localize("status.charging_at", { current: charger.current_a })}
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
    if (charger.excluded === null) {
      return [this.localize("status.first_decision")];
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
    return details;
  }

  private renderOnOff(on: boolean, onText: Parameters<Localize>[0], offText: Parameters<Localize>[0]) {
    return html`<span class="state chip ${on ? "on" : "off"}"><span class="dot"></span>${this.localize(on ? onText : offText)}</span>`;
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
      flex: none;
    }
    .swatch.power-now {
      width: 12px;
      height: 8px;
      border-radius: 4px;
      background: var(--kraftvakt-now-color);
    }
    .swatch:not(.power-now),
    .meter .marker {
      width: 0;
      height: 0;
      border-inline: 5px solid transparent;
      border-top: 7px solid var(--marker-color);
    }
    .capacity-average {
      --marker-color: var(--kraftvakt-grid-color);
    }
    .regulation-average {
      --marker-color: var(--primary-text-color);
    }
    .power-limit {
      --marker-color: var(--error-color);
    }
    .meter .markers {
      position: relative;
      height: 9px;
    }
    .meter .marker {
      position: absolute;
      top: 0;
      transform: translateX(-50%);
      transition: left 0.6s ease;
    }
    .meter .bar {
      position: relative;
      height: 12px;
      overflow: hidden;
      border-radius: 6px;
      background: var(--secondary-background-color);
    }
    .meter .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 6px;
      background: var(--kraftvakt-now-color);
      transition: width 0.6s ease;
    }
    .meter .ticks {
      position: relative;
      height: 5px;
      margin-top: 2px;
    }
    .meter .ticks span {
      position: absolute;
      top: 0;
      width: 1px;
      height: 100%;
      margin-left: -0.5px;
      background: var(--secondary-text-color);
      opacity: 0.6;
    }
    .meter .scale {
      position: relative;
      height: 18px;
      margin-top: 2px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .scale span {
      position: absolute;
      transform: translateX(-50%);
      white-space: nowrap;
    }
    .meter .scale .start {
      transform: none;
    }
    .meter .scale .end {
      transform: translateX(-100%);
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
    .row.group,
    .row.charger {
      background: color-mix(in srgb, var(--kraftvakt-ev-color) 7%, transparent);
    }
    .row.charger {
      border-top-style: dashed;
    }
    .row.off .name {
      color: var(--secondary-text-color);
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
      gap: 4px;
      text-align: end;
    }
    .waiting .indicator-label {
      white-space: normal;
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
      background: var(--kraftvakt-ev-color);
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
    .row-title ha-svg-icon,
    .row-title ha-state-icon {
      flex: none;
      --mdc-icon-size: 20px;
      color: var(--state-inactive-color, var(--secondary-text-color));
    }
    .row-title .device-icon.on {
      color: var(--kraftvakt-on-color);
    }
    .row-title .device-icon.ev.on,
    .row-title .ev-icon {
      color: var(--kraftvakt-ev-color);
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
