import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { ActionConfig, ActionParameter, DefaultAction, DomainAction, ParameterValue } from "../api";
import { initialData, parameterOptions, parameterRange } from "../domain-actions";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";

/**
 * An action as the default action for the entity, a domain action with values
 * from the user, the default action of another entity, or a custom one made
 * with Home Assistant's action editor.
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

  /** The variables the action gets. */
  @property({ attribute: false }) variables: string[] = [];

  @property() error?: string;

  @property({ type: Boolean }) disabled = false;

  protected render() {
    const mode = this.value?.mode;
    const domainAction = this.domainAction;
    return html`
      <div class="field ${this.error ? "invalid" : ""}">
        <div class="label">${this.label}</div>
        <ha-form
          .hass=${this.hass}
          .data=${{
            mode: mode === "domain" ? this.value?.domain_action : mode,
            action: this.value?.action ?? [],
            entity_id: this.value?.entity_id ?? undefined,
          }}
          .schema=${this.schema(mode)}
          .disabled=${this.disabled}
          .computeLabel=${() => ""}
          @value-changed=${this.valueChanged}
        ></ha-form>
        ${domainAction ? this.renderParameters(domainAction) : nothing}
        <div class="helper">${this.helperText(mode)}</div>
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
      </div>
    `;
  }

  private renderParameters(domainAction: DomainAction) {
    const data = this.value?.data ?? {};
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${Object.fromEntries(Object.entries(data).map(([name, value]) => [name, value ?? undefined]))}
        .schema=${domainAction.parameters.map((parameter) => this.parameterField(parameter))}
        .error=${this.parameterErrors}
        .disabled=${this.disabled}
        .computeLabel=${(field: { name: string }) =>
          this.localize(`action.parameters.${field.name}` as TranslationKey)}
        .computeHelper=${(field: { name: string }) => this.parameterHelper(domainAction, field.name)}
        @value-changed=${this.parametersChanged}
      ></ha-form>
    `;
  }

  private parameterField(parameter: ActionParameter) {
    const stateObj = this.stateObj;
    if (parameter.type === "option") {
      const options = parameterOptions(parameter, stateObj).map((option) => ({
        value: option,
        label: stateObj ? this.hass.formatEntityState(stateObj, option) : option,
      }));
      return { name: parameter.name, required: true, selector: { select: { mode: "dropdown", options } } };
    }
    const { min, max, step } = parameterRange(parameter, stateObj);
    const unit = this.hass.config.unit_system.temperature;
    return {
      name: parameter.name,
      required: true,
      selector: { number: { min, max, step: step ?? "any", mode: "box", unit_of_measurement: unit } },
    };
  }

  /** The range of a value, when the entity tells it. */
  private parameterHelper(domainAction: DomainAction, name: string): string {
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

  private schema(mode: ActionConfig["mode"] | undefined) {
    const options = [
      ...(this.defaultAvailable ? [{ value: "default", label: this.localize("action.default") }] : []),
      ...Object.keys(this.domainActions).map((key) => ({
        value: key,
        label: this.localize(`action.domain_actions.${key}` as TranslationKey),
      })),
      ...(this.entityDomains.length ? [{ value: "entity", label: this.localize("action.entity") }] : []),
      { value: "custom", label: this.localize("action.custom") },
    ];
    return [
      { name: "mode", selector: { select: { mode: "list", options } } },
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
      return domainAction
        ? this.localize("action.default_runs", { service: `${domainAction.domain}.${domainAction.service}` })
        : "";
    }
    if (mode === "entity") {
      const entityId = this.value?.entity_id;
      return entityId
        ? this.localize("action.entity_runs", { service: this.defaultService(entityId) })
        : this.localize("action.choose_action_entity");
    }
    if (this.defaultAvailable && this.entityId) {
      return this.localize("action.default_runs", { service: this.defaultService(this.entityId) });
    }
    return this.localize(this.entityId ? "action.no_default" : "action.choose_entity");
  }

  private valueChanged(event: CustomEvent<{ value: { mode?: string; action?: unknown; entity_id?: string } }>): void {
    event.stopPropagation();
    const { mode, action, entity_id } = event.detail.value;
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
            ? { mode, action: this.value?.mode === "custom" ? toList(action) : this.defaultSteps() }
            : null;
    this.fireChanged(value);
  }

  /** A value that is cleared becomes null, which counts as not chosen. */
  private parametersChanged(event: CustomEvent<{ value: Record<string, ParameterValue | undefined> }>): void {
    event.stopPropagation();
    const data = Object.fromEntries(
      (this.domainAction?.parameters ?? []).map(({ name }) => [name, event.detail.value[name] ?? null]),
    );
    this.fireChanged({ ...this.value!, data });
  }

  private fireChanged(value: ActionConfig | null): void {
    this.dispatchEvent(new CustomEvent("value-changed", { detail: { value } }));
  }

  /** The domain action the value is, when it is available for the entity. */
  private get domainAction(): DomainAction | undefined {
    return this.value?.mode === "domain" && this.value.domain_action
      ? this.domainActions[this.value.domain_action]
      : undefined;
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
    .field {
      padding: 12px;
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md, 8px);
    }
    .field.invalid {
      border-color: var(--error-color);
    }
    .label {
      font-weight: 500;
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
