import { css, html, type CSSResultGroup } from "lit";

import type { GeneralConfig, Range } from "../api";
import type { TranslationKey } from "../localize";
import { ConfigPage } from "./config-page";

export type GeneralField = keyof GeneralConfig;

export interface FormField {
  name: GeneralField;
  required?: boolean;
  selector: Record<string, unknown>;
}

const UNITS: Partial<Record<GeneralField, string>> = {
  power_limit_w: "W",
  turn_on_margin_w: "W",
  regulation_window_s: "s",
  wait_at_limit_s: "s",
  appliance_cycling_step_s: "s",
  appliance_cycling_cap_s: "s",
  charger_cycling_step_s: "s",
  charger_cycling_cap_s: "s",
  penalty_threshold_w: "W",
};

/**
 * A configuration page with fields from the general settings. The settings
 * are spread over «General» and «Advanced», and their texts are in
 * `general.fields`.
 */
export class GeneralSettingsPage extends ConfigPage {
  protected renderForm(schema: FormField[]) {
    return html`
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
    `;
  }

  protected numberField(name: GeneralField): FormField {
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

  protected range(name: GeneralField): Range {
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

  static styles: CSSResultGroup = css`
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
  `;
}
