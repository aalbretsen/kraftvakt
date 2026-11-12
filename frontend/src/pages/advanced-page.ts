import { css, html, nothing, svg } from "lit";
import { customElement } from "lit/decorators.js";

import { formatMinutes, formatNumber, formatPower } from "../format";
import { waitingCurve } from "../wait-curve";
import { GeneralSettingsPage } from "./general-settings-page";

type CurveField = "wait_curve_steepness" | "wait_curve_pivot";
type CyclingTitle = "advanced.appliances" | "advanced.chargers";
type CyclingFactorField = "appliance_cycling_step_factor" | "charger_cycling_step_factor";
type CyclingStepsField = "appliance_cycling_steps" | "charger_cycling_steps";
type TableRow = "advanced.free_power_kw" | "advanced.waiting_minutes" | "advanced.actual_waiting_minutes";

const CURVE_FIELDS: CurveField[] = ["wait_curve_steepness", "wait_curve_pivot"];
/** The first time a slot is turned on, and the first time again, follow the curve. */
const CURVE_TURN_ONS = 2;
const TABLE_FREE_PERCENTS = [50, 40, 30, 25, 20, 15, 10, 7, 4, 1];
/** The waiting time is 0 above 50 % free power, so the graph starts a bit above it. */
const GRAPH_FREE_PERCENT = 60;
const KW_TICK_STEPS = [0.1, 0.2, 0.5, 1, 2, 5, 10];
const MAX_KW_TICKS = 10;
const MAX_KW_TICKS_NARROW = 4;

/** Return the smallest kW step that gives at most `maxTicks` steps up to `reach` kW. */
function kwTickStep(reach: number, maxTicks: number): number {
  return KW_TICK_STEPS.find((step) => reach / step <= maxTicks) ?? KW_TICK_STEPS[KW_TICK_STEPS.length - 1];
}

/**
 * Return how long an appliance actually waits: it is turned on at the first
 * decision after the waiting time has passed, and decisions come every
 * `decisionInterval` seconds.
 */
function untilDecision(waiting: number, decisionInterval: number): number {
  return Math.max(0, Math.ceil(waiting / decisionInterval - 1e-9)) * decisionInterval;
}

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

/**
 * The waiting time curve, the waiting time when the same slot is turned on
 * again and again, and how often commands are repeated.
 */
