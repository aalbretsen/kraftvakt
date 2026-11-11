import { mdiEvStation } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Charger, Issue } from "../api";
import "../components/charger-dialog";
import "../components/manual-control-warning";
import type { ListRow } from "../components/sortable-list";
import { moveItem, newId } from "../draft";
import { chargerName } from "../entities";
import { formatNumber } from "../format";
import type { TranslationKey } from "../localize";
import { ConfigPage } from "./config-page";

const CHARGER_FIELDS = [
  "entity_id",
  "activate",
  "deactivate",
  "set_current",
  "min_current_a",
  "max_current_a",
  "charge_power_sensor",
  "power_reserve_w",
  "car_connected",
  "charging_window",
] as const;

/**
 * All configuration of EV charging. While it is disabled, the chargers are kept
 * but only shown.
 */
@customElement("kraftvakt-charging-page")
export class KraftvaktChargingPage extends ConfigPage {
  @state() private editing?: { charger: Charger; isNew: boolean };

  protected render() {
    const charging = this.config.charging;
    return html`
      <ha-card .header=${this.localize("charging.shared")}>
        <div class="card-content">
          <ha-form
            .hass=${this.hass}
            .data=${charging}
            .schema=${this.sharedSchema}
            .disabled=${this.locked}
            .computeLabel=${(field: { name: string }) => this.localize(`charging.${field.name}` as TranslationKey)}
            .computeHelper=${(field: { name: string }) => this.localize(`charging.${field.name}_sub` as TranslationKey)}
            @value-changed=${this.sharedChanged}
          ></ha-form>
        </div>
      </ha-card>
      ${charging.enabled ? nothing : html`<ha-alert alert-type="info">${this.localize("charging.disabled_info")}</ha-alert>`}
      ${this.renderChargers()} ${this.editing ? this.renderDialog(this.editing.charger, this.editing.isNew) : nothing}
    `;
  }

  private renderChargers() {
    const charging = this.config.charging;
    return html`
      ${this.renderListCard(
        {
          title: "charging.chargers",
          sub: "charging.chargers_sub",
          add: "charging.add",
          empty: "charging.empty",
          rows: charging.chargers.map((charger) => this.row(charger)),
          locked: this.locked || !charging.enabled,
          onAdd: this.addCharger,
          onMoved: this.chargerMoved,
          onOpen: this.openRow,
        },
        html`<div class="switches-info">${this.localize("charging.switches_info")}</div>`,
      )}
      ${charging.chargers.length === 0
        ? html`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="chargers"
            ></kraftvakt-manual-control-warning>
          `
        : nothing}
    `;
  }

  private renderDialog(charger: Charger, isNew: boolean) {
    return html`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${charger}
        .isNew=${isNew}
        .oneAtATime=${this.config.charging.one_at_a_time}
        .usedEntities=${this.entitiesUsedBesides(charger.id)}
        .saveErrors=${this.saveErrors.filter((issue) => issue.section === "chargers" && issue.target === charger.id)}
        .locked=${this.locked || !this.config.charging.enabled}
        @item-changed=${this.chargerChanged}
        @item-deleted=${this.chargerDeleted}
        @closed=${() => (this.editing = undefined)}
      ></kraftvakt-charger-dialog>
    `;
  }

  /** «One at a time» only matters while EV charging is enabled. */
  private get sharedSchema() {
    return [
      { name: "enabled", selector: { boolean: {} } },
      ...(this.config.charging.enabled ? [{ name: "one_at_a_time", selector: { boolean: {} } }] : []),
    ];
  }

  private row(charger: Charger): ListRow {
    const language = this.hass.language;
    const details = [
      this.localize("charging.currents", { min: charger.min_current_a, max: charger.max_current_a }),
      this.localize("charging.reserve", { power: formatNumber(language, charger.power_reserve_w, 0) }),
      charger.charging_window
        ? this.localize("charging.window", { ...charger.charging_window })
        : this.localize("charging.always_allowed"),
    ];
    if (charger.car_connected) {
      details.push(
        charger.car_connected.type === "entity"
          ? this.localize("charging.car_from", { source: charger.car_connected.value })
          : this.localize("charging.car_template"),
      );
    }
    const issues = this.issues.filter((issue) => issue.section === "chargers" && issue.target === charger.id);
    return {
      key: charger.id,
      title: charger.entity_id
        ? chargerName(this.hass, this.entityNames, charger.entity_id)
        : this.localize("missing.charger_without_entity"),
      iconPath: mdiEvStation,
      details,
      errors: issues.map((issue) => `${this.fieldLabel(issue)}: ${this.describeIssue(issue)}`),
      openable: true,
    };
  }

  private fieldLabel(issue: Issue): string {
    const field = issue.field ?? "";
    return (CHARGER_FIELDS as readonly string[]).includes(field)
      ? this.localize(`charger.fields.${field}.label` as TranslationKey)
      : field;
  }

  /** Changing the shared settings also adds or removes «EV charging» in the priority list. */
  private sharedChanged(event: CustomEvent<{ value: { enabled?: boolean; one_at_a_time?: boolean } }>): void {
    const { enabled, one_at_a_time } = event.detail.value;
    const charging = this.config.charging;
    this.changeConfig({
      ...this.config,
      charging: {
        ...charging,
        enabled: enabled ?? false,
        one_at_a_time: one_at_a_time ?? charging.one_at_a_time,
      },
    });
  }

  private chargerMoved(event: CustomEvent<{ oldIndex: number; newIndex: number }>): void {
    const { oldIndex, newIndex } = event.detail;
    const charging = this.config.charging;
    this.changeConfig({ ...this.config, charging: { ...charging, chargers: moveItem(charging.chargers, oldIndex, newIndex) } });
  }

  private addCharger(): void {
    const defaults = this.capabilities.defaults.chargers;
    const charger: Charger = {
      id: newId(),
      entity_id: null,
      activate: null,
      deactivate: null,
      set_current: null,
      min_current_a: defaults.min_current_a,
      max_current_a: defaults.max_current_a,
      charge_power_sensor: null,
      power_reserve_w: defaults.power_reserve_w,
      car_connected: null,
      charging_window: null,
    };
    this.editing = { charger, isNew: true };
  }

  private openRow(event: CustomEvent<string>): void {
    const charger = this.config.charging.chargers.find((item) => item.id === event.detail);
    if (charger) {
      this.editing = { charger, isNew: false };
    }
  }

  private chargerChanged(event: CustomEvent<Charger>): void {
    const charger = event.detail;
    const chargers = this.config.charging.chargers;
    const exists = chargers.some((item) => item.id === charger.id);
    this.changeChargers(
      exists ? chargers.map((item) => (item.id === charger.id ? charger : item)) : [...chargers, charger],
    );
  }

  private chargerDeleted(event: CustomEvent<string>): void {
    this.changeChargers(this.config.charging.chargers.filter((item) => item.id !== event.detail));
  }

  private changeChargers(chargers: Charger[]): void {
    this.changeConfig({ ...this.config, charging: { ...this.config.charging, chargers } });
  }

  static styles = [
    ConfigPage.styles,
    css`
      .switches-info {
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-charging-page": KraftvaktChargingPage;
  }
}
