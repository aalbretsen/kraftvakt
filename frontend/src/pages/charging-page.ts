import { mdiDelete, mdiEvStation, mdiPlus } from "@mdi/js";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Charger, ChargerGroup, Issue } from "../api";
import "../components/charger-dialog";
import "../components/manual-control-warning";
import type { ItemAdded, ListRow } from "../components/sortable-list";
import { allChargers, moveItem, newId } from "../draft";
import { chargerName } from "../entities";
import { formatNumber } from "../format";
import type { TranslationKey } from "../localize";
import { renderDescription, renderSectionHeader } from "../section-styles";
import { issuesFor } from "../validation";
import { ConfigPage, type ItemList } from "./config-page";

const CHARGER_FIELDS = [
  "device_id",
  "entity_id",
  "activate",
  "deactivate",
  "switched_by_current",
  "set_current",
  "min_current_a",
  "max_current_a",
  "min_current_power_w",
  "car_connected",
  "actively_charging",
  "charging_power",
  "cloud_controlled",
  "start_delay_s",
  "charging_window",
  "finish_after_window",
  "override_ends",
  "deactivate_on_fault",
  "fault_flag",
] as const;

const GROUP_SCHEMA = [
  { name: "name", required: true, selector: { text: {} } },
  { name: "one_at_a_time", selector: { boolean: {} } },
  { name: "dynamic_order", selector: { boolean: {} } },
];

/** The groups of EV chargers, each with its settings and its chargers. */
@customElement("kraftvakt-charging-page")
export class KraftvaktChargingPage extends ConfigPage {
  @state() private editing?: { charger: Charger; groupId: string; isNew: boolean };

  protected render() {
    const groups = this.config.charger_groups;
    return html`
      ${groups.length === 0
        ? html`<div class="empty">${this.localize("charging.no_groups")}</div>`
        : groups.map((group) => this.renderGroup(group))}
      ${this.renderPageFooter(
        groups.length > 0 ? this.localize("charging.switches_info") : "",
        html`
          <ha-button .disabled=${this.locked} @click=${this.addGroup}>
            <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
            ${this.localize("charging.add_group")}
          </ha-button>
        `,
      )}
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
    const list: ItemList = {
      add: this.localize("charging.add"),
      empty: this.localize("charging.empty"),
      rows: group.chargers.map((charger) => this.row(charger)),
      locked: this.locked,
      group: "kraftvakt-chargers",
      onAdd: () => this.addCharger(group),
      onMoved: (event) => this.chargerMoved(group, event),
      onAdded: (event) => this.chargerAdded(group, event),
      onOpen: (event) => this.openRow(group, event),
    };
    return this.renderCard({
      title: group.name.trim() || this.localize("charging.unnamed_group"),
      content: html`
        <ha-form
          .hass=${this.hass}
          .data=${group}
          .schema=${GROUP_SCHEMA}
          .error=${this.formErrors("charger_groups", group.id)}
          .disabled=${this.locked}
          .computeLabel=${(field: { name: string }) => this.localize(`charging.${field.name}` as TranslationKey)}
          .computeHelper=${(field: { name: string }) => withLineBreaks(this.localize(`charging.${field.name}_sub` as TranslationKey))}
          .computeError=${(error: string) => error}
          @value-changed=${(event: CustomEvent<{ value: Partial<ChargerGroup> }>) => this.groupChanged(group, event)}
        ></ha-form>
        ${renderSectionHeader(this.localize("charging.chargers"), this.renderAddButton(list))}
        ${renderDescription(this.localize("charging.chargers_sub"))}
      `,
      list: this.renderItemList(list),
      footer: this.renderCardFooter(
        empty ? "" : this.localize("charging.delete_group_not_empty"),
        html`
          <ha-button variant="danger" appearance="plain" .disabled=${this.locked || !empty} @click=${() => this.deleteGroup(group)}>
            <ha-svg-icon slot="start" .path=${mdiDelete}></ha-svg-icon>
            ${this.localize("charging.delete_group")}
          </ha-button>
        `,
      ),
    });
  }

  private renderDialog(charger: Charger, groupId: string, isNew: boolean) {
    return html`
      <kraftvakt-charger-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${charger}
        .isNew=${isNew}
        .usedEntities=${this.entitiesUsedBesides(charger.id)}
        .saveErrors=${issuesFor(this.saveErrors, "chargers", charger.id)}
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
      this.localize("charging.min_current_power", { power: formatNumber(language, charger.min_current_power_w, 0) }),
      charger.charging_window
        ? this.localize("charging.window", { ...charger.charging_window })
        : this.localize("charging.always_allowed"),
    ];
    if (charger.charging_window && charger.finish_after_window) {
      details.push(this.localize("charging.finishes_after_window"));
    }
    if (charger.car_connected) {
      details.push(
        charger.car_connected.type === "entity"
          ? this.localize("charging.car_from", { source: charger.car_connected.value })
          : this.localize("charging.car_template"),
      );
    }
    if (charger.actively_charging?.value) {
      details.push(
        charger.actively_charging.type === "template"
          ? this.localize("charging.charging_template")
          : this.localize("charging.charging_from", { source: charger.actively_charging.value }),
      );
    }
    if (charger.charging_power?.value) {
      details.push(
        charger.charging_power.type === "template"
          ? this.localize("charging.power_template")
          : this.localize("charging.power_from", { source: charger.charging_power.value }),
      );
    }
    if (charger.switched_by_current) {
      details.push(this.localize("charging.switched_by_current"));
    }
    if (charger.deactivate_on_fault) {
      details.push(this.localize("charging.deactivated_on_fault"));
    }
    const issues = issuesFor(this.issues, "chargers", charger.id);
    return {
      key: charger.id,
      title: chargerName(this.hass, this.entityNames, charger) ?? this.localize("missing.charger_without_entity"),
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
    const { name, one_at_a_time, dynamic_order } = event.detail.value;
    this.changeGroup({
      ...group,
      name: name ?? "",
      one_at_a_time: one_at_a_time ?? group.one_at_a_time,
      dynamic_order: dynamic_order ?? group.dynamic_order,
    });
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
      device_id: null,
      entity_id: null,
      activate: null,
      deactivate: null,
      switched_by_current: false,
      set_current: null,
      min_current_a: defaults.min_current_a,
      max_current_a: defaults.max_current_a,
      min_current_power_w: defaults.min_current_power_w,
      car_connected: null,
      actively_charging: null,
      charging_power: null,
      charging_window: null,
      finish_after_window: false,
      override_ends: defaults.override_ends,
      cloud_controlled: false,
      start_delay_s: defaults.start_delay_s,
      deactivate_on_fault: false,
      fault_flag: null,
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

  static styles = ConfigPage.styles;
}

/** A helper text keeps its line breaks, since Home Assistant shows it as one paragraph. */
function withLineBreaks(text: string) {
  return text.split("\n").map((line, index) => (index === 0 ? line : html`<br />${line}`));
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-charging-page": KraftvaktChargingPage;
  }
}
