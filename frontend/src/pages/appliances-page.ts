import { mdiEvStation } from "@mdi/js";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import { MAIN_ACTIONS, type Appliance, type Issue, type PriorityEntry, type Variant } from "../api";
import "../components/appliance-dialog";
import "../components/manual-control-warning";
import "../components/variant-dialog";
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

  @state() private viewingVariant?: { appliance: Appliance; variant: Variant };

  protected render() {
    const rows = this.config.priority.map((entry) => this.row(entry));
    return html`
      ${this.renderListCard({
        title: "appliances.priority_title",
        sub: "appliances.priority_sub",
        add: "appliances.add",
        empty: "appliances.empty",
        rows,
        locked: this.locked,
        onAdd: this.addAppliance,
        onMoved: this.entryMoved,
        onOpen: this.openRow,
      })}
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
      ${this.viewingVariant ? this.renderVariantDialog(this.viewingVariant.appliance, this.viewingVariant.variant) : ""}
    `;
  }

  private renderVariantDialog(appliance: Appliance, variant: Variant) {
    return html`
      <kraftvakt-variant-dialog
        .heading=${this.localize("appliances.variant_dialog_title")}
        .text=${this.localize("appliances.variant_dialog_text", {
          label: variant.label,
          appliance: this.applianceName(appliance),
        })}
        .closeText=${this.localize("dialog.close")}
        @closed=${() => (this.viewingVariant = undefined)}
      ></kraftvakt-variant-dialog>
    `;
  }

  private renderDialog(appliance: Appliance, isNew: boolean) {
    return html`
      <kraftvakt-appliance-dialog
        .hass=${this.hass}
        .localize=${this.localize}
        .capabilities=${this.capabilities}
        .item=${appliance}
        .isNew=${isNew}
        .usedEntities=${this.entitiesUsedBesides(appliance.id)}
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
      details: appliance ? (variant ? this.variantDetails(appliance, variant) : this.applianceDetails(appliance)) : [],
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

  private variantDetails(appliance: Appliance, variant: Variant): string[] {
    const source =
      variant.condition.type === "entity"
        ? this.localize("appliances.variant_entity", { entity: variant.condition.value })
        : this.localize("appliances.variant_template");
    return appliance.actions[variant.id] ? [source, this.localize("appliances.variant_own_actions")] : [source];
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
      actions: { [MAIN_ACTIONS]: { turn_on: null, turn_off: null } },
      power_reserve_w: this.capabilities.defaults.appliances.power_reserve_w,
      variants: [],
    };
    this.editing = { appliance, isNew: true };
  }

  /** A variant is configured in the dialog of its appliance, which its row tells. */
  private openRow(event: CustomEvent<string>): void {
    const entry = this.config.priority.find((item) => priorityKey(item) === event.detail);
    if (entry?.type !== "appliance") {
      return;
    }
    const appliance = this.config.appliances.find((item) => item.id === entry.appliance_id);
    const variant = appliance?.variants.find((item) => item.id === entry.variant_id);
    if (appliance && variant) {
      this.viewingVariant = { appliance, variant };
    } else if (appliance) {
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

  static styles = ConfigPage.styles;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-appliances-page": KraftvaktAppliancesPage;
  }
}
