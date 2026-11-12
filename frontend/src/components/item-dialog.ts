import { LitElement, css, html, nothing, type CSSResultGroup, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import type { ActionConfig, Appliance, Capabilities, Charger, Issue } from "../api";
import { domainActionsFor } from "../domain-actions";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";
import { defaultActionOf, hasDefaultAction, isActionAvailable } from "../validation";
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

  @property({ attribute: false }) saveErrors: Issue[] = [];

  @property({ type: Boolean }) locked = false;

  @state() protected open = true;

  @state() protected draft!: T;

  protected abstract readonly section: "appliances" | "chargers";

  /** The first part of the keys of the dialog's texts. */
  protected abstract readonly texts: "appliance" | "charger";

  /** Return the changes that keep the actions working with a new entity, see `actionForEntity`. */
  protected abstract actionsForEntity(entityId: string | null): Partial<T>;

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

  /** The only entities the item's fields may use, when they are limited. */
  protected get entityScope(): string[] | undefined {
    return undefined;
  }

  protected renderEntity(issues: Issue[]) {
    const schema = [
      {
        name: "entity_id",
        required: true,
        selector: { entity: { include_entities: this.entityScope, exclude_entities: this.usedEntities } },
      },
    ];
    return this.renderForm(schema, issues, (value) => this.entityChanged((value.entity_id as string) || null));
  }

  /** One of the item's own action fields; `entityAllowed` offers to give it as an entity with the same default action. */
  protected renderAction(field: string, issues: Issue[], variables: string[], entityAllowed = false) {
    return this.renderActionField(
      { name: field, field, value: (this.draft as unknown as Record<string, ActionConfig | null>)[field] },
      issues,
      variables,
      (value) => this.changeDraft({ [field]: value } as Partial<T>),
      entityAllowed,
    );
  }

  /**
   * An action field. `name` is the field in the capabilities and the texts,
   * and `field` the field the issues address.
   */
  protected renderActionField(
    action: { name: string; field: string; value: ActionConfig | null },
    issues: Issue[],
    variables: string[],
    changed: (value: ActionConfig | null) => void,
    entityAllowed = false,
  ) {
    const { name, field } = action;
    const issue = issues.find((item) => item.field === field);
    const parameterErrors = errorsByField(issues, `${field}.`, this.describe);
    const defaultAction = defaultActionOf(this.capabilities, this.section, name);
    return html`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .label=${this.label(name)}
        .value=${action.value}
        .entityId=${this.draft.entity_id}
        .defaultAction=${defaultAction}
        .defaultAvailable=${hasDefaultAction(this.capabilities, this.section, name, this.draft.entity_id)}
        .entityDomains=${entityAllowed ? defaultAction.domains : []}
        .includeEntities=${this.entityScope}
        .domainActions=${domainActionsFor(this.capabilities, this.section, name, this.draft.entity_id)}
        .variables=${variables}
        .error=${issue ? this.describe(issue) : undefined}
        .parameterErrors=${parameterErrors}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: ActionConfig | null }>) => changed(event.detail.value)}
      ></kraftvakt-action-field>
    `;
  }

  /**
   * Return the action to use with a new entity: the default action when the
   * entity has one and no action is set, and a custom action when the default
   * or domain action is not available for it.
   */
  protected actionForEntity(name: string, action: ActionConfig | null, entityId: string | null): ActionConfig | null {
    if (action === null && hasDefaultAction(this.capabilities, this.section, name, entityId)) {
      return { mode: "default" };
    }
    if (entityId !== null && !isActionAvailable(this.capabilities, this.section, name, entityId, action)) {
      return { mode: "custom", action: [] };
    }
    return action;
  }

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

  protected numberField(name: string, unit: string, required: boolean): FormField {
    const range = this.capabilities.limits[this.section][name];
    return {
      name,
      required,
      selector: {
        number: {
          min: range.min ?? undefined,
          max: range.max ?? undefined,
          step: range.resolution,
          mode: "box",
          unit_of_measurement: unit,
        },
      },
    };
  }

  protected label(field: string): string {
    return this.localize(`${this.texts}.fields.${field}.label` as TranslationKey);
  }

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

  protected entityChanged(entityId: string | null): void {
    this.changeDraft({ entity_id: entityId, ...this.actionsForEntity(entityId) } as Partial<T>);
  }

  private renderButtons(hasErrors: boolean) {
    if (this.locked) {
      return html`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`;
    }
    return html`
      ${this.isNew
        ? nothing
        : html`<ha-button variant="danger" appearance="plain" @click=${this.delete}>${this.deleteText}</ha-button>`}
      <span class="spacer"></span>
      <ha-button appearance="plain" @click=${this.close}>${this.localize("dialog.cancel")}</ha-button>
      <ha-button .disabled=${hasErrors} @click=${this.confirm}>${this.localize("dialog.ok")}</ha-button>
    `;
  }

  protected get deleteText(): string {
    return this.localize(`${this.texts}.delete`);
  }

  protected get heading(): string {
    if (this.locked) {
      return this.localize(`${this.texts}.view_title`);
    }
    return this.localize(this.isNew ? `${this.texts}.add_title` : `${this.texts}.edit_title`);
  }

  private confirm(): void {
    this.dispatchEvent(new CustomEvent("item-changed", { detail: this.draft }));
    this.close();
  }

  protected delete(): void {
    this.dispatchEvent(new CustomEvent("item-deleted", { detail: this.draft.id }));
    this.close();
  }

  protected close(): void {
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
