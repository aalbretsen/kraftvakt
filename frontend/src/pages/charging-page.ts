import { mdiDelete, mdiEvStation, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Charger, ChargerGroup, Condition, Issue } from "../api";
import "../components/charger-dialog";
import "../components/condition-field";
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
  "switched_by",
  "on_off_entity",
  "activate",
  "deactivate",
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
  "charge_until_disconnected",
  "override_ends",
  "deactivate_on_fault",
  "fault_flag",
] as const;

const SHARING_MODES = ["never", "always", "condition"] as const;
type SharingMode = (typeof SHARING_MODES)[number];

interface GroupForm {
  name: string;
  one_at_a_time: SharingMode;
  dynamic_order: boolean;
}

const NAME_SCHEMA = [{ name: "name", required: true, selector: { text: {} } }];

const DYNAMIC_ORDER_SCHEMA = [{ name: "dynamic_order", selector: { boolean: {} } }];

/** The setting to restrict to one EV charger at a time is named by its section header, so its field says when it applies. */
const FIELD_LABELS: Record<keyof GroupForm, TranslationKey> = {
  name: "charging.name",
  one_at_a_time: "charging.one_at_a_time_applies",
  dynamic_order: "charging.dynamic_order",
};

/** How the chargers of a group share the power makes no difference with fewer than two, so these settings are disabled then, and keep their values. */
const SHARING_FIELDS = new Set(["one_at_a_time", "dynamic_order"]);

/** The groups of EV chargers, each with its settings and its chargers. */
@customElement("kraftvakt-charging-page")
export class KraftvaktChargingPage extends ConfigPage {
  @state() private editing?: { charger: Charger; groupId: string; isNew: boolean };

  protected render() {
    const groups = this.config.charger_groups;
    return html`
      ${groups.length === 0 ? html`<div class="empty">${this.localize("charging.no_groups")}</div>` : groups.map((group) => this.renderGroup(group))}
      ${this.renderPageFooter(
        groups.length > 0 ? this.localize("charging.switches_info") : "",
        html`
          <ha-button .disabled=${this.locked} @click=${this.addGroup}>
            <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
            ${this.localize("charging.add_group")}
          </ha-button>
        `,
      )}
      ${
        allChargers(this.config).length === 0
          ? html` <kraftvakt-manual-control-warning .localize=${this.localize} .narrow=${this.narrow} kind="chargers"></kraftvakt-manual-control-warning> `
          : nothing
      }
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
        ${this.renderGroupForm(group, NAME_SCHEMA)} ${renderSectionHeader(this.localize("charging.one_at_a_time"))}
        ${renderDescription(this.localize("charging.one_at_a_time_sub"))} ${this.renderGroupForm(group, this.sharingSchema())}
        ${typeof group.one_at_a_time === "object" ? this.renderSharingCondition(group, group.one_at_a_time) : nothing}
        ${renderSectionHeader(this.localize("charging.chargers"), this.renderAddButton(list))} ${renderDescription(this.localize("charging.chargers_sub"))}
        ${this.renderGroupForm(group, DYNAMIC_ORDER_SCHEMA)}
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

  private sharingSchema() {
    const options = SHARING_MODES.map((mode) => ({ value: mode, label: this.localize(`charging.one_at_a_time_${mode}`) }));
    return [{ name: "one_at_a_time", required: true, selector: { select: { mode: "dropdown", options } } }];
  }

  private renderGroupForm(group: ChargerGroup, schema: { name: string }[]) {
    const { one_at_a_time: _conditionIssue, ...errors } = this.formErrors("charger_groups", group.id);
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${groupForm(group)}
        .schema=${schema.map((field) => (this.sharingDisabled(group, field.name) ? { ...field, disabled: true } : field))}
        .error=${errors}
        .disabled=${this.locked}
        .computeLabel=${(field: { name: keyof GroupForm }) => this.localize(FIELD_LABELS[field.name])}
        .computeHelper=${(field: { name: string }) => withLineBreaks(this.groupHelper(group, field.name))}
        .computeError=${(error: string) => error}
        @value-changed=${(event: CustomEvent<{ value: Partial<GroupForm> }>) => this.groupChanged(group, event.detail.value)}
      ></ha-form>
    `;
  }

