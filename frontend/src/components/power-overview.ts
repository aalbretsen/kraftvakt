import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { StatusSnapshot } from "../api";
import { formatNumber, formatPower } from "../format";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/** The kW steps the meter's scale may use. */
const TICK_STEPS = [1, 2, 5, 10, 20, 50];

/** Return the step between at most 15 ticks and the end of a scale that reaches at least `reach` kW. */
function meterScale(reach: number): { step: number; end: number } {
  const step = TICK_STEPS.find((candidate) => reach / candidate <= 15) ?? TICK_STEPS[TICK_STEPS.length - 1];
  return { step, end: Math.ceil(reach / step) * step };
}

/** The tiles for the consumption now, the averages and the power limit, and the meter that shows them together. */
@customElement("kraftvakt-power-overview")
export class KraftvaktPowerOverview extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status!: StatusSnapshot;

  /** The power sensor's state now, read in the panel so it updates live. */
  @property({ attribute: false }) powerNowW: number | null = null;

  protected render() {
    const status = this.status;
    const language = this.hass.language;
    const overLimit = (value: number | null) => value !== null && value > status.power_limit_w;
    return html`
      <div class="stats">
        ${this.renderStat("power-now", "status.power_now", formatPower(language, this.powerNowW), this.localize("status.momentary"))}
        ${this.renderStat(
          "regulation-average",
          "status.regulation_average",
          formatPower(language, status.regulation_average_w),
          this.localize("status.average_over_seconds", { seconds: status.regulation_window_s }),
        )}
        ${this.renderStat(
          "tariff-average",
          "status.tariff_average",
          formatPower(language, status.tariff_average_w),
          this.localize("status.average_over_hour"),
          overLimit(status.tariff_average_w),
        )}
        ${this.renderStat("power-limit", "status.power_limit", formatPower(language, status.power_limit_w))}
      </div>
      ${this.renderMeter()}
    `;
  }

  private renderStat(swatch: string, label: Parameters<Localize>[0], value: string, period?: string, alarm = false) {
    return html`
      <div class="stat">
        <div class="stat-label"><span class="swatch ${swatch}"></span>${this.localize(label)}</div>
        <div class="stat-value ${alarm ? "alarm" : ""}">${value} <small>kW</small></div>
        ${period ? html`<div class="stat-period">${period}</div>` : nothing}
      </div>
    `;
  }

  /**
   * The consumption now as a bar, with a triangle for each average and the
   * power limit, and a scale in whole kW with a value at every second tick
   * (every third on a narrow screen).
   */
  private renderMeter() {
    const status = this.status;
    const kilowatt = (watt: number | null) => (watt === null ? null : watt / 1000);
    const limit = status.power_limit_w / 1000;
    const powerNow = kilowatt(this.powerNowW);
    const tariffAverage = kilowatt(status.tariff_average_w);
    const regulationAverage = kilowatt(status.regulation_average_w);
    const values = [powerNow, tariffAverage, regulationAverage];
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
            title="${this.localize(label)} ${formatNumber(language, value, 2)} kW"
          ></span>`;
    return html`
      <div class="meter">
        <div class="markers">
          ${marker("power-limit", "status.power_limit", limit)}
          ${marker("tariff-average", "status.tariff_average", tariffAverage)}
          ${marker("regulation-average", "status.regulation_average", regulationAverage)}
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

  static styles = css`
    :host {
      display: grid;
      gap: 16px;
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
    .tariff-average {
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
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-power-overview": KraftvaktPowerOverview;
  }
}
