import { mdiDelete, mdiDragHorizontalVariant, mdiPlus } from "@mdi/js";
import { css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import { MAIN_ACTIONS, type Appliance, type ApplianceActions, type Condition, type Issue, type Variant } from "../api";
import { moveItem, newId } from "../draft";
import { APPLIANCE_ACTIONS, applianceErrors, missingInAppliance } from "../validation";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

const ACTION_VARIABLES = ["entity_id", "entity"];

/** Adds or edits one appliance. */
@customElement("kraftvakt-appliance-dialog")
export class KraftvaktApplianceDialog extends ItemDialog<Appliance> {
  protected readonly section = "appliances";

  protected readonly texts = "appliance";

  /** The own actions of variants switched to the appliance's, kept while the dialog is open. */
  private setAsideActions = new Map<string, ApplianceActions>();

  protected actionsForEntity(entityId: string | null): Partial<Appliance> {
    const actions = Object.fromEntries(
      Object.entries(this.draft.actions).map(([key, own]) => [
        key,
        {
          turn_on: this.actionForEntity("turn_on", own.turn_on, entityId),
          turn_off: this.actionForEntity("turn_off", own.turn_off, entityId),
        },
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
      ${this.renderEntity(issues)} ${this.renderSection("appliance.actions")}
      ${this.renderActions(MAIN_ACTIONS, "", issues)}
      ${this.renderForm([this.numberField("power_reserve_w", "W", false)], issues, (value) =>
        this.changeDraft({ power_reserve_w: (value.power_reserve_w as number | undefined) ?? null }),
      )}
      ${this.renderVariants(issues)}
    `;
  }

  /** The actions under `key` in the actions of the appliance; `prefix` is the start of their issue fields. */
  private renderActions(key: string, prefix: string, issues: Issue[]) {
    const actions = this.draft.actions[key];
    return APPLIANCE_ACTIONS.map((name) =>
      this.renderActionField(
        { name, field: `${prefix}${name}`, value: actions?.[name] ?? null },
        issues,
        ACTION_VARIABLES,
        (value) => this.changeActions(key, { [name]: value }),
      ),
    );
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
    const ownActions = this.draft.actions[variant.id] !== undefined;
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
        ${this.renderForm(USE_MAIN_ACTIONS_SCHEMA, [], (value) => this.useMainActions(variant.id, !!value.use_main_actions), {
          use_main_actions: !ownActions,
        })}
        ${ownActions ? this.renderActions(variant.id, prefix, issues) : nothing}
      </div>
    `;
  }

  private addVariant(): void {
    const variant: Variant = { id: newId(), label: "", condition: { type: "template", value: "" } };
    this.changeDraft({ variants: [...this.draft.variants, variant] });
  }

  private removeVariant(id: string): void {
    const { [id]: _removed, ...actions } = this.draft.actions;
    this.changeDraft({ variants: this.draft.variants.filter((variant) => variant.id !== id), actions });
  }

  private changeActions(key: string, changes: Partial<ApplianceActions>): void {
    this.changeDraft({ actions: { ...this.draft.actions, [key]: { ...this.draft.actions[key], ...changes } } });
  }

  /** A variant gets its own actions from those it had in this dialog, or a copy of the appliance's. */
  private useMainActions(id: string, useMain: boolean): void {
    const { [id]: own, ...others } = this.draft.actions;
    if (useMain) {
      if (own) {
        this.setAsideActions.set(id, own);
      }
      this.changeDraft({ actions: others });
    } else {
      const actions = this.setAsideActions.get(id) ?? structuredClone(this.draft.actions[MAIN_ACTIONS]);
      this.changeDraft({ actions: { ...this.draft.actions, [id]: actions } });
    }
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
const USE_MAIN_ACTIONS_SCHEMA = [{ name: "use_main_actions", selector: { boolean: {} } }];

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-appliance-dialog": KraftvaktApplianceDialog;
  }
}
