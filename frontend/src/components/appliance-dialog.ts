import { mdiDragHorizontalVariant, mdiEye, mdiPencil, mdiPlus } from "@mdi/js";
import { css, html, nothing, type PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import type { Appliance, Condition, Issue, Variant } from "../api";
import { displaySensorScope, displayValuesForEntity } from "../devices";
import { moveItem, newId } from "../draft";
import { APPLIANCE_ACTIONS, applianceErrors, missingInAppliance } from "../validation";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

export const APPLIANCE_ACTION_VARIABLES = ["entity_id", "entity"];

/**
 * Adds or edits one appliance, and lists its variants by label.
 *
 * An essential appliance has no power reserve and no variants, so their
 * groups are left out, and it can only be made essential without variants.
 * The power reserve is cleared when its switch is turned off.
 *
 * A variant is configured, and deleted, in its own dialog, which edits the
 * appliance as it is in the draft. «Edit» on a variant fires
 * `variant-opened` with its id and closes this dialog. It is disabled while
 * the appliance is new or this dialog has changes.
 */
@customElement("kraftvakt-appliance-dialog")
export class KraftvaktApplianceDialog extends ItemDialog<Appliance> {
  protected readonly section = "appliances";

  protected readonly texts = "appliance";

  /** Whether the fixed load switch is on, also while the power reserve is not given yet. */
  @state() private fixedLoad = false;

  protected willUpdate(changed: PropertyValues<this>): void {
    super.willUpdate(changed);
    if (changed.has("item")) {
      this.fixedLoad = this.item.power_reserve_w !== null;
    }
  }

  /** Also clears the display sensors that are not on the device of the new entity. */
  protected actionsForEntity(entityId: string | null): Partial<Appliance> {
    return {
      ...displayValuesForEntity(this.draft, entityId, this.hass),
      turn_on: this.actionForEntity("turn_on", this.draft.turn_on, entityId),
      turn_off: this.actionForEntity("turn_off", this.draft.turn_off, entityId),
      variants: this.draft.variants.map((variant) => ({
        ...variant,
        actions: Object.fromEntries(Object.entries(variant.actions).map(([name, action]) => [name, this.actionForEntity(name, action ?? null, entityId)])),
      })),
    };
  }

  protected errors(): Issue[] {
    return applianceErrors(this.draft, this.capabilities, this.hass);
  }

  protected missing(): Issue[] {
    return missingInAppliance(this.draft);
  }

  protected renderFields(issues: Issue[]) {
    const essential = this.draft.essential;
    return html`
      ${this.renderEntity(issues)} ${this.renderActions(issues)} ${this.renderEssential(issues)} ${essential ? nothing : this.renderFixedLoad(issues)}
      ${essential ? nothing : this.renderVariants()} ${this.renderDisplayValues(issues)}
    `;
  }

  private renderEssential(issues: Issue[]) {
    const issue = issues.find((item) => item.field === "essential");
    return this.renderGroup({
      title: this.label("essential"),
      description: this.helper("essential"),
      toggle: {
        checked: this.draft.essential,
        disabled: !this.draft.essential && this.draft.variants.length > 0,
        changed: this.essentialChanged,
      },
      error: issue ? this.describe(issue) : undefined,
    });
  }

  private essentialChanged = (checked: boolean): void => {
    if (checked) {
      this.fixedLoadChanged(false);
    }
    this.changeDraft({ essential: checked });
  };

  /** The power reserve stays in view while it has an error, so the error that keeps the draft from being saved can be seen. */
  private renderFixedLoad(issues: Issue[]) {
    const showReserve = this.fixedLoad || issues.some((issue) => issue.field === "power_reserve_w");
    return this.renderGroup({
      title: this.label("fixed_load"),
      description: this.helper("fixed_load"),
      toggle: { checked: this.fixedLoad, changed: this.fixedLoadChanged },
      content: showReserve
        ? this.renderForm([this.numberField("power_reserve_w", "W", false)], issues, (value) =>
            this.changeDraft({ power_reserve_w: (value.power_reserve_w as number | undefined) ?? null }),
          )
        : nothing,
    });
  }

  private fixedLoadChanged = (checked: boolean): void => {
    this.fixedLoad = checked;
    if (!checked) {
      this.changeDraft({ power_reserve_w: null });
    }
  };

  private renderDisplayValues(issues: Issue[]) {
    return this.renderGroup({
      title: this.localize("appliance.display_values"),
      description: this.localize("appliance.display_values_info"),
      content: html` ${this.renderDisplayValue("display_power", issues)} ${this.renderDisplayValue("display_temperature", issues)} `,
    });
  }

  private renderDisplayValue(field: "display_power" | "display_temperature", issues: Issue[]) {
    const issue = issues.find((item) => item.field === field);
    return html`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[field]}
        .entityId=${this.draft.entity_id}
        .includeEntities=${displaySensorScope(this.hass, this.draft)}
        .kind=${field}
        optional
        .error=${issue ? this.describe(issue) : undefined}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: Condition }>) => this.changeDraft({ [field]: event.detail.value })}
      ></kraftvakt-condition-field>
    `;
  }

  private renderActions(issues: Issue[]) {
    return APPLIANCE_ACTIONS.map((name) => this.renderActionGroup(name, issues, APPLIANCE_ACTION_VARIABLES));
  }

  /** The variants, sorted in the order their expressions are evaluated, with their errors. Left out in view mode when there are none. */
  private renderVariants() {
    if (this.locked && this.draft.variants.length === 0) {
      return nothing;
    }
    const errors = [...this.errors(), ...this.saveErrors];
    const editable = this.locked || this.errors().length === 0;
    return this.renderGroup({
      title: this.localize("appliance.variants"),
      description: this.localize("appliance.variants_info"),
      control: this.locked
        ? nothing
        : html`
            <ha-button @click=${this.addVariant}>
              <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
              ${this.localize("appliance.add_variant")}
            </ha-button>
          `,
      content:
        this.draft.variants.length === 0
          ? nothing
          : html`
              <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
                <div class="variants">
                  ${repeat(
                    this.draft.variants,
                    (variant) => variant.id,
                    (variant) => this.renderVariant(variant, errors, editable),
                  )}
                </div>
              </ha-sortable>
            `,
    });
  }

  /**
   * The label of the variant, with what else is wrong in the variant under it.
   * What is missing is shown in the priority list and the variant dialog, where it is set.
   */
  private renderVariant(variant: Variant, issues: Issue[], editable: boolean) {
    const prefix = `variants.${variant.id}.`;
    const variantIssues = issues.filter((issue) => issue.field?.startsWith(prefix)).map((issue) => ({ ...issue, field: issue.field?.slice(prefix.length) }));
    const otherIssues = variantIssues.filter((issue) => issue.field !== "label");
    return html`
      <div class="variant">
        <div class="variant-row">
          ${this.locked ? nothing : html`<ha-svg-icon class="handle" .path=${mdiDragHorizontalVariant}></ha-svg-icon>`}
          <div class="label">
            ${this.renderForm(LABEL_SCHEMA, variantIssues, (value) => this.changeVariant(variant.id, { label: (value.label as string | undefined) ?? "" }), variant)}
          </div>
          <ha-icon-button
            .path=${this.locked ? mdiEye : mdiPencil}
            .label=${this.localize(this.locked ? "list.view" : "list.edit")}
            .disabled=${!editable}
            @click=${() => this.openVariant(variant.id)}
          ></ha-icon-button>
        </div>
        ${otherIssues.map((issue) => html`<div class="error">${this.label(issue.field ?? "")}: ${this.describe(issue)}</div>`)}
      </div>
    `;
  }

  /** The variant dialog edits the appliance as it is in the draft, so the changes here are applied first. */
  private openVariant(id: string): void {
    if (!this.locked) {
      this.dispatchEvent(new CustomEvent("item-changed", { detail: this.draft }));
    }
    this.dispatchEvent(new CustomEvent("variant-opened", { detail: id }));
    this.close();
  }

  private addVariant(): void {
    const variant: Variant = { id: newId(), label: "", condition: { type: "template", value: "" }, actions: {} };
    this.changeDraft({ variants: [...this.draft.variants, variant] });
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
        gap: 8px;
      }
      .variant-row {
        display: flex;
        align-items: center;
        gap: 4px;
      }
      .label {
        flex: 1;
        min-width: 0;
      }
      .handle {
        cursor: grab;
        color: var(--secondary-text-color);
      }
      .variant .error {
        margin-top: 4px;
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
