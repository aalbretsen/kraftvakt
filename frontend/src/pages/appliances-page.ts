import { mdiEvStation, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import type { Appliance, Issue, PriorityEntry } from "../api";
import "../components/appliance-dialog";
import "../components/manual-control-warning";
import "../components/sortable-list";
import type { ListRow } from "../components/sortable-list";
import { moveItem, newId, priorityKey } from "../draft";
import { entityName } from "../entities";
import { formatNumber } from "../format";
import type { TranslationKey } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import { ConfigPage } from "./config-page";

const APPLIANCE_FIELDS = ["entity_id", "turn_on", "turn_off", "power_reserve_w", "label", "condition"] as const;

/** The appliances and the priority list. */
@customElement("kraftvakt-appliances-page")
export class KraftvaktAppliancesPage extends ConfigPage {
  @state() private editing?: { appliance: Appliance; isNew: boolean };

  protected render() {
    const rows = this.config.priority.map((entry) => this.row(entry));
    return html`
      <ha-card>
        <div class="card-header">
          <div class="heading">
            <span>${this.localize("appliances.priority_title")}</span>
            <span class="sub">${this.localize("appliances.priority_sub")}</span>
          </div>
          <ha-button .disabled=${this.locked} @click=${this.addAppliance}>
            <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
            ${this.localize("appliances.add")}
          </ha-button>
        </div>
        ${rows.length === 0
          ? html`<div class="empty">${this.localize("appliances.empty")}</div>`
          : html`
              <kraftvakt-sortable-list
                .localize=${this.localize}
                .rows=${rows}
                .locked=${this.locked}
                @item-moved=${this.entryMoved}
                @open-row=${this.openRow}
              ></kraftvakt-sortable-list>
            `}
      </ha-card>
      ${this.config.appliances.length === 0
        ? html`
            <kraftvakt-manual-control-warning
              .localize=${this.localize}
              .narrow=${this.narrow}
              kind="appliances"
            ></kraftvakt-manual-control-warning>
          `
        : nothing}
      ${this.editing ? this.renderDialog(this.editing.appliance, this.editing.isNew) : ""}
    `;
  }

  private renderDialog(appliance: Appliance, isNew: boolean) {
    const usedEntities = [...this.config.appliances, ...this.config.charging.chargers]
      .filter((item) => item.id !== appliance.id && item.entity_id)
      .map((item) => item.entity_id as string);
    return html`
      <kraftvakt-appliance-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${appliance}
        .isNew=${isNew}
        .usedEntities=${usedEntities}
        .saveErrors=${this.saveErrors.filter((issue) => issue.section === "appliances" && issue.target === appliance.id)}
        .locked=${this.locked}
        @item-changed=${this.applianceChanged}
        @item-deleted=${this.applianceDeleted}
        @closed=${() => (this.editing = undefined)}
      ></kraftvakt-appliance-dialog>
    `;
  }

  private row(entry: PriorityEntry): ListRow {
    if (entry.type === "ev_charging") {
      return {
        key: priorityKey(entry),
        title: this.localize("appliances.ev_charging"),
        iconPath: mdiEvStation,
        details: [
          html`${this.localize("appliances.ev_charging_sub", { count: this.config.charging.chargers.length })}
            <a href="${PANEL_PATH}/charging" @click=${this.openChargingPage}>${this.localize("tabs.charging")}</a>`,
        ],
        errors: [],
        openable: false,
      };
    }
    const appliance = this.config.appliances.find((item) => item.id === entry.appliance_id);
    const variant = appliance?.variants.find((item) => item.id === entry.variant_id);
    const issues = this.issues.filter(
      (issue) =>
        issue.section === "appliances" &&
        issue.target === entry.appliance_id &&
        (variant ? issue.field?.startsWith(`variants.${variant.id}.`) : !issue.field?.startsWith("variants.")),
    );
    return {
      key: priorityKey(entry),
      title: appliance ? this.applianceName(appliance) : "",
      tag: variant?.label,
      details: appliance ? (variant ? [this.variantSource(variant.condition)] : this.applianceDetails(appliance)) : [],
      errors: issues.map((issue) => `${this.fieldLabel(issue)}: ${this.describeIssue(issue)}`),
      openable: true,
    };
  }

  private applianceName(appliance: Appliance): string {
    return appliance.entity_id
      ? entityName(this.hass, this.entityNames, appliance.entity_id)
      : this.localize("missing.appliance_without_entity");
  }

  private applianceDetails(appliance: Appliance): string[] {
    const details = appliance.entity_id ? [appliance.entity_id] : [];
    if (appliance.power_reserve_w !== null) {
      details.push(
        this.localize("appliances.power_reserve", {
          power: formatNumber(this.hass.language, appliance.power_reserve_w, 0),
        }),
      );
    }
    if (appliance.variants.length > 0) {
      details.push(this.localize("appliances.variant_count", { count: appliance.variants.length }));
    }
    return details;
  }

  private variantSource(condition: Appliance["variants"][number]["condition"]): string {
    return condition.type === "entity"
      ? this.localize("appliances.variant_entity", { entity: condition.value })
      : this.localize("appliances.variant_template");
  }

  private fieldLabel(issue: Issue): string {
    const field = issue.field?.split(".").at(-1) ?? "";
    return (APPLIANCE_FIELDS as readonly string[]).includes(field)
      ? this.localize(`appliance.fields.${field}.label` as TranslationKey)
      : field;
  }

  private entryMoved(event: CustomEvent<{ oldIndex: number; newIndex: number }>): void {
    const { oldIndex, newIndex } = event.detail;
    this.changeConfig({ ...this.config, priority: moveItem(this.config.priority, oldIndex, newIndex) });
  }

  private addAppliance(): void {
    const appliance: Appliance = {
      id: newId(),
      entity_id: null,
      turn_on: null,
      turn_off: null,
      power_reserve_w: this.capabilities.defaults.appliances.power_reserve_w,
      variants: [],
    };
    this.editing = { appliance, isNew: true };
  }

  /** A variant opens its appliance. */
  private openRow(event: CustomEvent<string>): void {
    const entry = this.config.priority.find((item) => priorityKey(item) === event.detail);
    const appliance =
      entry?.type === "appliance" ? this.config.appliances.find((item) => item.id === entry.appliance_id) : undefined;
    if (appliance) {
      this.editing = { appliance, isNew: false };
    }
  }

  /** New variants end up at the bottom of the priority list. */
  private applianceChanged(event: CustomEvent<Appliance>): void {
    const appliance = event.detail;
    const exists = this.config.appliances.some((item) => item.id === appliance.id);
    const appliances = exists
      ? this.config.appliances.map((item) => (item.id === appliance.id ? appliance : item))
      : [...this.config.appliances, appliance];
    this.changeConfig({ ...this.config, appliances });
  }

  /** Take the appliance out of the draft, with its entries in the priority list. */
  private applianceDeleted(event: CustomEvent<string>): void {
    this.changeConfig({ ...this.config, appliances: this.config.appliances.filter((item) => item.id !== event.detail) });
  }

  private openChargingPage(event: Event): void {
    event.preventDefault();
    navigateToPage("charging");
  }

  static styles = css`
    :host {
      display: grid;
      gap: 16px;
    }
    :host([narrow]) {
      gap: 8px;
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
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-appliances-page": KraftvaktAppliancesPage;
  }
}
