import { css, html, nothing, svg } from "lit";
import { customElement } from "lit/decorators.js";

import { formatNumber, formatPower } from "../format";
import { waitingCurve } from "../wait-curve";
import { GeneralSettingsPage } from "./general-settings-page";

type CurveField = "wait_curve_steepness" | "wait_curve_pivot";
type TableRow =
  | "advanced.free_power_percent"
  | "advanced.free_power_kw"
  | "advanced.waiting_percent"
  | "advanced.waiting_seconds";

const CURVE_FIELDS: CurveField[] = ["wait_curve_steepness", "wait_curve_pivot"];
const TABLE_FREE_PERCENTS = [50, 40, 30, 25, 20, 15, 10, 7, 4, 1];

/**
 * The regulation works with utilization of the power limit, but the page shows
 * free power, the power limit minus the regulation average, as a share of the
 * limit. The pivot point slider moves over the stored utilization, so free
 * power goes down to the right like on the graph, and shows 100 minus it.
 */
const SHOWN_AS_FREE_POWER: Record<CurveField, boolean> = {
  wait_curve_steepness: false,
  wait_curve_pivot: true,
};

/** The waiting time curve and the waiting time when the same slot is turned on again and again. */
@customElement("kraftvakt-advanced-page")
export class KraftvaktAdvancedPage extends GeneralSettingsPage {
  protected render() {
    return html`${this.renderWaitCurveCard()} ${this.renderCyclingCard()}`;
  }

  /** Sliders for the waiting time curve, and the curve as a table and a graph that follow them. */
  private renderWaitCurveCard() {
    return html`
      <ha-card .header=${this.localize("advanced.wait_curve")}>
        <div class="card-content">
          <p class="description">${this.localize("advanced.wait_curve_info")}</p>
          <div class="sliders">${CURVE_FIELDS.map((name) => this.renderSlider(name))}</div>
          ${this.renderWaitCurve()}
        </div>
      </ha-card>
    `;
  }

  private renderCyclingCard() {
    return html`
      <ha-card .header=${this.localize("advanced.cycling")}>
        <div class="card-content">
          <p class="description">${this.localize("advanced.cycling_info")}</p>
          <h3>${this.localize("advanced.appliances")}</h3>
          ${this.renderForm([this.numberField("appliance_cycling_step_s"), this.numberField("appliance_cycling_cap_s")])}
          <h3>${this.localize("advanced.chargers")}</h3>
          ${this.renderForm([this.numberField("charger_cycling_step_s"), this.numberField("charger_cycling_cap_s")])}
        </div>
      </ha-card>
    `;
  }

  private renderSlider(name: CurveField) {
    const range = this.range(name);
    const value = this.config.general[name];
    const shownValue = SHOWN_AS_FREE_POWER[name] ? 100 - value : value;
    const label = this.localize(`general.fields.${name}.label`);
    const unit = SHOWN_AS_FREE_POWER[name] ? " %" : "";
    return html`
      <span class="slider-label">${label}</span>
      <ha-slider
        aria-label=${label}
        .min=${range.min}
        .max=${range.max}
        .step=${range.step}
        .value=${value}
        .withTooltip=${false}
        ?disabled=${this.locked}
        @input=${(event: Event) => this.changeCurve(name, Number((event.target as HTMLInputElement).value))}
      ></ha-slider>
      <span class="slider-value">${new Intl.NumberFormat(this.hass.language).format(shownValue)}${unit}</span>
    `;
  }

  private changeCurve(name: CurveField, value: number): void {
    if (value !== this.config.general[name]) {
      this.changeConfig({ ...this.config, general: { ...this.config.general, [name]: value } });
    }
  }