  /** The template gets the power limit of the draft, as the regulation gives it the power limit at the decision. */
  private renderSharingCondition(group: ChargerGroup, condition: Condition) {
    return html`
      <kraftvakt-condition-field
        class="sharing-condition"
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${condition}
        .variables=${{ power_limit: this.config.general.power_limit_w }}
        kind="one_at_a_time"
        .error=${this.formErrors("charger_groups", group.id).one_at_a_time}
        .disabled=${this.locked || this.sharingDisabled(group, "one_at_a_time")}
        @value-changed=${(event: CustomEvent<{ value: Condition }>) => this.changeGroup({ ...group, one_at_a_time: event.detail.value })}
      ></kraftvakt-condition-field>
    `;
  }

  private sharingDisabled(group: ChargerGroup, field: string): boolean {
    return group.chargers.length < 2 && SHARING_FIELDS.has(field);
  }

  /** What restricting to one EV charger at a time does is told under its section header, not under its field. */
  private groupHelper(group: ChargerGroup, field: string): string {
    const helper = field === "one_at_a_time" ? "" : this.localize(`charging.${field}_sub` as TranslationKey);
    const needsTwo = this.sharingDisabled(group, field) ? this.localize("charging.needs_two_chargers") : "";
    return [helper, needsTwo].filter(Boolean).join("\n");
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
    const details = [
      this.localize("charging.currents", {
        min: charger.min_current_a,
        max: charger.max_current_a,
        power: formatNumber(this.hass.language, charger.min_current_power_w, 0),
      }),
    ];
    if (charger.charging_window) {
      const window = this.localize("charging.window", { ...charger.charging_window });
      details.push(charger.charge_until_disconnected ? `${window}, ${this.localize("charging.charges_until_disconnected")}` : window);
    }
    if (charger.deactivate_on_fault) {
      details.push(this.localize("charging.deactivated_on_fault"));
    }
    const issues = issuesFor(this.issues, "chargers", charger.id);
    return {
      key: charger.id,
      title: chargerName(this.hass, this.entityNames, charger) ?? this.localize("missing.charger_without_device"),
      iconPath: mdiEvStation,
      details,
      errors: issues.map((issue) => `${this.fieldLabel(issue)}: ${this.describeIssue(issue)}`),
      openable: true,
    };
  }

  private fieldLabel(issue: Issue): string {
    const field = issue.field ?? "";
    return (CHARGER_FIELDS as readonly string[]).includes(field) ? this.localize(`charger.fields.${field}.label` as TranslationKey) : field;
  }

  /** A condition chosen anew starts as an empty template, as a new variant does. */
  private groupChanged(group: ChargerGroup, value: Partial<GroupForm>): void {
    const mode = value.one_at_a_time ?? groupForm(group).one_at_a_time;
    const sameMode = mode === groupForm(group).one_at_a_time;
    const condition: Condition = { type: "template", value: "" };
    this.changeGroup({
      ...group,
      name: value.name ?? group.name,
      one_at_a_time: sameMode ? group.one_at_a_time : mode === "condition" ? condition : mode === "always",
      dynamic_order: value.dynamic_order ?? group.dynamic_order,
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
      switched_by: defaults.switched_by,
      on_off_entity: null,
      activate: { mode: "custom", action: [] },
      deactivate: { mode: "custom", action: [] },
      set_current: { mode: "entity", entity_id: null },
      min_current_a: defaults.min_current_a,
      max_current_a: defaults.max_current_a,
      min_current_power_w: defaults.min_current_power_w,
      car_connected: null,
      actively_charging: null,
      charging_power: null,
      charging_window: null,
      charge_until_disconnected: false,
      override_ends: defaults.override_ends,
      cloud_controlled: defaults.cloud_controlled,
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
      chargers: exists ? group.chargers.map((item) => (item.id === charger.id ? charger : item)) : [...group.chargers, charger],
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
      .sharing-condition {
        margin-bottom: 24px;
      }
    `,
  ];
}

function groupForm(group: ChargerGroup): GroupForm {
  const sharing = group.one_at_a_time;
  return {
    name: group.name,
    one_at_a_time: typeof sharing === "object" ? "condition" : sharing ? "always" : "never",
    dynamic_order: group.dynamic_order,
  };
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
