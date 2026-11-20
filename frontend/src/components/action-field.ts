import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { ActionConfig, ActionParameter, DefaultAction, DomainAction, ParameterValue } from "../api";
import { initialData, parameterOptions, parameterRange } from "../domain-actions";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";

/**
 * An action as the default action for the entity, a domain action with values
 * from the user, the default action of another entity, or a custom one made
 * with Home Assistant's action editor. With only one way to give it, there is
 * no choice. A temperature of a domain action is a number or a template.
 *
 * Kept in one place, since the action editor may change between versions.
 * Fires `value-changed` with the new action.
 */
@customElement("kraftvakt-action-field")
export class KraftvaktActionField extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property() label = "";

  @property({ attribute: false }) value: ActionConfig | null = null;

  @property({ attribute: false }) entityId: string | null = null;

  /** The default action of the field, from the capabilities. */
  @property({ attribute: false }) defaultAction?: DefaultAction;

  @property({ type: Boolean }) defaultAvailable = false;

  /** The domains of the entities the action may be given as, or none. */
  @property({ attribute: false }) entityDomains: string[] = [];

  /** The only entities the action may be given as, when they are limited. */
  @property({ attribute: false }) includeEntities?: string[];

  /** The domain actions available for the entity, by key. */
  @property({ attribute: false }) domainActions: Record<string, DomainAction> = {};

  /** The error of each parameter of a domain action, by name. */
  @property({ attribute: false }) parameterErrors: Record<string, string> = {};

  @property({ attribute: false }) variables: string[] = [];

  @property() error?: string;

  @property({ type: Boolean }) disabled = false;

  protected render() {
    const mode = this.onlyMode ?? this.value?.mode;
    const domainAction = this.domainAction;
    const shown = this.shownSchema(mode);
    return html`
      <div class="field ${this.error ? "invalid" : ""}">
        ${this.label ? html`<div class="label">${this.label}</div>` : nothing}
        ${this.onlyMode ? nothing : this.renderForm([{ name: "mode", selector: { select: { mode: "list", options: this.modeOptions } } }])}
        ${
          shown.length || domainAction
            ? html`
                <div class=${this.onlyMode ? "" : "shown"}>${shown.length ? this.renderForm(shown) : nothing} ${domainAction ? this.renderParameters(domainAction) : nothing}</div>
              `
            : nothing
        }
        <div class="helper">${this.helperText(mode)}</div>
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
      </div>
    `;
  }

  /** A temperature has a choice of whether it is a number or a template before its value, named `<parameter>_from`. */
  private renderParameters(domainAction: DomainAction) {
    const data = this.value?.data ?? {};
    const choices = Object.fromEntries(domainAction.parameters.filter(isTemperature).map(({ name }) => [`${name}_from`, typeof data[name] === "string" ? "template" : "number"]));
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${{ ...Object.fromEntries(Object.entries(data).map(([name, value]) => [name, value ?? undefined])), ...choices }}
        .schema=${domainAction.parameters.flatMap((parameter) => this.parameterFields(parameter, data[parameter.name] ?? null))}
        .error=${this.parameterErrors}
        .disabled=${this.disabled}
        .computeLabel=${(field: { name: string }) => this.localize(`action.parameters.${field.name}` as TranslationKey)}
        .computeHelper=${(field: { name: string }) => this.parameterHelper(domainAction, field.name, data[field.name] ?? null)}
        @value-changed=${this.parametersChanged}
      ></ha-form>
    `;
  }

  private parameterFields(parameter: ActionParameter, value: ParameterValue): Record<string, unknown>[] {
    const stateObj = this.stateObj;
    if (parameter.type === "option") {
      const options = parameterOptions(parameter, stateObj).map((option) => ({
        value: option,
        label: stateObj ? this.hass.formatEntityState(stateObj, option) : option,
      }));
      return [{ name: parameter.name, required: true, selector: { select: { mode: "dropdown", options } } }];
    }
    const choice = {
      name: `${parameter.name}_from`,
      selector: {
        select: { mode: "list", options: (["number", "template"] as const).map((from) => ({ value: from, label: this.localize(`action.value_from.${from}`) })) },
      },
    };
    if (typeof value === "string") {
      return [choice, { name: parameter.name, required: true, selector: { template: {} } }];
    }
    const { min, max, step } = parameterRange(parameter, stateObj);
    const unit = this.hass.config.unit_system.temperature;
    return [
      choice,
      {
        name: parameter.name,
        required: true,
        selector: { number: { min, max, step: step ?? "any", mode: "box", unit_of_measurement: unit } },
      },
    ];
  }

  /** The variables of a template, or the range of a number, when the entity tells it. */
  private parameterHelper(domainAction: DomainAction, name: string, value: ParameterValue): string {
    if (typeof value === "string" && domainAction.parameters.some((parameter) => parameter.name === name && isTemperature(parameter))) {
      return this.localize("action.variables", { variables: this.variables.join(", ") });
    }
    const parameter = domainAction.parameters.find((item) => item.name === name);
    const { min, max } = parameter ? parameterRange(parameter, this.stateObj) : {};
    if (min === undefined || max === undefined) {
      return "";
    }
    const number = (value: number) => new Intl.NumberFormat(this.hass.language).format(value);
    return this.localize("action.parameter_range", {
      min: number(min),
      max: number(max),
      unit: this.hass.config.unit_system.temperature,
    });
  }

  /** The ways the action may be given: the default, each domain action by its key, an entity, and custom. */
  private get modeOptions(): { value: string; label: string }[] {
    return [
      ...(this.defaultAvailable ? [{ value: "default", label: this.localize("action.default") }] : []),
      ...Object.keys(this.domainActions).map((key) => ({
        value: key,
        label: this.localize(`action.domain_actions.${key}` as TranslationKey),
      })),
      ...(this.entityDomains.length ? [{ value: "entity", label: this.localize("action.entity") }] : []),
      { value: "custom", label: this.localize("action.custom") },
    ];
  }

  /** The only way the action may be given, which needs no choice: custom. */
  private get onlyMode(): "custom" | undefined {
    return this.modeOptions.length === 1 ? "custom" : undefined;
  }

  /** The way the action is given, or what that way shows: the entity or the action editor. */
  private renderForm(schema: Record<string, unknown>[]) {
    const mode = this.onlyMode ?? this.value?.mode;
    return html`
      <ha-form .hass=${this.hass} .data=${this.formData(mode)} .schema=${schema} .disabled=${this.disabled} .computeLabel=${() => ""} @value-changed=${this.valueChanged}></ha-form>
    `;
  }

  private formData(mode: ActionConfig["mode"] | undefined) {
    return {
      mode: mode === "domain" ? this.value?.domain_action : mode,
      action: this.value?.action ?? [],
      entity_id: this.value?.entity_id ?? undefined,
    };
  }

  private shownSchema(mode: ActionConfig["mode"] | undefined): Record<string, unknown>[] {
    return [
      ...(mode === "entity"
        ? [
            {
              name: "entity_id",
              selector: { entity: { filter: { domain: this.entityDomains }, include_entities: this.includeEntities } },
            },
          ]
        : []),
      ...(mode === "custom" ? [{ name: "action", selector: { action: {} } }] : []),
    ];
  }

  private helperText(mode: ActionConfig["mode"] | undefined): string {
    if (mode === "custom") {
      return this.localize("action.variables", { variables: this.variables.join(", ") });
    }
    if (mode === "domain") {
      const domainAction = this.domainAction;
      return domainAction ? this.localize("action.default_runs", { service: `${domainAction.domain}.${domainAction.service}` }) : "";
    }
    if (mode === "entity") {
      const entityId = this.value?.entity_id;
      return entityId ? this.localize("action.entity_runs", { service: this.defaultService(entityId) }) : this.localize("action.choose_action_entity");
    }
    if (this.defaultAvailable && this.entityId) {
      return this.localize("action.default_runs", { service: this.defaultService(this.entityId) });
    }
    return this.localize(this.entityId ? "action.no_default" : "action.choose_entity");
  }

  private valueChanged(event: CustomEvent<{ value: { mode?: string; action?: unknown; entity_id?: string } }>): void {
    event.stopPropagation();
    const { action, entity_id, mode: chosen } = { ...this.formData(this.onlyMode ?? this.value?.mode), ...event.detail.value };
    const mode = this.onlyMode ?? chosen;
    const domainAction = mode ? this.domainActions[mode] : undefined;
    const value: ActionConfig | null = domainAction
      ? {
          mode: "domain",
          domain_action: mode,
          data: initialData(domainAction, this.stateObj, this.value?.data),
        }
      : mode === "default"
        ? { mode }
        : mode === "entity"
          ? { mode, entity_id: entity_id || null }
          : mode === "custom"
            ? { mode, action: this.value?.mode === "custom" || this.onlyMode ? toList(action) : this.defaultSteps() }
            : null;
    this.fireChanged(value);
  }

  /**
   * A value that is cleared becomes null, which counts as not chosen. A temperature that changes
   * between a number and a template starts empty: an empty template, or null.
   */
  private parametersChanged(event: CustomEvent<{ value: Record<string, ParameterValue | undefined> }>): void {
    event.stopPropagation();
    const values = event.detail.value;
    const previous = this.value?.data ?? {};
    const data = Object.fromEntries(
      (this.domainAction?.parameters ?? []).map((parameter) => {
        const { name } = parameter;
        const template = values[`${name}_from`] === "template";
        if (isTemperature(parameter) && template !== (typeof previous[name] === "string")) {
          return [name, template ? "" : null];
        }
        return [name, values[name] ?? (template ? "" : null)];
      }),
    );
    this.fireChanged({ ...this.value!, data });
  }

  private fireChanged(value: ActionConfig | null): void {
    this.dispatchEvent(new CustomEvent("value-changed", { detail: { value } }));
  }

  /** The domain action the value is, when it is available for the entity. */
  private get domainAction(): DomainAction | undefined {
    return this.value?.mode === "domain" && this.value.domain_action ? this.domainActions[this.value.domain_action] : undefined;
  }

  private get stateObj() {
    return this.entityId ? this.hass.states[this.entityId] : undefined;
  }

  /** A custom action starts as the default action, when there is one, for the user to change. */
  private defaultSteps(): Record<string, unknown>[] {
    if (!this.defaultAvailable || !this.entityId) {
      return [];
    }
    const data = this.defaultAction?.data ?? {};
    return [
      {
        action: this.defaultService(this.entityId),
        target: { entity_id: this.entityId },
        ...(Object.keys(data).length ? { data } : {}),
      },
    ];
  }

  private defaultService(entityId: string): string {
    return `${entityId.split(".")[0]}.${this.defaultAction?.service}`;
  }

  static styles = css`
    .label {
      margin-bottom: 8px;
      font-weight: var(--ha-font-weight-medium, 500);
    }
    .invalid .label {
      color: var(--error-color);
    }
    /* What the chosen way shows is divided from the choice by a line from edge to edge of the group, across its padding. */
    .shown {
      display: grid;
      gap: 16px;
      margin: 16px -16px 0;
      padding: 16px 16px 0;
      border-top: 1px solid var(--divider-color);
    }
    /* Indented as Home Assistant indents the helper text of a field. */
    .helper,
    .error {
      padding-inline-start: 16px;
    }
    .helper {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .error {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--error-color);
    }
  `;
}

function isTemperature(parameter: ActionParameter): boolean {
  return parameter.type === "temperature";
}

/** The action editor gives a list of actions, or one action. */
function toList(action: unknown): Record<string, unknown>[] {
  if (Array.isArray(action)) {
    return action as Record<string, unknown>[];
  }
  return action && typeof action === "object" ? [action as Record<string, unknown>] : [];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-action-field": KraftvaktActionField;
  }
}
