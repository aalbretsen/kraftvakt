import { mdiDelete, mdiDragHorizontalVariant, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import type { Appliance, Condition, Issue, Variant } from "../api";
import { moveItem, newId } from "../draft";
import { applianceErrors, missingInAppliance } from "../validation";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

const ACTION_VARIABLES = ["entity_id", "entity"];

/**
 * Adds or edits one appliance: its entity, its actions, its power reserve and
 * its variants.
 */
@customElement("kraftvakt-appliance-dialog")
export class KraftvaktApplianceDialog extends ItemDialog<Appliance> {
  protected readonly section = "appliances";

  protected readonly texts = "appliance";

  protected readonly actionFields = ["turn_on", "turn_off"] as const;

  protected errors(): Issue[] {
    return applianceErrors(this.draft, this.capabilities);
  }

  protected missing(): Issue[] {
    return missingInAppliance(this.draft);
  }

  protected renderFields(issues: Issue[]) {
    return html`
      ${this.renderEntity(issues)} ${this.renderSection("appliance.actions")}
      ${this.actionFields.map((field) => this.renderAction(field, issues, ACTION_VARIABLES))}
      ${this.renderForm([this.numberField("power_reserve_kw", "kW", false)], issues, (value) =>
        this.changeDraft({ power_reserve_kw: (value.power_reserve_kw as number | undefined) ?? null }),
      )}
      ${this.renderVariants(issues)}
    `;
  }

  /** The variants, sorted in the order their expressions are evaluated. */
  private renderVariants(issues: Issue[]) {
    return html`
      ${this.renderSection("appliance.variants")}
      <div class="info">${this.localize("appliance.variants_info")}</div>
      <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
        <div class="variants">
          ${repeat(
            this.draft.variants,
            (variant) => variant.id,
            (variant, index) => this.renderVariant(variant, index, issues),
          )}
        </div>
      </ha-sortable>
      ${this.locked
        ? nothing
        : html`
            <div>
              <ha-button appearance="outlined" @click=${this.addVariant}>
                <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
                ${this.localize("appliance.add_variant")}
              </ha-button>
            </div>
          `}
    `;
  }

  private renderVariant(variant: Variant, index: number, issues: Issue[]) {
    const prefix = `variants.${variant.id}.`;
    const variantIssues = issues
      .filter((issue) => issue.field?.startsWith(prefix))
      .map((issue) => ({ ...issue, field: issue.field?.slice(prefix.length) }));
    const conditionIssue = variantIssues.find((issue) => issue.field === "condition");
    return html`
      <div class="variant">
        <div class="variant-header">
          ${this.locked ? nothing : html`<ha-svg-icon class="handle" .path=${mdiDragHorizontalVariant}></ha-svg-icon>`}
          <b>${index + 1}.</b>
          <span class="spacer"></span>
          ${this.locked
            ? nothing
            : html`
                <ha-icon-button
                  .path=${mdiDelete}
                  .label=${this.localize("appliance.remove_variant")}
                  @click=${() => this.removeVariant(variant.id)}
                ></ha-icon-button>
              `}
        </div>
        ${this.renderForm(
          LABEL_SCHEMA,
          variantIssues,
          (value) => this.changeVariant(variant.id, { label: (value.label as string | undefined) ?? "" }),
          variant,
        )}
        <kraftvakt-condition-field
          .hass=${this.hass}
          .localize=${this.localize}
          .value=${variant.condition}
          .entityId=${this.draft.entity_id}
          .error=${conditionIssue ? this.describe(conditionIssue) : undefined}
          .disabled=${this.locked}
          @value-changed=${(event: CustomEvent<{ value: Condition | null }>) =>
            event.detail.value && this.changeVariant(variant.id, { condition: event.detail.value })}
        ></kraftvakt-condition-field>
      </div>
    `;
  }

  private addVariant(): void {
    const variant: Variant = { id: newId(), label: "", condition: { type: "template", value: "" } };
    this.changeDraft({ variants: [...this.draft.variants, variant] });
  }

  private removeVariant(id: string): void {
    this.changeDraft({ variants: this.draft.variants.filter((variant) => variant.id !== id) });
  }

  private changeVariant(id: string, changes: Partial<Variant>): void {
    this.changeDraft({
      variants: this.draft.variants.map((variant) => (variant.id === id ? { ...variant, ...changes } : variant)),
    });
  }

  private variantMoved(event: CustomEvent<{ oldIndex: number; newIndex: number }>): void {
    event.stopPropagation();
    this.changeDraft({ variants: moveItem(this.draft.variants, event.detail.oldIndex, event.detail.newIndex) });
  }

  static styles = [
    ItemDialog.styles,
    css`
      .variants {
        display: grid;
        gap: 12px;
      }
      .variant {
        display: grid;
        gap: 8px;
        padding: 8px 12px 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-border-radius-md, 8px);
        background: var(--card-background-color);
      }
      .variant-header {
        display: flex;
        align-items: center;
        gap: 8px;
        min-height: 40px;
      }
      .handle {
        cursor: grab;
        color: var(--secondary-text-color);
      }
    `,
  ];
}

const LABEL_SCHEMA = [{ name: "label", required: true, selector: { text: {} } }];

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-appliance-dialog": KraftvaktApplianceDialog;
  }
}
