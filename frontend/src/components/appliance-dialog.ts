import { mdiDelete, mdiDragHorizontalVariant, mdiEye, mdiPencil, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import { MAIN_ACTIONS, type ActionConfig, type Appliance, type ApplianceActions, type Issue, type Variant } from "../api";
import { moveItem, newId } from "../draft";
import { APPLIANCE_ACTIONS, applianceErrors, missingInAppliance } from "../validation";
import { ItemDialog } from "./item-dialog";

export const APPLIANCE_ACTION_VARIABLES = ["entity_id", "entity"];

/**
 * Adds or edits one appliance, and lists its variants by label.
 *
 * A variant is configured in its own dialog, which edits the appliance as it
 * is in the draft. «Edit» on a variant fires `variant-opened` with its id and
 * closes this dialog. It is disabled while the appliance is new or this
 * dialog has changes.
 */
@customElement("kraftvakt-appliance-dialog")
export class KraftvaktApplianceDialog extends ItemDialog<Appliance> {
  protected readonly section = "appliances";

  protected readonly texts = "appliance";

  protected actionsForEntity(entityId: string | null): Partial<Appliance> {
    const actions = Object.fromEntries(
      Object.entries(this.draft.actions).map(([key, own]) => [
        key,
        Object.fromEntries(
          Object.entries(own).map(([name, action]) => [
            name,
            this.actionForEntity(name, action as ActionConfig | null, entityId),
          ]),
        ),
      ]),
    );
    return { actions };
  }

  protected errors(): Issue[] {
    return applianceErrors(this.draft, this.capabilities, this.hass.states);
  }

  protected missing(): Issue[] {
    return missingInAppliance(this.draft);
  }

  protected renderFields(issues: Issue[]) {
    return html`
      ${this.renderEntity(issues)} ${this.renderSection("appliance.actions")} ${this.renderActions(issues)}
      ${this.renderForm([this.numberField("power_reserve_w", "W", false)], issues, (value) =>
        this.changeDraft({ power_reserve_w: (value.power_reserve_w as number | undefined) ?? null }),
      )}
      ${this.renderVariants(issues)}
    `;
  }

  private renderActions(issues: Issue[]) {
    const actions = this.draft.actions[MAIN_ACTIONS];
    return APPLIANCE_ACTIONS.map((name) =>
      this.renderActionField(
        { name, field: name, value: actions?.[name] ?? null },
        issues,
        APPLIANCE_ACTION_VARIABLES,
        (value) => this.changeMainActions({ [name]: value }),
      ),
    );
  }

  /** The variants, sorted in the order their expressions are evaluated. */
  private renderVariants(issues: Issue[]) {
    const editable = this.locked || (!this.isNew && !this.hasChanges);
    return html`
      ${this.renderSection("appliance.variants")}
      <div class="info">${this.localize("appliance.variants_info")}</div>
      <ha-sortable handle-selector=".handle" .disabled=${this.locked} @item-moved=${this.variantMoved}>
        <div class="variants">
          ${repeat(
            this.draft.variants,
            (variant) => variant.id,
            (variant) => this.renderVariant(variant, issues, editable),
          )}
        </div>
      </ha-sortable>
      ${this.draft.variants.length > 0 && !editable
        ? html`<div class="hint">${this.localize("appliance.confirm_before_editing_variant")}</div>`
        : nothing}
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

  /** The label of the variant, with what else is wrong or missing in the variant under it. */
  private renderVariant(variant: Variant, issues: Issue[], editable: boolean) {
    const prefix = `variants.${variant.id}.`;
    const variantIssues = issues
      .filter((issue) => issue.field?.startsWith(prefix))
      .map((issue) => ({ ...issue, field: issue.field?.slice(prefix.length) }));
    const otherIssues = variantIssues.filter((issue) => issue.field !== "label");
    return html`
      <div class="variant">
        <div class="variant-row">
          ${this.locked ? nothing : html`<ha-svg-icon class="handle" .path=${mdiDragHorizontalVariant}></ha-svg-icon>`}
          <div class="label">
            ${this.renderForm(
              LABEL_SCHEMA,
              variantIssues,
              (value) => this.changeVariant(variant.id, { label: (value.label as string | undefined) ?? "" }),
              variant,
            )}
          </div>
          <ha-icon-button
            .path=${this.locked ? mdiEye : mdiPencil}
            .label=${this.localize(this.locked ? "list.view" : "list.edit")}
            .disabled=${!editable}
            @click=${() => this.openVariant(variant.id)}
          ></ha-icon-button>
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
        ${otherIssues.map(
          (issue) => html`<div class="error">${this.label(issue.field ?? "")}: ${this.describe(issue)}</div>`,
        )}
      </div>
    `;
  }

  private get hasChanges(): boolean {
    return JSON.stringify(this.draft) !== JSON.stringify(this.item);
  }

  private openVariant(id: string): void {
    this.dispatchEvent(new CustomEvent("variant-opened", { detail: id }));
    this.close();
  }

  private addVariant(): void {
    const variant: Variant = { id: newId(), label: "", condition: { type: "template", value: "" } };
    this.changeDraft({ variants: [...this.draft.variants, variant] });
  }

  private removeVariant(id: string): void {
    const { [id]: _removed, ...actions } = this.draft.actions;
    this.changeDraft({ variants: this.draft.variants.filter((variant) => variant.id !== id), actions });
  }

  private changeMainActions(changes: Partial<ApplianceActions>): void {
    const main = { ...this.draft.actions[MAIN_ACTIONS], ...changes };
    this.changeDraft({ actions: { ...this.draft.actions, [MAIN_ACTIONS]: main } });
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
      .hint {
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
      .error {
        margin-top: 4px;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--error-color);
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
