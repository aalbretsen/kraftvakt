import { html } from "lit";
import { customElement } from "lit/decorators.js";

import { ownEntities } from "../entities";
import { GeneralSettingsPage, type FormField, type GeneralField } from "./general-settings-page";

type CardTitle = "general.measurement" | "general.regulation" | "general.penalty";

/** The power sensor and the settings of the regulation and the penalty. */
@customElement("kraftvakt-general-page")
export class KraftvaktGeneralPage extends GeneralSettingsPage {
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
        html`<ha-alert alert-type="info">${this.localize("general.tariff_window_info")}</ha-alert>`,
      )}
    `;
  }

  private renderCard(title: CardTitle, schema: FormField[], extra?: unknown) {
    return html`
      <ha-card .header=${this.localize(title)}>
        <div class="card-content">${this.renderForm(schema)} ${extra ?? ""}</div>
      </ha-card>
    `;
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

  /** The interval is a whole number of regulation windows. */
  private intervalField(): FormField {
    return this.selectField("regulation_interval", (count) => this.localize("general.interval_option", { count }));
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-general-page": KraftvaktGeneralPage;
  }
}
