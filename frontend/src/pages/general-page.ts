import { css, html } from "lit";
import { customElement } from "lit/decorators.js";

import type { GeneralConfig, Range } from "../api";
import { ownEntities } from "../entities";
import { ConfigPage } from "./config-page";

type GeneralField = keyof GeneralConfig;

type CardTitle = "general.measurement" | "general.regulation" | "general.penalty";

interface FormField {
  name: GeneralField;
  required?: boolean;
  selector: Record<string, unknown>;
}

const UNITS: Partial<Record<GeneralField, string>> = {
  power_limit_kw: "kW",
  regulation_window_s: "s",
  wait_at_limit_min: "min",
  penalty_threshold_kw: "kW",
};

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
        this.numberField("power_limit_kw"),
        this.intervalField(),
        this.numberField("wait_at_limit_min"),
      ])}
      ${this.renderCard(
        "general.penalty",
        [this.numberField("penalty_threshold_kw")],
        html`<ha-alert alert-type="info">${this.localize("general.capacity_window_info")}</ha-alert>`,
      )}
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
    return this.localize(`general.fields.${field.name}.helper`, {
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
    .card-content {
      display: grid;
      gap: 16px;
      padding: 0 16px 16px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-general-page": KraftvaktGeneralPage;
  }
}
