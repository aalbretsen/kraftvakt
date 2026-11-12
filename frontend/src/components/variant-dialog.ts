import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import { MAIN_ACTIONS, type ActionConfig, type Appliance, type ApplianceActions, type Condition, type Issue, type Variant } from "../api";
import { APPLIANCE_ACTIONS, applianceErrors, isOverridden, missingInAppliance } from "../validation";
import { APPLIANCE_ACTION_VARIABLES } from "./appliance-dialog";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

type ApplianceAction = keyof ApplianceActions;

/**
 * Edits one variant of an appliance: its expression, and whether it
 * overrides the appliance's action to turn on and to turn off.
 *
 * The dialog edits a copy of the appliance and fires `item-changed` with the
 * whole appliance, also when the variant is deleted.
 */
@customElement("kraftvakt-variant-dialog")
export class KraftvaktVariantDialog extends ItemDialog<Appliance> {
  @property() variantId = "";

  @property() applianceName = "";

  protected readonly section = "appliances";

  protected readonly texts = "appliance";

  /** The own actions of overrides switched off, kept while the dialog is open. */
  private setAsideActions = new Map<ApplianceAction, ActionConfig | null>();

  protected actionsForEntity(): Partial<Appliance> {
    return {};
  }

  protected errors(): Issue[] {
    return this.ofVariant(applianceErrors(this.draft, this.capabilities, this.hass.states));
  }

  protected missing(): Issue[] {
    return this.ofVariant(missingInAppliance(this.draft));
  }

  protected get deleteText(): string {
    return this.localize("variant.delete");
  }

  /** Deleting the variant changes the appliance, so it fires `item-changed` without the variant. */
  protected delete(): void {
    const { [this.variantId]: _removed, ...actions } = this.draft.actions;
    const variants = this.draft.variants.filter((variant) => variant.id !== this.variantId);
    this.dispatchEvent(new CustomEvent("item-changed", { detail: { ...this.draft, variants, actions } }));
    this.close();
  }

  protected get heading(): string {
    const name = `${this.applianceName} «${this.variant?.label ?? ""}»`;
    return this.localize(this.locked ? "variant.view_title" : "variant.edit_title", { name });
  }

  protected renderFields(issues: Issue[]) {
    const variant = this.variant;
    if (!variant) {
      return html``;
    }
    const conditionIssue = issues.find((issue) => issue.field === `${this.fieldPrefix}condition`);
    return html`
      ${this.renderSection("variant.condition")}
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${variant.condition}
        .entityId=${this.draft.entity_id}
        .error=${conditionIssue ? this.describe(conditionIssue) : undefined}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: Condition | null }>) =>
          event.detail.value && this.changeCondition(event.detail.value)}
      ></kraftvakt-condition-field>
      ${this.renderSection("appliance.actions")} ${APPLIANCE_ACTIONS.map((name) => this.renderOverride(name, issues))}
    `;
  }

  /** The switch to override the action, and the variant's own action while it is on. */
  private renderOverride(name: ApplianceAction, issues: Issue[]) {
    const own = this.draft.actions[this.variantId];
    const overridden = isOverridden(own, name);
    const switchName = `override_${name}`;
    return html`
      ${this.renderForm(
        [{ name: switchName, selector: { boolean: {} } }],
        [],
        (value) => this.override(name, !!value[switchName]),
        { [switchName]: overridden },
      )}
      ${overridden
        ? this.renderActionField(
            { name, field: `${this.fieldPrefix}${name}`, value: own?.[name] ?? null },
            issues,
            APPLIANCE_ACTION_VARIABLES,
            (value) => this.changeOwnActions({ ...own, [name]: value }),
          )
        : nothing}
    `;
  }

  private get variant(): Variant | undefined {
    return this.draft.variants.find((variant) => variant.id === this.variantId);
  }

  private get fieldPrefix(): string {
    return `variants.${this.variantId}.`;
  }

  private ofVariant(issues: Issue[]): Issue[] {
    return issues.filter((issue) => issue.field?.startsWith(this.fieldPrefix));
  }

  private changeCondition(condition: Condition): void {
    this.changeDraft({
      variants: this.draft.variants.map((variant) => (variant.id === this.variantId ? { ...variant, condition } : variant)),
    });
  }

  /** An overridden action starts from what it had in this dialog, or a copy of the appliance's. */
  private override(name: ApplianceAction, overridden: boolean): void {
    const { [name]: action, ...others } = this.draft.actions[this.variantId] ?? {};
    if (overridden) {
      const start = this.setAsideActions.has(name)
        ? this.setAsideActions.get(name)
        : structuredClone(this.draft.actions[MAIN_ACTIONS]?.[name] ?? null);
      this.changeOwnActions({ ...others, [name]: start ?? null });
    } else {
      this.setAsideActions.set(name, action ?? null);
      this.changeOwnActions(others);
    }
  }

  /** A variant that overrides no action has no entry in the actions. */
  private changeOwnActions(own: Partial<ApplianceActions>): void {
    const { [this.variantId]: _old, ...actions } = this.draft.actions;
    this.changeDraft({ actions: Object.keys(own).length > 0 ? { ...actions, [this.variantId]: own } : actions });
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-variant-dialog": KraftvaktVariantDialog;
  }
}