  /**
   * The waiting time curve as a table and a graph, as the sliders are moved.
   * The table also gives the free power in kW and the waiting time in seconds
   * with the power limit and the waiting time at the limit in the draft.
   */
  private renderWaitCurve() {
    const general = this.config.general;
    const curve = waitingCurve(general.wait_curve_steepness, general.wait_curve_pivot);
    const share = (freePercent: number) => curve(1 - freePercent / 100);
    const language = this.hass.language;
    const limit = general.power_limit_w as number | null;
    const waitAtLimit = general.wait_at_limit_s as number | null;
    const waitingPercent = (free: number) => {
      const value = 100 * share(free);
      return value === 0 ? "0" : formatNumber(language, value, 1);
    };
    const freeKw = (free: number) => formatPower(language, limit === null ? null : (limit * free) / 100);
    const waitingSeconds = (free: number) =>
      waitAtLimit === null ? "–" : formatNumber(language, Math.round(waitAtLimit * share(free)), 0);
    const row = (title: TableRow, cell: (free: number) => unknown) => html`
      <tr>
        <th>${this.localize(title)}</th>
        ${TABLE_FREE_PERCENTS.map((free) => html`<td>${cell(free)}</td>`)}
      </tr>
    `;
    return html`
      ${this.narrow
        ? nothing
        : html`<table class="curve-table">
            ${row("advanced.free_power_percent", (free) => free)} ${row("advanced.free_power_kw", freeKw)}
            ${row("advanced.waiting_percent", waitingPercent)}
            ${row("advanced.waiting_seconds", waitingSeconds)}
          </table>`}
      ${this.renderCurveGraph(share)}
    `;
  }

  /** The graph has less free power to the right, so the waiting time grows to the right. */
  private renderCurveGraph(share: (freePercent: number) => number) {
    const [width, height] = this.narrow ? [320, 200] : [900, 260];
    const [left, right, top, bottom] = [44, 24, 8, 38];
    const x = (freePercent: number) => left + ((width - left - right) * (100 - freePercent)) / 100;
    const y = (percent: number) => top + ((height - top - bottom) * (100 - percent)) / 100;
    const label = (value: number) => `${formatNumber(this.hass.language, value, 0)} %`;
    const points = Array.from({ length: 201 }, (_, index) => {
      const free = 100 - index / 2;
      return `${x(free)},${y(100 * share(free))}`;
    });
    const line = `M${points.join("L")}`;
    const yTicks = [0, 20, 40, 60, 80, 100];
    const xTicks = Array.from({ length: this.narrow ? 5 : 11 }, (_, index) => 100 - index * (this.narrow ? 25 : 10));
    return html`
      <svg class="curve" viewBox="0 0 ${width} ${height}" role="img" aria-label=${this.localize("advanced.wait_curve")}>
        ${yTicks.map(
          (tick) => svg`
            <line class="grid" x1=${left} x2=${width - right} y1=${y(tick)} y2=${y(tick)}></line>
            <text x=${left - 6} y=${y(tick) + 4} text-anchor="end">${label(tick)}</text>
          `,
        )}
        ${xTicks.map((tick) => svg`<text x=${x(tick)} y=${height - bottom + 18} text-anchor="middle">${label(tick)}</text>`)}
        <text x=${x(50)} y=${height - 4} text-anchor="middle">${this.localize("advanced.free_power")}</text>
        <path class="area" d="${line}L${x(0)},${y(0)}L${x(100)},${y(0)}Z"></path>
        <path class="line" d=${line}></path>
      </svg>
    `;
  }

  static styles = [
    GeneralSettingsPage.styles,
    css`
      h3 {
        margin: 0 0 -8px;
        font-size: var(--ha-font-size-m, 14px);
        font-weight: 500;
      }
      .sliders {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) 3em;
        align-items: center;
        gap: 8px 16px;
      }
      .sliders ha-slider {
        width: 100%;
      }
      :host([locked]) .sliders {
        opacity: 0.6;
      }
      .slider-value {
        text-align: end;
        font-variant-numeric: tabular-nums;
      }
      .curve-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }
      .curve-table th {
        width: 120px;
        text-align: start;
        font-weight: normal;
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .curve-table th,
      .curve-table td {
        padding: 6px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .curve-table td {
        text-align: center;
        font-variant-numeric: tabular-nums;
      }
      .curve {
        display: block;
        width: 100%;
        height: auto;
      }
      .curve .grid {
        stroke: var(--divider-color);
      }
      .curve text {
        fill: var(--secondary-text-color);
        font-size: 12px;
      }
      .curve .line {
        fill: none;
        stroke: var(--primary-color);
        stroke-width: 2;
      }
      .curve .area {
        fill: var(--primary-color);
        opacity: 0.12;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-advanced-page": KraftvaktAdvancedPage;
  }
}
