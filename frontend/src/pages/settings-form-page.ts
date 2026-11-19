import { mdiRestore } from "@mdi/js";
import { html, type CSSResultGroup } from "lit";

import type { GeneralConfig, Range } from "../api";
import type { TranslationKey } from "../localize";
import { ConfigPage } from "./config-page";

export type GeneralField = keyof GeneralConfig;

export interface FormField {
  name: GeneralField;
  required?: boolean;
  disabled?: boolean;
  selector: Record<string, unknown>;
}

const UNITS: Partial<Record<GeneralField, string>> = {
  power_limit_w: "W",
  turn_on_margin_w: "W",
  wait_at_limit_s: "s",
  penalty_threshold_w: "W",
  command_repeat_interval_min: "min",
  action_timeout_s: "s",
  power_sensor_timeout_s: "s",
};

/** Fields chosen from a list, which works with text values. */
const SELECT_FIELDS: ReadonlySet<GeneralField> = new Set(["regulation_window_updates", "appliance_repeat_increment_factor", "appliance_repeat_increments"]);

/**
 * A configuration page with fields from the general settings. The settings
 * are spread over «General» and «Advanced», and their texts are in
 * `general.fields`.
 */
export class SettingsFormPage extends ConfigPage {
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

  /** It only changes the draft, so it needs no confirmation: Discard brings the saved values back. */
  protected renderRestoreDefaults(fields: readonly GeneralField[]) {
    const general = this.config.general;
    const defaults = this.capabilities.defaults.general;
    const atDefaults = fields.every((name) => general[name] === defaults[name]);
    const restore = () => {
      const restored = Object.fromEntries(fields.map((name) => [name, defaults[name]]));
      this.changeConfig({ ...this.config, general: { ...general, ...restored } });
    };
    return this.renderPageFooter(
      "",
      html`
        <ha-button appearance="plain" .disabled=${this.locked || atDefaults} @click=${restore}>
          <ha-svg-icon slot="start" .path=${mdiRestore}></ha-svg-icon>
          ${this.localize("config.restore_defaults")}
        </ha-button>
      `,
    );
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
          step: range.resolution,
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
    for (let value = range.min ?? range.resolution; value <= (range.max ?? value); value += range.resolution) {
      options.push({ value: String(value), label: label(value) });
    }
    return { name, required: true, selector: { select: { mode: "dropdown", options } } };
  }

  protected range(name: GeneralField): Range {
    return this.capabilities.limits.general[name];
  }

  private get formData(): Record<string, unknown> {
    const general = this.config.general as unknown as Record<GeneralField, unknown>;
    return Object.fromEntries(Object.entries(general).map(([name, value]) => [name, SELECT_FIELDS.has(name as GeneralField) && value !== null ? String(value) : value]));
  }

  private valueChanged(event: CustomEvent<{ value: Record<string, unknown> }>): void {
    const value = event.detail.value;
    const general = { ...this.config.general };
    for (const name of Object.keys(general) as GeneralField[]) {
      const changed = value[name];
      (general as Record<string, unknown>)[name] = SELECT_FIELDS.has(name) && changed !== undefined ? Number(changed) : (changed ?? null);
    }
    this.changeConfig({ ...this.config, general });
  }

  private computeLabel = (field: FormField): string => this.localize(`general.fields.${field.name}.label`);

  private computeHelper = (field: FormField): string => this.helperText(field);

  /** The helper text of the field, with its range and its default. */
  protected helperText(field: FormField): string {
    const range = this.range(field.name) as Range | undefined;
    const defaults = this.capabilities.defaults.general;
    return this.localize(`general.fields.${field.name}.helper` as TranslationKey, {
      min: this.formatNumber(range?.min),
      max: this.formatNumber(range?.max),
      default: this.formatNumber(defaults[field.name] as number | null),
    });
  }

  protected formatNumber(value: number | null | undefined): string {
    return value === null || value === undefined ? "" : new Intl.NumberFormat(this.hass.language).format(value);
  }

  static styles: CSSResultGroup = ConfigPage.styles;
}
