import { LitElement, css, html, nothing, type CSSResultGroup, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import type { ActionConfig, Appliance, Capabilities, Charger, Issue } from "../api";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";
import { hasDefaultAction } from "../validation";
import "./action-field";

type Item = Appliance | Charger;

/** A field in the schema of `ha-form`. */
interface FormField {
  name: string;
  [option: string]: unknown;
}

/**
 * What the dialogs for an appliance and an EV charger have in common: the
 * entity, the actions, the fields with limits, and the buttons.
 *
 * The dialog edits a copy of the item. «OK» fires `item-changed` with the
 * item, and «Delete» fires `item-deleted` with its id. Both only change the
 * draft. `closed` is fired when the dialog has closed. While the
 * configuration is locked, the dialog only shows the item.
 */
export abstract class ItemDialog<T extends Item> extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ attribute: false }) capabilities!: Capabilities;

  @property({ attribute: false }) item!: T;

  @property({ type: Boolean }) isNew = false;

  /** The entities of the other appliances and chargers, which cannot be chosen. */
  @property({ attribute: false }) usedEntities: string[] = [];

  /** The errors the backend gave for the item when the draft was last saved. */
  @property({ attribute: false }) saveErrors: Issue[] = [];

  @property({ type: Boolean }) locked = false;

  @state() protected open = true;

  @state() protected draft!: T;

  protected abstract readonly section: "appliances" | "chargers";

  /** The first part of the keys of the dialog's texts. */
  protected abstract readonly texts: "appliance" | "charger";

  protected abstract readonly actionFields: readonly string[];

  /** The mistakes in the item that stop the dialog from being confirmed. */
  protected abstract errors(): Issue[];

  /** What is missing in the item before the regulation can start. */
  protected abstract missing(): Issue[];

  protected abstract renderFields(issues: Issue[]): TemplateResult;

  protected willUpdate(changed: PropertyValues<this>): void {
    if (changed.has("item")) {
      this.draft = structuredClone(this.item);
    }
  }

  /** A new item is not marked as incomplete before it is added. */
  protected render() {
    const errors = this.errors();
    const issues = [...errors, ...(this.isNew ? [] : this.missing()), ...this.saveErrors];
    return html`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} prevent-scrim-close @closed=${this.closed}>
        <div class="content">${this.renderFields(issues)}</div>
        <div slot="footer">${this.renderButtons(errors.length > 0)}</div>
      </ha-dialog>
    `;
  }

  /** The entity of the item, which gives it its name. */
  protected renderEntity(issues: Issue[]) {
    const schema = [{ name: "entity_id", required: true, selector: { entity: { exclude_entities: this.usedEntities } } }];
    return this.renderForm(schema, issues, (value) => this.entityChanged((value.entity_id as string) || null));
  }

  protected renderAction(field: string, issues: Issue[], variables: string[]) {
    const issue = issues.find((item) => item.field === field);
    return html`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .field=${field}
        .label=${this.label(field)}
        .value=${(this.draft as unknown as Record<string, ActionConfig | null>)[field]}
        .entityId=${this.draft.entity_id}
        .defaultAvailable=${hasDefaultAction(this.capabilities, this.section, field, this.draft.entity_id)}
        .variables=${variables}
        .error=${issue ? this.describe(issue) : undefined}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: ActionConfig | null }>) =>
          this.changeDraft({ [field]: event.detail.value } as Partial<T>)}
      ></kraftvakt-action-field>
    `;
  }

  /** An `ha-form` for fields of the item, whose changes are given to `changed`. */
  protected renderForm(
    schema: FormField[],
    issues: Issue[],
    changed: (value: Record<string, unknown>) => void,
    data: object = this.draft,
  ) {
    const fields = schema.map((field) => field.name);
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${data}
        .schema=${schema}
        .error=${errorsByField(
          issues.filter((issue) => issue.field !== undefined && fields.includes(issue.field)),
          "",
          this.describe,
        )}
        .disabled=${this.locked}
        .computeLabel=${(field: { name: string }) => this.label(field.name)}
        .computeHelper=${(field: { name: string }) => this.helper(field.name)}
        @value-changed=${(event: CustomEvent<{ value: Record<string, unknown> }>) => {
          event.stopPropagation();
          changed(event.detail.value);
        }}
      ></ha-form>
    `;
  }

  /** A number field with the limits from `kraftvakt/capabilities`. */
  protected numberField(name: string, unit: string, required: boolean): FormField {
    const range = this.capabilities.limits[this.section][name];
    return {
      name,
      required,
      selector: {
        number: {
          min: range.min ?? undefined,
          max: range.max ?? undefined,
          step: range.step,
          mode: "box",
          unit_of_measurement: unit,
        },
      },
    };
  }

  protected label(field: string): string {
    return this.localize(`${this.texts}.fields.${field}.label` as TranslationKey);
  }

  /** The help text of the field, with the limits and the default of the field, if it has one. */
  protected helper(field: string): string {
    const key = `${this.texts}.fields.${field}.helper` as TranslationKey;
    const text = this.localize(key);
    if (text === key) {
      return "";
    }
    const range = this.capabilities.limits[this.section][field];
    const defaults = this.capabilities.defaults[this.section] as Record<string, unknown>;
    const number = (value: unknown) =>
      typeof value === "number" ? new Intl.NumberFormat(this.hass.language).format(value) : "";
    return this.localize(key, { min: number(range?.min), max: number(range?.max), default: number(defaults[field]) });
  }

  protected renderSection(title: TranslationKey) {
    return html`<div class="section">${this.localize(title)}</div>`;
  }

  protected changeDraft(changes: Partial<T>): void {
    this.draft = { ...this.draft, ...changes };
  }

  protected describe = (issue: Issue): string =>
    fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  /**
   * Choose the default action when the new entity has one and no action is set,
   * and a custom action when the default is no longer available.
   */
  private entityChanged(entityId: string | null): void {
    const actions = this.draft as unknown as Record<string, ActionConfig | null>;
    const changes: Record<string, unknown> = { entity_id: entityId };
    for (const field of this.actionFields) {
      const available = hasDefaultAction(this.capabilities, this.section, field, entityId);
      if (available && actions[field] === null) {
        changes[field] = { mode: "default" };
      } else if (!available && actions[field]?.mode === "default" && entityId !== null) {
        changes[field] = { mode: "custom", action: [] };
      }
    }
    this.changeDraft(changes as Partial<T>);
  }

  private renderButtons(hasErrors: boolean) {
    if (this.locked) {
      return html`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`;
    }
    return html`
      ${this.isNew
        ? nothing
        : html`<ha-button variant="danger" appearance="plain" @click=${this.delete}>
            ${this.localize(`${this.texts}.delete`)}
          </ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${hasErrors} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `;
  }

  private get heading(): string {
    if (this.locked) {
      return this.localize(`${this.texts}.view_title`);
    }
    return this.localize(this.isNew ? `${this.texts}.add_title` : `${this.texts}.edit_title`);
  }

  private confirm(): void {
    this.dispatchEvent(new CustomEvent("item-changed", { detail: this.draft }));
    this.close();
  }

  private delete(): void {
    this.dispatchEvent(new CustomEvent("item-deleted", { detail: this.draft.id }));
    this.close();
  }

  private close(): void {
    this.open = false;
  }

  private closed(event: Event): void {
    event.stopPropagation();
    this.dispatchEvent(new CustomEvent("closed"));
  }

  static styles: CSSResultGroup = css`
    .content {
      display: grid;
      gap: 16px;
    }
    .section {
      margin-top: 8px;
      font-size: var(--ha-font-size-l, 16px);
      font-weight: 500;
    }
    .info {
      margin-top: -8px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
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
