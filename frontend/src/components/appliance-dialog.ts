import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { ActionConfig, Appliance, Capabilities, Issue } from "../api";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";
import { applianceErrors, hasDefaultAction, missingInAppliance } from "../validation";
import "./action-field";

const ACTION_FIELDS = ["turn_on", "turn_off"] as const;
const ACTION_VARIABLES = ["entity_id", "entity"];

/**
 * Adds or edits one appliance: its entity, its actions, and its power reserve
 * (APP-002 to APP-004, GEN-013).
 *
 * «OK» fires `appliance-changed` with the appliance, and «Delete» fires
 * `appliance-deleted`. Both only change the draft (B7). `closed` is fired when
 * the dialog has closed. While the configuration is locked, the dialog only
 * shows the appliance (GUI-012).
 */
@customElement("kraftvakt-appliance-dialog")
export class KraftvaktApplianceDialog extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ attribute: false }) capabilities!: Capabilities;

  @property({ attribute: false }) appliance!: Appliance;

  @property({ type: Boolean }) isNew = false;

  /** The entities of the other appliances and chargers, which cannot be chosen (T9). */
  @property({ attribute: false }) usedEntities: string[] = [];

  /** The errors the backend gave for the appliance when the draft was last saved. */
  @property({ attribute: false }) saveErrors: Issue[] = [];

  @property({ type: Boolean }) locked = false;

  @state() private open = true;

  @state() private draft!: Appliance;

  protected willUpdate(changed: PropertyValues<this>): void {
    if (changed.has("appliance")) {
      this.draft = structuredClone(this.appliance);
    }
  }

  protected render() {
    const errors = applianceErrors(this.draft, this.capabilities);
    const missing = this.isNew ? [] : missingInAppliance(this.draft);
    const issues = [...errors, ...missing, ...this.saveErrors];
    return html`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} prevent-scrim-close @closed=${this.closed}>
        <div class="content">
          <ha-form
            .hass=${this.hass}
            .data=${this.draft}
            .schema=${this.entitySchema}
            .error=${this.formErrors(issues, "entity_id")}
            .disabled=${this.locked}
            .computeLabel=${this.computeLabel}
            .computeHelper=${this.computeHelper}
            @value-changed=${this.entityChanged}
          ></ha-form>
          <div class="section">${this.localize("appliance.actions")}</div>
          ${ACTION_FIELDS.map((field) => this.renderAction(field, issues))}
          <ha-form
            .hass=${this.hass}
            .data=${this.draft}
            .schema=${this.reserveSchema}
            .error=${this.formErrors(issues, "power_reserve_kw")}
            .disabled=${this.locked}
            .computeLabel=${this.computeLabel}
            .computeHelper=${this.computeHelper}
            @value-changed=${this.reserveChanged}
          ></ha-form>
        </div>
        <div slot="footer">${this.renderButtons(errors.length > 0)}</div>
      </ha-dialog>
    `;
  }

  private renderAction(field: (typeof ACTION_FIELDS)[number], issues: Issue[]) {
    const issue = issues.find((item) => item.field === field);
    return html`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .field=${field}
        .label=${this.localize(`appliance.fields.${field}.label`)}
        .value=${this.draft[field]}
        .entityId=${this.draft.entity_id}
        .defaultAvailable=${hasDefaultAction(this.capabilities, "appliances", field, this.draft.entity_id)}
        .variables=${ACTION_VARIABLES}
        .error=${issue ? this.describe(issue) : undefined}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: ActionConfig | null }>) =>
          this.changeDraft({ [field]: event.detail.value })}
      ></kraftvakt-action-field>
    `;
  }

  private renderButtons(hasErrors: boolean) {
    if (this.locked) {
      return html`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`;
    }
    return html`
      ${this.isNew
        ? nothing
        : html`<ha-button variant="danger" appearance="plain" @click=${this.delete}>
            ${this.localize("appliance.delete")}
          </ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${hasErrors} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `;
  }

  private get heading(): string {
    if (this.locked) {
      return this.localize("appliance.view_title");
    }
    return this.localize(this.isNew ? "appliance.add_title" : "appliance.edit_title");
  }

  private get entitySchema() {
    return [{ name: "entity_id", required: true, selector: { entity: { exclude_entities: this.usedEntities } } }];
  }

  private get reserveSchema() {
    const range = this.capabilities.limits.appliances.power_reserve_kw;
    return [
      {
        name: "power_reserve_kw",
        selector: {
          number: {
            min: range.min ?? undefined,
            max: range.max ?? undefined,
            step: range.step,
            mode: "box",
            unit_of_measurement: "kW",
          },
        },
      },
    ];
  }

  /**
   * Choose the default action when the new entity has one and no action is set,
   * and a custom action when the default is no longer available (GEN-013).
   */
  private entityChanged(event: CustomEvent<{ value: { entity_id?: string } }>): void {
    const entityId = event.detail.value.entity_id || null;
    const changes: Partial<Appliance> = { entity_id: entityId };
    for (const field of ACTION_FIELDS) {
      const available = hasDefaultAction(this.capabilities, "appliances", field, entityId);
      const action = this.draft[field];
      if (available && action === null) {
        changes[field] = { mode: "default" };
      } else if (!available && action?.mode === "default" && entityId !== null) {
        changes[field] = { mode: "custom", action: [] };
      }
    }
    this.changeDraft(changes);
  }

  private reserveChanged(event: CustomEvent<{ value: { power_reserve_kw?: number } }>): void {
    this.changeDraft({ power_reserve_kw: event.detail.value.power_reserve_kw ?? null });
  }

  private changeDraft(changes: Partial<Appliance>): void {
    this.draft = { ...this.draft, ...changes };
  }

  private confirm(): void {
    this.dispatchEvent(new CustomEvent("appliance-changed", { detail: this.draft }));
    this.close();
  }

  private delete(): void {
    this.dispatchEvent(new CustomEvent("appliance-deleted", { detail: this.draft.id }));
    this.close();
  }

  private close(): void {
    this.open = false;
  }

  private closed(): void {
    this.dispatchEvent(new CustomEvent("closed"));
  }

  /** The error text for `ha-form` of the field, with the prefix left out of its name. */
  private formErrors(issues: Issue[], field: string, prefix = ""): Record<string, string> {
    return errorsByField(
      issues.filter((issue) => issue.field === field),
      prefix,
      this.describe,
    );
  }

  private describe = (issue: Issue): string =>
    fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  private computeLabel = (field: { name: string }): string =>
    this.localize(`appliance.fields.${field.name as "entity_id" | "power_reserve_kw"}.label`);

  private computeHelper = (field: { name: string }): string =>
    field.name === "entity_id" || field.name === "power_reserve_kw"
      ? this.localize(`appliance.fields.${field.name}.helper`)
      : "";

  static styles = css`
    .content {
      display: grid;
      gap: 16px;
    }
    .section {
      margin-top: 8px;
      font-size: var(--ha-font-size-l, 16px);
      font-weight: 500;
    }
    .spacer {
      flex: 1;
    }
    div[slot="footer"] {
      display: flex;
      align-items: center;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-appliance-dialog": KraftvaktApplianceDialog;
  }
}
