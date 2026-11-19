import { html, type PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";

import { measurePowerSensorInterval, type KraftvaktConfig } from "../api";
import { ownEntities } from "../entities";
import { closestWindowUpdates, regulationWindowOptions, windowSeconds } from "../regulation-window";
import { SettingsFormPage, type FormField, type GeneralField } from "./settings-form-page";

/**
 * The power sensor has no default, the power limit is the tariff step the user has chosen,
 * and the regulation window depends on the power sensor.
 */
const RESTORED_FIELDS: readonly GeneralField[] = ["turn_on_margin_w", "regulation_interval", "wait_at_limit_s", "penalty_threshold_w"];

type CardTitle = "general.measurement" | "general.regulation" | "general.penalty";

/** The power sensor and the settings of the regulation and the penalty. */
@customElement("kraftvakt-general-page")
export class KraftvaktGeneralPage extends SettingsFormPage {
  /** The power sensor whose interval is being measured. */
  @state() private measuring?: string;

  /** The power sensor whose interval could not be found, so it is not measured again until it is chosen again. */
  @state() private notMeasured?: string;

  /** The length of the regulation window before another power sensor was chosen, kept as near as its updates allow. */
  private secondsBeforeNewSensor?: number;

  protected render() {
    return html`
      ${this.renderSettingsCard("general.measurement", [this.entityField("power_sensor"), this.windowField()])}
      ${this.renderSettingsCard("general.regulation", [
        this.numberField("power_limit_w"),
        this.numberField("turn_on_margin_w"),
        this.intervalField(),
        this.numberField("wait_at_limit_s"),
      ])}
      ${this.renderSettingsCard("general.penalty", [this.numberField("penalty_threshold_w")], "general.penalty_info")} ${this.renderRestoreDefaults(RESTORED_FIELDS)}
    `;
  }

  /** Measure the interval of a power sensor that has none, such as one just chosen. */
  protected willUpdate(changed: PropertyValues<this>): void {
    super.willUpdate(changed);
    const { power_sensor: sensor, power_sensor_interval_s: interval } = this.config.general;
    if (sensor && interval === null && !this.locked && this.measuring !== sensor && this.notMeasured !== sensor) {
      void this.measureInterval(sensor);
    }
  }

  /** Another power sensor reports at its own interval, which is measured again. */
  protected changeConfig(config: KraftvaktConfig): void {
    const general = config.general;
    if (general.power_sensor !== this.config.general.power_sensor) {
      this.secondsBeforeNewSensor = windowSeconds(this.config.general) ?? this.secondsBeforeNewSensor;
      this.notMeasured = undefined;
      config = { ...config, general: { ...general, power_sensor_interval_s: null, regulation_window_updates: null } };
    }
    super.changeConfig(config);
  }

  private async measureInterval(sensor: string): Promise<void> {
    this.measuring = sensor;
    let interval: number | null = null;
    try {
      interval = (await measurePowerSensorInterval(this.hass, sensor)).interval_s;
    } catch {
      interval = null;
    }
    this.measuring = undefined;
    const general = this.config.general;
    if (general.power_sensor !== sensor || this.locked) {
      return;
    }
    if (interval === null) {
      this.notMeasured = sensor;
      return;
    }
    const limits = this.capabilities.regulation_window;
    const updates = closestWindowUpdates(this.secondsBeforeNewSensor ?? limits.seconds.min ?? 0, interval, limits);
    super.changeConfig({ ...this.config, general: { ...general, power_sensor_interval_s: interval, regulation_window_updates: updates } });
  }

  private renderSettingsCard(title: CardTitle, schema: FormField[], description?: "general.penalty_info") {
    return this.renderCard({
      title: this.localize(title),
      description: description && this.localize(description),
      content: this.renderForm(schema),
    });
  }

  /** Kraftvakt's own averages are left out of the power sensors to choose from. */
  private entityField(name: GeneralField): FormField {
    return {
      name,
      required: true,
      selector: {
        entity: { filter: { domain: "sensor", device_class: "power" }, exclude_entities: ownEntities(this.hass) },
      },
    };
  }

  /** A number of updates of the power sensor, each shown with how long the window lasts at its interval. */
  private windowField(): FormField {
    const interval = this.config.general.power_sensor_interval_s;
    const options =
      interval === null
        ? []
        : regulationWindowOptions(interval, this.capabilities.regulation_window).map((count) => ({
            value: String(count),
            label: this.localize(count === 1 ? "general.window_option_one" : "general.window_option", { count, seconds: this.formatNumber(count * interval) }),
          }));
    return { name: "regulation_window_updates", required: true, disabled: options.length === 0, selector: { select: { mode: "dropdown", options } } };
  }

  /** The interval is a whole number of regulation windows. */
  private intervalField(): FormField {
    return this.selectField("regulation_interval", (count) => this.localize("general.interval_option", { count }));
  }

  /** The regulation window tells how often the power sensor reports, or why it cannot be chosen yet. */
  protected helperText(field: FormField): string {
    if (field.name !== "regulation_window_updates") {
      return super.helperText(field);
    }
    const { power_sensor: sensor, power_sensor_interval_s: interval } = this.config.general;
    const seconds = this.capabilities.regulation_window.seconds;
    const params = { interval: this.formatNumber(interval), min: this.formatNumber(seconds.min), max: this.formatNumber(seconds.max) };
    if (!sensor) {
      return this.localize("general.window_no_power_sensor");
    }
    if (this.measuring === sensor) {
      return this.localize("general.window_measuring");
    }
    if (interval === null) {
      return this.localize("general.window_not_measured");
    }
    if (regulationWindowOptions(interval, this.capabilities.regulation_window).length === 0) {
      return this.localize("general.window_too_seldom", params);
    }
    return this.localize("general.fields.regulation_window_updates.helper", params);
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-general-page": KraftvaktGeneralPage;
  }
}
