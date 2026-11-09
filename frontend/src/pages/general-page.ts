import { css, html, nothing, svg } from "lit";
import { customElement } from "lit/decorators.js";

import type { GeneralConfig, Range } from "../api";
import { ownEntities } from "../entities";
import { formatNumber } from "../format";
import type { TranslationKey } from "../localize";
import { waitingCurve } from "../wait-curve";
import { ConfigPage } from "./config-page";

type GeneralField = keyof GeneralConfig;

type CardTitle = "general.measurement" | "general.regulation" | "general.penalty";

interface FormField {
  name: GeneralField;
  required?: boolean;
  selector: Record<string, unknown>;
}

const UNITS: Partial<Record<GeneralField, string>> = {
  power_limit_w: "W",
  turn_on_margin_w: "W",
  regulation_window_s: "s",
  wait_at_limit_s: "s",
  penalty_threshold_w: "W",
};

type CurveField = "wait_curve_steepness" | "wait_curve_pivot";

const CURVE_FIELDS: CurveField[] = ["wait_curve_steepness", "wait_curve_pivot"];
const TABLE_UTILIZATIONS = [50, 60, 70, 75, 80, 85, 90, 93, 96, 99];

/** The power sensor and the settings of the regulation and the penalty. */
@customElement("kraftvakt-general-page")
export class KraftvaktGeneralPage extends ConfigPage {
  protected render() {
    return html`
      ${this.renderCard("general.measurement", [
        this.entityField("power_sensor"),
        this.numberField("regulation_window_s"),
      ])}
      ${this.renderCard("general.regulation", [
        this.numberField("power_limit_w"),
        this.numberField("turn_on_margin_w"),
        this.intervalField(),
        this.numberField("wait_at_limit_s"),
      ])}
      ${this.renderCard(
        "general.penalty",
        [this.numberField("penalty_threshold_w")],
        html`<ha-alert alert-type="info">${this.localize("general.capacity_window_info")}</ha-alert>`,
      )}
      ${this.renderWaitCurveCard()}
    `;
  }

  private renderCard(title: CardTitle, schema: FormField[], extra?: unknown) {
    return html`
      <ha-card .header=${this.localize(title)}>
        <div class="card-content">
          <ha-form
            .hass=${this.hass}
            .data=${this.formData}
            .schema=${schema}
            .error=${this.formErrors("general")}
            .disabled=${this.locked}
            .computeLabel=${this.computeLabel}
            .computeHelper=${this.computeHelper}
            .computeError=${(error: string) => error}
            @value-changed=${this.valueChanged}
          ></ha-form>
          ${extra ?? ""}
        </div>
      </ha-card>
    `;
  }

  /**
   * The power sensor is a sensor from another integration that measures power,
   * in W or kW, so Kraftvakt's own averages are left out.
   */
  private entityField(name: GeneralField): FormField {
    return {
      name,
      required: true,
      selector: {
        entity: { filter: { domain: "sensor", device_class: "power" }, exclude_entities: ownEntities(this.hass) },
      },
    };
  }

  private numberField(name: GeneralField): FormField {
    const range = this.range(name);
    return {
      name,
      required: true,
      selector: {
        number: {
          min: range.min ?? undefined,
          max: range.max ?? undefined,
          step: range.step,
          mode: "box",
          unit_of_measurement: UNITS[name],
        },
      },
    };
  }

  /** Sliders for the waiting time curve, and the curve as a table and a graph that follow them. */
  private renderWaitCurveCard() {
    return html`
      <ha-card .header=${this.localize("general.wait_curve")}>
        <div class="card-content">
          <p class="description">${this.localize("general.wait_curve_info")}</p>
          <div class="sliders">${CURVE_FIELDS.map((name) => this.renderSlider(name))}</div>
          ${this.renderWaitCurve()}
        </div>
      </ha-card>
    `;
  }

