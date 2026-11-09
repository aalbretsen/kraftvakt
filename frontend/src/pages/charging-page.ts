import { mdiEvStation, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Charger, Issue } from "../api";
import "../components/charger-dialog";
import "../components/manual-control-warning";
import "../components/sortable-list";
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
 * All configuration of EV charging: the shared settings,
 * the EV chargers in the configured charging priority
 * and, while there are no chargers, the warning against manual control.
 *
 * While EV charging is disabled, the chargers are kept but not used,
 * so the list is only shown.
 */
@customElement("kraftvakt-charging-page")
export class KraftvaktChargingPage extends ConfigPage {
  /** The charger in the dialog, and whether it is new. */
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
    const locked = this.locked || !charging.enabled;
    return html`
      <ha-card class=${charging.enabled ? "" : "disabled"}>
        <div class="card-header">
          <div class="heading">
            <span>${this.localize("charging.chargers")}</span>
            <span class="sub">${this.localize("charging.chargers_sub")}</span>
          </div>
          ${locked
            ? nothing
            : html`
                <ha-button @click=${this.addCharger}>
                  <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
                  ${this.localize("charging.add")}
                </ha-button>
              `}
        </div>
        ${charging.chargers.length === 0
          ? html`<div class="empty">${this.localize("charging.empty")}</div>`
          : html`
              <kraftvakt-sortable-list
                .localize=${this.localize}
                .rows=${charging.chargers.map((charger) => this.row(charger))}
                .locked=${locked}
                @item-moved=${this.chargerMoved}
                @open-row=${this.openRow}
              ></kraftvakt-sortable-list>
            `}
        <div class="switches-info">${this.localize("charging.switches_info")}</div>
      </ha-card>
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
    const usedEntities = [...this.config.appliances, ...this.config.charging.chargers]
      .filter((item) => item.id !== charger.id && item.entity_id)
      .map((item) => item.entity_id as string);
    return html`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${charger}
        .isNew=${isNew}
        .oneAtATime=${this.config.charging.one_at_a_time}
        .usedEntities=${usedEntities}
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

  /** The name of the field the issue is about, as the charger dialog shows it. */
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

  static styles = css`
    :host {
      display: grid;
      gap: 16px;
    }
    :host([narrow]) {
      gap: 8px;
    }
    .card-content {
      padding: 0 16px 16px;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
    }
    .heading {
      flex: 1;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 4px 12px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .sub {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .empty {
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
    }
    .disabled kraftvakt-sortable-list {
      opacity: 0.6;
    }
    .switches-info {
      padding: 12px 16px;
      border-top: 1px solid var(--divider-color);
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-charging-page": KraftvaktChargingPage;
  }
}
