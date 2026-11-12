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
  penalty_threshold_w: "W",
  command_repeat_interval_min: "min",
};

/** Fields chosen from a list, which works with text values. */
const SELECT_FIELDS: ReadonlySet<GeneralField> = new Set([
  "regulation_interval",
  "appliance_cycling_step_factor",
  "appliance_cycling_steps",
  "charger_cycling_step_factor",
  "charger_cycling_steps",
]);

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

  /** A list of the values in the field's range, each shown with `label`. */
  protected selectField(name: GeneralField, label: (value: number) => string): FormField {
    const range = this.range(name);
    const options = [];
    for (let value = range.min ?? range.step; value <= (range.max ?? value); value += range.step) {
      options.push({ value: String(value), label: label(value) });
    }
    return { name, required: true, selector: { select: { mode: "dropdown", options } } };
  }

  protected range(name: GeneralField): Range {
    return this.capabilities.limits.general[name];
  }

  private get formData(): Record<string, unknown> {
    const general = this.config.general as unknown as Record<GeneralField, unknown>;
    return Object.fromEntries(
      Object.entries(general).map(([name, value]) => [
        name,
        SELECT_FIELDS.has(name as GeneralField) && value !== null ? String(value) : value,
      ]),
    );
  }

  private valueChanged(event: CustomEvent<{ value: Record<string, unknown> }>): void {
    const value = event.detail.value;
    const general = { ...this.config.general };
    for (const name of Object.keys(general) as GeneralField[]) {
      const changed = value[name];
      (general as Record<string, unknown>)[name] =
        SELECT_FIELDS.has(name) && changed !== undefined ? Number(changed) : (changed ?? null);
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

  static styles: CSSResultGroup = [
    ConfigPage.styles,
    css`
      .card-content {
        display: grid;
        gap: 16px;
      }
      .description {
        margin: 0;
        color: var(--secondary-text-color);
      }
    `,
  ];
}