@customElement("kraftvakt-advanced-page")
export class KraftvaktAdvancedPage extends GeneralSettingsPage {
  protected render() {
    return html`${this.renderWaitCurveCard()} ${this.renderCyclingCard()} ${this.renderCommandRepeatCard()}`;
  }

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
          ${this.renderCyclingSection("advanced.appliances", "appliance_cycling_step_factor", "appliance_cycling_steps")}
          ${this.renderCyclingSection("advanced.chargers", "charger_cycling_step_factor", "charger_cycling_steps")}
        </div>
      </ha-card>
    `;
  }

  private renderCommandRepeatCard() {
    return html`
      <ha-card .header=${this.localize("advanced.command_repeat")}>
        <div class="card-content">
          <p class="description">${this.localize("advanced.command_repeat_info")}</p>
          ${this.renderForm([this.numberField("command_repeat_interval_min")])}
        </div>
      </ha-card>
    `;
  }

  private renderCyclingSection(title: CyclingTitle, factorField: CyclingFactorField, stepsField: CyclingStepsField) {
    const language = this.hass.language;
    return html`
      <h3>${this.localize(title)}</h3>
      ${this.renderForm([
        this.selectField(factorField, (factor) => `× ${new Intl.NumberFormat(language).format(factor)}`),
        this.selectField(stepsField, (steps) => String(steps)),
      ])}
      ${this.narrow ? nothing : this.renderCyclingTable(this.config.general[factorField], this.config.general[stepsField])}
    `;
  }

  /**
   * The waiting time each time the same slot is turned on in a row. The first
   * two follow the curve and are shown at the pivot point; from the third it
   * is the waiting time at the limit, one step longer each time, until the
   * last column, which holds for every time after it as well.
   */
  private renderCyclingTable(factor: number, steps: number) {
    const general = this.config.general;
    const waitAtLimit = general.wait_at_limit_s as number | null;
    const decisionInterval = this.decisionInterval;
    const shareAtPivot = waitingCurve(general.wait_curve_steepness, general.wait_curve_pivot)(general.wait_curve_pivot / 100);
    const turnOns = Array.from({ length: steps + CURVE_TURN_ONS + 1 }, (_, index) => index + 1);
    const waiting = (turnOn: number, actual: boolean) => {
      if (waitAtLimit === null || (actual && decisionInterval === null)) {
        return "–";
      }
      const value =
        turnOn <= CURVE_TURN_ONS
          ? waitAtLimit * shareAtPivot
          : waitAtLimit * (1 + factor * (turnOn - CURVE_TURN_ONS - 1));
      return formatMinutes(actual ? untilDecision(value, decisionInterval as number) : value);
    };
    return html`
      <table class="curve-table">
        <tr>
          <th>${this.localize("advanced.turn_on_in_a_row")}</th>
          ${turnOns.map((turnOn) => html`<td>${turnOn}${turnOn === turnOns.length ? "+" : ""}</td>`)}
        </tr>
        <tr>
          <th>${this.localize("advanced.waiting_minutes")}</th>
          ${turnOns.map((turnOn) => html`<td>${waiting(turnOn, false)}</td>`)}
        </tr>
        <tr>
          <th>${this.localize("advanced.actual_waiting_minutes")}</th>
          ${turnOns.map((turnOn) => html`<td>${waiting(turnOn, true)}</td>`)}
        </tr>
      </table>
    `;
  }

  /** Seconds between decisions, or null while the regulation window is not set. */
  private get decisionInterval(): number | null {
    const window = this.config.general.regulation_window_s as number | null;
    return window === null ? null : window * this.config.general.regulation_interval;
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

  private renderWaitCurve() {
    const general = this.config.general;
    const curve = waitingCurve(general.wait_curve_steepness, general.wait_curve_pivot);
    const share = (freePercent: number) => curve(1 - freePercent / 100);
    const language = this.hass.language;
    const limit = general.power_limit_w as number | null;
    const waitAtLimit = general.wait_at_limit_s as number | null;
    const decisionInterval = this.decisionInterval;
    const waiting = (free: number) => (waitAtLimit === null ? null : waitAtLimit * share(free));
    const actualWaiting = (free: number) => {
      const value = waiting(free);
      return value === null || decisionInterval === null ? null : untilDecision(value, decisionInterval);
    };
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
            ${row("advanced.free_power_kw", (free) => formatPower(language, limit === null ? null : (limit * free) / 100))}
            ${row("advanced.waiting_minutes", (free) => formatMinutes(waiting(free)))}
            ${row("advanced.actual_waiting_minutes", (free) => formatMinutes(actualWaiting(free)))}
          </table>`}
      ${this.renderCurveGraph(share, limit)}
    `;
  }

  /**
   * The graph has the free power in kW, from 60 % of the power limit to the
   * left down to 0 to the right, so the waiting time grows to the right.
   */
  private renderCurveGraph(share: (freePercent: number) => number, limitW: number | null) {
    const language = this.hass.language;
    const [width, height] = this.narrow ? [320, 200] : [900, 260];
    const [left, right, top, bottom] = [44, 24, 8, 38];
    const x = (freePercent: number) =>
      left + ((width - left - right) * (GRAPH_FREE_PERCENT - freePercent)) / GRAPH_FREE_PERCENT;
    const y = (percent: number) => top + ((height - top - bottom) * (100 - percent)) / 100;
    const points = Array.from({ length: 201 }, (_, index) => {
      const free = GRAPH_FREE_PERCENT - (index * GRAPH_FREE_PERCENT) / 200;
      return `${x(free)},${y(100 * share(free))}`;
    });
    const line = `M${points.join("L")}`;
    const yTicks = [0, 20, 40, 60, 80, 100];
    const limitKw = limitW === null ? 0 : limitW / 1000;
    const reachKw = (limitKw * GRAPH_FREE_PERCENT) / 100;
    const step = kwTickStep(reachKw, this.narrow ? MAX_KW_TICKS_NARROW : MAX_KW_TICKS);
    const kwTicks = reachKw > 0 ? Array.from({ length: Math.floor(reachKw / step + 1e-9) + 1 }, (_, i) => i * step) : [];
    const decimals = step < 1 ? 1 : 0;
    return html`
      <svg class="curve" viewBox="0 0 ${width} ${height}" role="img" aria-label=${this.localize("advanced.wait_curve")}>
        ${yTicks.map(
          (tick) => svg`
            <line class="grid" x1=${left} x2=${width - right} y1=${y(tick)} y2=${y(tick)}></line>
            <text x=${left - 6} y=${y(tick) + 4} text-anchor="end">${formatNumber(language, tick, 0)} %</text>
          `,
        )}
        ${kwTicks.map(
          (kw) =>
            svg`<text x=${x((100 * kw) / limitKw)} y=${height - bottom + 18} text-anchor="middle">${formatNumber(language, kw, decimals)}</text>`,
        )}
        <text x=${x(GRAPH_FREE_PERCENT / 2)} y=${height - 4} text-anchor="middle">${this.localize("advanced.free_power_kw")}</text>
        <path class="area" d="${line}L${x(0)},${y(0)}L${x(GRAPH_FREE_PERCENT)},${y(0)}Z"></path>
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
        width: 180px;
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
