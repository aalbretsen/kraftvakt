import { mdiDelete, mdiEvStation, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Charger, ChargerGroup, Issue } from "../api";
import "../components/charger-dialog";
import "../components/manual-control-warning";
import type { ItemAdded, ListRow } from "../components/sortable-list";
import { allChargers, moveItem, newId } from "../draft";
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
  "power_reserve_w",
  "car_connected",
  "actively_charging",
  "charging_window",
] as const;

/** EV chargers can be dragged between the lists of all groups. */
const CHARGER_LISTS = "kraftvakt-chargers";

const GROUP_SCHEMA = [
  { name: "name", required: true, selector: { text: {} } },
  { name: "one_at_a_time", selector: { boolean: {} } },
];

/** The groups of EV chargers, each with its settings and its chargers. */
@customElement("kraftvakt-charging-page")
export class KraftvaktChargingPage extends ConfigPage {
  @state() private editing?: { charger: Charger; groupId: string; isNew: boolean };

  protected render() {
    const groups = this.config.charger_groups;
    return html`
      ${groups.length === 0
        ? html`<ha-card><div class="card-content no-groups">${this.localize("charging.no_groups")}</div></ha-card>`
        : groups.map((group) => this.renderGroup(group))}
      <div class="page-footer">
        <ha-button .disabled=${this.locked} @click=${this.addGroup}>
          <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
          ${this.localize("charging.add_group")}
        </ha-button>
      </div>
      ${groups.length > 0 ? html`<div class="switches-info">${this.localize("charging.switches_info")}</div>` : nothing}
      ${allChargers(this.config).length === 0
        ? html`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="chargers"
            ></kraftvakt-manual-control-warning>
          `
        : nothing}
      ${this.editing ? this.renderDialog(this.editing.charger, this.editing.groupId, this.editing.isNew) : nothing}
    `;
  }

  private renderGroup(group: ChargerGroup) {
    const empty = group.chargers.length === 0;
    return this.renderListCard(
      {
        title: group.name.trim() || this.localize("charging.unnamed_group"),
        sub: this.localize("charging.chargers_sub"),
        add: this.localize("charging.add"),
        empty: this.localize("charging.empty"),
        rows: group.chargers.map((charger) => this.row(charger)),
        locked: this.locked,
        group: CHARGER_LISTS,
        onAdd: () => this.addCharger(group),
        onMoved: (event) => this.chargerMoved(group, event),
        onAdded: (event) => this.chargerAdded(group, event),
        onOpen: (event) => this.openRow(group, event),
      },
      html`
        <div class="group-footer">
          <span class="footer-text">${empty ? "" : this.localize("charging.delete_group_not_empty")}</span>
          <ha-button variant="danger" appearance="plain" .disabled=${this.locked || !empty} @click=${() => this.deleteGroup(group)}>
            <ha-svg-icon slot="start" .path=${mdiDelete}></ha-svg-icon>
            ${this.localize("charging.delete_group")}
          </ha-button>
        </div>
      `,
      html`
        <div class="card-content">
          <ha-form
            .hass=${this.hass}
            .data=${group}
            .schema=${GROUP_SCHEMA}
            .error=${this.formErrors("charger_groups", group.id)}
            .disabled=${this.locked}
            .computeLabel=${(field: { name: string }) => this.localize(`charging.${field.name}` as TranslationKey)}
            .computeHelper=${(field: { name: string }) => this.localize(`charging.${field.name}_sub` as TranslationKey)}
            .computeError=${(error: string) => error}
            @value-changed=${(event: CustomEvent<{ value: Partial<ChargerGroup> }>) => this.groupChanged(group, event)}
          ></ha-form>
        </div>
      `,
    );
  }

