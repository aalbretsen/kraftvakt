import { LitElement, css, html, nothing, type CSSResultGroup, type PropertyValues, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import type { ActionConfig, Appliance, Capabilities, Charger, Issue } from "../api";
import { domainActionsFor } from "../domain-actions";
import { templateVariables } from "../entities";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize, TranslationKey } from "../localize";
import { renderDescription, renderSectionHeader, sectionStyles } from "../section-styles";
import type { HomeAssistant } from "../types";
import { defaultActionOf, hasDefaultAction } from "../validation";
import "./action-field";

type Item = Appliance | Charger;

/** A field in the schema of `ha-form`. */
interface FormField {
  name: string;
  schema?: FormField[];
  [option: string]: unknown;
}

/**
 * A group of fields in a dialog: a box with a header, which has the title
 * and an optional control at the right end, the description and the content.
 * Content given as a list is parts, such as two actions, with a line between them,
 * as Home Assistant divides a card. A group with a switch in its header is about
 * something that can be turned on, and shows its content only while it is on.
 */
export interface Group {
  title: string;
  description?: string;
  control?: unknown;
  toggle?: { checked: boolean; changed: (checked: boolean) => void; disabled?: boolean };
  content?: unknown;
  error?: string;
}

function renderContent(content: unknown) {
  if (!Array.isArray(content)) {
    return content ?? nothing;
  }
  return html`<div class="parts">${content.filter((part) => part !== nothing).map((part) => html`<div class="part">${part}</div>`)}</div>`;
}

/**
 * What the dialogs for an appliance and an EV charger have in common: the
 * entity pickers, the actions, the fields with limits, and the buttons.
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

  /** The entity the default and domain actions run for: an appliance's, since an EV charger has none. */
  protected get actionEntity(): string | null {
    return "entity_id" in this.draft ? this.draft.entity_id : null;
  }

  /** The variables the item's templates and actions get. */
  protected get variables(): Record<string, unknown> {
    return templateVariables(this.hass, this.draft);
  }

  /** The entity Kraftvakt turns on and off, which no other appliance or EV charger may use; `domains` limits it to those. */
  protected renderEntityField(field: string, issues: Issue[], changed: (entityId: string | null) => void, domains?: string[]) {
    const schema = [
      {
        name: field,
        required: true,
        selector: { entity: { filter: domains ? { domain: domains } : undefined, include_entities: this.entityScope, exclude_entities: this.usedEntities } },
      },
    ];
    return this.renderForm(schema, issues, (value) => changed((value[field] as string) || null));
  }

  /**
   * One of the item's own action fields; `entityAllowed` offers to give it as
   * an entity with the same default action, and `label` replaces the field's.
   */
  protected renderAction(field: string, issues: Issue[], options: { entityAllowed?: boolean; label?: string; extraVariables?: string[] } = {}) {
    return this.renderActionField(
      { name: field, field, value: (this.draft as unknown as Record<string, ActionConfig | null>)[field], label: options.label },
      issues,
      (value) => this.changeDraft({ [field]: value } as Partial<T>),
      options,
    );
  }

  /** One of the item's own action fields in a group of its own, with the field's label as title and its helper as description. */
  protected renderActionGroup(field: string, issues: Issue[]) {
    return this.renderGroup({
      title: this.label(field),
      description: this.helper(field),
      content: this.renderAction(field, issues, { label: "" }),
    });
  }

  /**
   * An action field. `name` is the field in the capabilities and the texts,
   * and `field` the field the issues address.
   */
  protected renderActionField(
    action: { name: string; field: string; value: ActionConfig | null; label?: string },
    issues: Issue[],
    changed: (value: ActionConfig | null) => void,
    { entityAllowed = false, extraVariables = [] }: { entityAllowed?: boolean; extraVariables?: string[] } = {},
  ) {
    const { name, field } = action;
    const issue = issues.find((item) => item.field === field);
    const parameterErrors = errorsByField(issues, `${field}.`, this.describe);
    const defaultAction = defaultActionOf(this.capabilities, this.section, name);
    const entityId = this.actionEntity;
    return html`
      <kraftvakt-action-field
        .hass=${this.hass}
        .localize=${this.localize}
        .label=${action.label ?? this.label(name)}
        .value=${action.value}
        .entityId=${entityId}
        .defaultAction=${defaultAction}
        .defaultAvailable=${hasDefaultAction(this.capabilities, this.section, name, entityId)}
        .entityDomains=${entityAllowed ? defaultAction.domains : []}
        .includeEntities=${this.entityScope}
        .domainActions=${this.section === "appliances" ? domainActionsFor(this.capabilities, name, entityId) : {}}
        .variables=${[...extraVariables, ...Object.keys(this.variables)]}
        .error=${issue ? this.describe(issue) : undefined}
        .parameterErrors=${parameterErrors}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: ActionConfig | null }>) => changed(event.detail.value)}
      ></kraftvakt-action-field>
    `;
  }

  protected renderForm(schema: FormField[], issues: Issue[], changed: (value: Record<string, unknown>) => void, data: object = this.draft) {
    const fields = schema.flatMap((field) => field.schema?.map((inner) => inner.name) ?? [field.name]);
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
    const number = (value: unknown) => (typeof value === "number" ? new Intl.NumberFormat(this.hass.language).format(value) : "");
    return this.localize(key, { min: number(range?.min), max: number(range?.max), default: number(defaults[field]) });
  }

  protected renderGroup(group: Group) {
    const toggle = group.toggle;
    const control = toggle
      ? html`
          <ha-switch
            .checked=${toggle.checked}
            .disabled=${this.locked || toggle.disabled === true}
            aria-label=${group.title}
            @change=${(event: Event) => toggle.changed((event.target as HTMLInputElement).checked)}
          ></ha-switch>
        `
      : (group.control ?? nothing);
    return html`
      <section class="group ${group.error ? "invalid" : ""}">
        ${renderSectionHeader(group.title, control)} ${renderDescription(group.description)} ${renderContent(group.content)}
        ${group.error ? html`<div class="error">${group.error}</div>` : nothing}
      </section>
    `;
  }

  protected changeDraft(changes: Partial<T>): void {
    this.draft = { ...this.draft, ...changes };
  }

  protected describe = (issue: Issue): string => fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  private renderButtons(hasErrors: boolean) {
    if (this.locked) {
      return html`<ha-button @click=${this.close}>${this.localize("dialog.close")}</ha-button>`;
    }
    return html`
      ${this.isNew ? nothing : html`<ha-button variant="danger" appearance="plain" @click=${this.delete}>${this.deleteText}</ha-button>`}
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

  static styles: CSSResultGroup = [
    sectionStyles,
    css`
      .content {
        display: grid;
        gap: 16px;
      }
      .group {
        display: grid;
        gap: 12px;
        padding: 16px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-card-border-radius, 12px);
      }
      .group.invalid {
        border-color: var(--error-color);
      }
      .parts {
        display: grid;
        gap: 16px;
      }
      /* The line goes from edge to edge of the group, across its padding. */
      .part + .part {
        margin-inline: -16px;
        padding: 16px 16px 0;
        border-top: 1px solid var(--divider-color);
      }
      .error {
        font-size: var(--ha-font-size-s, 12px);
        color: var(--error-color);
      }
      .spacer {
        flex: 1;
      }
      div[slot="footer"] {
        display: flex;
        align-items: center;
      }
    `,
  ];
}
