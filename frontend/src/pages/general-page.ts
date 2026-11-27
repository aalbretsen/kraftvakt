import { css, html, type PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";

import { analysePowerSensor, type KraftvaktConfig, type PowerSensorReports } from "../api";
import { ownEntities } from "../entities";
import { reportLines, reportText, windowChoices } from "../power-sensor-reports";
import { SettingsFormPage, type FormField, type GeneralField } from "./settings-form-page";

/** The power sensor has no default, the power limit is the tariff step the user has chosen, and the timeout is suggested from the power sensor. */
const RESTORED_FIELDS: readonly GeneralField[] = ["regulation_window_s", "turn_on_margin_w", "wait_at_limit_s", "penalty_threshold_w"];

type CardTitle = "general.regulation" | "general.penalty";

/** The power sensor, how it reports, and the settings of the regulation and the penalty. */
@customElement("kraftvakt-general-page")
export class KraftvaktGeneralPage extends SettingsFormPage {
  /** The power sensor being analysed. */
  @state() private analysing?: string;

  /** How the power sensor reports, from the last analysis. */
  @state() private reports?: { sensor: string; reports: PowerSensorReports | null };

  /** A power sensor the user has just chosen, whose timeout is set to the one suggested when its analysis comes. */
  private suggestTimeoutFor?: string;

  protected render() {
    return html`
      ${this.renderMeasurementCard()}
      ${this.renderSettingsCard("general.regulation", [this.numberField("power_limit_w"), this.numberField("turn_on_margin_w"), this.numberField("wait_at_limit_s")])}
      ${this.renderSettingsCard("general.penalty", [this.numberField("penalty_threshold_w")], "general.penalty_info")} ${this.renderRestoreDefaults(RESTORED_FIELDS)}
    `;
  }

  /** Analyse a power sensor that has not been analysed, such as the saved one when the page opens, or one just chosen. */
  protected willUpdate(changed: PropertyValues<this>): void {
    super.willUpdate(changed);
    const sensor = this.config.general.power_sensor;
    if (sensor && this.analysing !== sensor && this.reports?.sensor !== sensor) {
      void this.analyse(sensor);
    }
  }

  protected changeConfig(config: KraftvaktConfig): void {
    if (config.general.power_sensor !== this.config.general.power_sensor) {
      this.suggestTimeoutFor = config.general.power_sensor ?? undefined;
    }
    super.changeConfig(config);
  }

  private async analyse(sensor: string): Promise<void> {
    this.analysing = sensor;
    let reports: PowerSensorReports | null;
    try {
      reports = await analysePowerSensor(this.hass, sensor);
    } catch {
      reports = null;
    }
    if (this.analysing === sensor) {
      this.analysing = undefined;
    }
    const general = this.config.general;
    if (general.power_sensor !== sensor) {
      return;
    }
    this.reports = { sensor, reports };
    if (reports && this.suggestTimeoutFor === sensor && !this.locked) {
      super.changeConfig({ ...this.config, general: { ...general, power_sensor_timeout_s: reports.suggested_timeout_s } });
    }
    this.suggestTimeoutFor = undefined;
  }

  private renderMeasurementCard() {
    return this.renderCard({
      title: this.localize("general.measurement"),
      sections: [this.renderForm([this.entityField("power_sensor"), this.windowField(), this.numberField("power_sensor_timeout_s")]), this.renderReports()],
    });
  }

  /** How the power sensor reports, for the regulation window and the timeout in the draft. */
  private renderReports() {
    const sensor = this.config.general.power_sensor;
    if (!sensor) {
      return html`<p class="description">${this.localize("reports.no_power_sensor")}</p>`;
    }
    if (this.analysing === sensor || this.reports?.sensor !== sensor) {
      return html`<p class="description">${this.localize("reports.analysing")}</p>`;
    }
    const reports = this.reports.reports;
    if (!reports) {
      return html`<p class="description">${this.localize("reports.not_analysed")}</p>`;
    }
    const general = this.config.general;
    const choices = windowChoices(this.capabilities.limits.general.regulation_window_s);
    const language = this.hass.language;
    return html`
      <div class="reports">
        ${reportLines(reports, general.regulation_window_s, general.power_sensor_timeout_s, choices).map((line) => {
          const text = reportText(line, this.localize, language);
          return line.warning ? html`<ha-alert alert-type="warning">${text}</ha-alert>` : html`<p class="description">${text}</p>`;
        })}
      </div>
    `;
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

  private windowField(): FormField {
    return this.selectField("regulation_window_s", (seconds) => this.localize("general.window_option", { seconds: this.formatNumber(seconds) }));
  }

  static styles = [
    SettingsFormPage.styles,
    css`
      .reports {
        display: grid;
        gap: 8px;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-general-page": KraftvaktGeneralPage;
  }
}