  private renderDialog(charger: Charger, groupId: string, isNew: boolean) {
    const group = this.config.charger_groups.find((item) => item.id === groupId);
    return html`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${charger}
        .isNew=${isNew}
        .oneAtATime=${group?.one_at_a_time ?? false}
        .usedEntities=${this.entitiesUsedBesides(charger.id)}
        .saveErrors=${this.saveErrors.filter((issue) => issue.section === "chargers" && issue.target === charger.id)}
        .locked=${this.locked}
        @item-changed=${(event: CustomEvent<Charger>) => this.chargerChanged(groupId, event.detail)}
        @item-deleted=${this.chargerDeleted}
        @closed=${() => (this.editing = undefined)}
      ></kraftvakt-charger-dialog>
    `;
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
    if (charger.actively_charging) {
      details.push(
        charger.actively_charging.type === "template"
          ? this.localize("charging.charging_template")
          : this.localize("charging.charging_from", { source: charger.actively_charging.value }),
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

  private groupChanged(group: ChargerGroup, event: CustomEvent<{ value: Partial<ChargerGroup> }>): void {
    const { name, one_at_a_time } = event.detail.value;
    this.changeGroup({ ...group, name: name ?? "", one_at_a_time: one_at_a_time ?? group.one_at_a_time });
  }

  /** A new group is named so that its name is not used by another group. */
  private addGroup(): void {
    const groups = this.config.charger_groups;
    const base = this.localize("charging.new_group_name");
    const names = new Set(groups.map((group) => group.name.trim()));
    let name = base;
    for (let number = 2; names.has(name); number++) {
      name = `${base} ${number}`;
    }
    const defaults = this.capabilities.defaults.charger_groups;
    const group: ChargerGroup = { id: newId(), name, ...defaults, chargers: [] };
    this.changeConfig({ ...this.config, charger_groups: [...groups, group] });
  }

  private deleteGroup(group: ChargerGroup): void {
    this.changeConfig({
      ...this.config,
      charger_groups: this.config.charger_groups.filter((item) => item.id !== group.id),
    });
  }

  private chargerMoved(group: ChargerGroup, event: CustomEvent<{ oldIndex: number; newIndex: number }>): void {
    const { oldIndex, newIndex } = event.detail;
    this.changeGroup({ ...group, chargers: moveItem(group.chargers, oldIndex, newIndex) });
  }

  /** A charger dragged in from another group leaves that group. */
  private chargerAdded(group: ChargerGroup, event: CustomEvent<ItemAdded>): void {
    const { key, index } = event.detail;
    const charger = allChargers(this.config).find((item) => item.id === key);
    if (!charger) {
      return;
    }
    const groups = this.config.charger_groups.map((item) => {
      const chargers = item.chargers.filter((other) => other.id !== key);
      if (item.id === group.id) {
        chargers.splice(index, 0, charger);
      }
      return { ...item, chargers };
    });
    this.changeConfig({ ...this.config, charger_groups: groups });
  }

  private addCharger(group: ChargerGroup): void {
    const defaults = this.capabilities.defaults.chargers;
    const charger: Charger = {
      id: newId(),
      entity_id: null,
      activate: null,
      deactivate: null,
      set_current: null,
      min_current_a: defaults.min_current_a,
      max_current_a: defaults.max_current_a,
      power_reserve_w: defaults.power_reserve_w,
      car_connected: null,
      actively_charging: null,
      charging_window: null,
    };
    this.editing = { charger, groupId: group.id, isNew: true };
  }

  private openRow(group: ChargerGroup, event: CustomEvent<string>): void {
    const charger = group.chargers.find((item) => item.id === event.detail);
    if (charger) {
      this.editing = { charger, groupId: group.id, isNew: false };
    }
  }

  private chargerChanged(groupId: string, charger: Charger): void {
    const group = this.config.charger_groups.find((item) => item.id === groupId);
    if (!group) {
      return;
    }
    const exists = group.chargers.some((item) => item.id === charger.id);
    this.changeGroup({
      ...group,
      chargers: exists
        ? group.chargers.map((item) => (item.id === charger.id ? charger : item))
        : [...group.chargers, charger],
    });
  }

  private chargerDeleted(event: CustomEvent<string>): void {
    const groups = this.config.charger_groups.map((group) => ({
      ...group,
      chargers: group.chargers.filter((item) => item.id !== event.detail),
    }));
    this.changeConfig({ ...this.config, charger_groups: groups });
  }

  private changeGroup(group: ChargerGroup): void {
    const groups = this.config.charger_groups.map((item) => (item.id === group.id ? group : item));
    this.changeConfig({ ...this.config, charger_groups: groups });
  }

  static styles = [
    ConfigPage.styles,
    css`
      .no-groups {
        padding-top: 16px;
        color: var(--secondary-text-color);
      }
      .group-footer {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 8px 8px 16px;
        border-top: 1px solid var(--divider-color);
      }
      .footer-text {
        flex: 1;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
      .page-footer {
        display: flex;
        justify-content: flex-end;
      }
      .switches-info {
        padding: 0 16px;
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