  private renderSlider(name: CurveField) {
    const range = this.range(name);
    const value = this.config.general[name];
    const label = this.localize(`general.fields.${name}.label`);
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
      <span class="slider-value">${new Intl.NumberFormat(this.hass.language).format(value)}</span>
    `;
  }

  private changeCurve(name: CurveField, value: number): void {
    if (value !== this.config.general[name]) {
      this.changeConfig({ ...this.config, general: { ...this.config.general, [name]: value } });
    }
  }

  /** The waiting time curve as a table of shares and a graph, as the sliders are moved. */
  private renderWaitCurve() {
    const general = this.config.general;
    const share = waitingCurve(general.wait_curve_steepness, general.wait_curve_pivot);
    const percent = (utilization: number) => {
      const value = 100 * share(utilization / 100);
      return value === 0 ? "0" : formatNumber(this.hass.language, value, 1);
    };
    return html`
      ${this.narrow
        ? nothing
        : html`<table class="curve-table">
            <tr>
              <th>${this.localize("general.utilization_percent")}</th>
              ${TABLE_UTILIZATIONS.map((utilization) => html`<td>${utilization}</td>`)}
            </tr>
            <tr>
              <th>${this.localize("general.waiting_percent")}</th>
              ${TABLE_UTILIZATIONS.map((utilization) => html`<td class="value">${percent(utilization)}</td>`)}
            </tr>
          </table>`}
      ${this.renderCurveGraph(share)}
    `;
  }

  private renderCurveGraph(share: (utilization: number) => number) {
    const [width, height] = this.narrow ? [320, 200] : [900, 260];
    const [left, right, top, bottom] = [44, 24, 8, 38];
    const x = (utilization: number) => left + ((width - left - right) * utilization) / 100;
    const y = (percent: number) => top + ((height - top - bottom) * (100 - percent)) / 100;
    const label = (value: number) => `${formatNumber(this.hass.language, value, 0)} %`;
    const points = Array.from({ length: 201 }, (_, index) => `${x(index / 2)},${y(100 * share(index / 200))}`);
    const line = `M${points.join("L")}`;
    const yTicks = [0, 20, 40, 60, 80, 100];
    const xTicks = Array.from({ length: this.narrow ? 5 : 11 }, (_, index) => index * (this.narrow ? 25 : 10));
    return html`
      <svg class="curve" viewBox="0 0 ${width} ${height}" role="img" aria-label=${this.localize("general.wait_curve")}>
        ${yTicks.map(
          (tick) => svg`
            <line class="grid" x1=${left} x2=${width - right} y1=${y(tick)} y2=${y(tick)}></line>
            <text x=${left - 6} y=${y(tick) + 4} text-anchor="end">${label(tick)}</text>
          `,
        )}
        ${xTicks.map((tick) => svg`<text x=${x(tick)} y=${height - bottom + 18} text-anchor="middle">${label(tick)}</text>`)}
        <text x=${x(50)} y=${height - 4} text-anchor="middle">${this.localize("general.utilization")}</text>
        <path class="area" d="${line}L${x(100)},${y(0)}L${x(0)},${y(0)}Z"></path>
        <path class="line" d=${line}></path>
      </svg>
    `;
  }

  /** The interval is a whole number of regulation windows. */
  private intervalField(): FormField {
    const range = this.range("regulation_interval");
    const options = [];
    for (let count = range.min ?? 1; count <= (range.max ?? count); count += range.step) {
      options.push({ value: String(count), label: this.localize("general.interval_option", { count }) });
    }
    return { name: "regulation_interval", required: true, selector: { select: { mode: "dropdown", options } } };
  }

  private range(name: GeneralField): Range {
    return this.capabilities.limits.general[name];
  }

  /** The select field for the interval works with text values. */
  private get formData(): Record<string, unknown> {
    const general = this.config.general;
    return { ...general, regulation_interval: String(general.regulation_interval) };
  }

  private valueChanged(event: CustomEvent<{ value: Record<string, unknown> }>): void {
    const value = event.detail.value;
    const general = { ...this.config.general };
    for (const name of Object.keys(general) as GeneralField[]) {
      const changed = value[name];
      (general as Record<string, unknown>)[name] =
        name === "regulation_interval" && changed !== undefined ? Number(changed) : (changed ?? null);
    }
    this.changeConfig({ ...this.config, general });
  }

  private computeLabel = (field: FormField): string => this.localize(`general.fields.${field.name}.label`);

  private computeHelper = (field: FormField): string => {
    const range = this.range(field.name) as Range | undefined;
    const defaults = this.capabilities.defaults.general;
    const number = (value: number | null | undefined) =>
      value === null || value === undefined ? "" : new Intl.NumberFormat(this.hass.language).format(value);
    const window = this.config.general.regulation_window_s;
    return this.localize(`general.fields.${field.name}.helper` as TranslationKey, {
      min: number(range?.min),
      max: number(range?.max),
      default: number(defaults[field.name] as number | null),
      seconds: number(window * this.config.general.regulation_interval),
    });
  };

  static styles = css`
    :host {
      display: grid;
      gap: 16px;
    }
    :host([narrow]) {
      gap: 8px;
    }
    /* HA's number field keeps its full text colour when disabled. */
    :host([locked]) ha-form {
      opacity: 0.6;
    }
    .card-content {
      display: grid;
      gap: 16px;
      padding: 0 16px 16px;
    }
    .description {
      margin: 0;
      color: var(--secondary-text-color);
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
      color: var(--secondary-text-color);
    }
    .curve-table .value {
      color: var(--primary-text-color);
      font-weight: 500;
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
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-general-page": KraftvaktGeneralPage;
  }
}
