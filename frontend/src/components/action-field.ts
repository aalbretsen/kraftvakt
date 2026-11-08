import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { ActionConfig } from "../api";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/** The service of the default action for each field. */
const DEFAULT_SERVICES: Record<string, string> = {
  turn_on: "turn_on",
  turn_off: "turn_off",
  activate: "turn_on",
  deactivate: "turn_off",
  set_current: "set_value",
};

/**
 * An action as the default action for the entity or a custom one.
 *
 * «Standard» is offered only when the domain of the entity has a default action
 *. The custom action uses Home Assistant's action editor. Kept in one
 * place, since the action editor may change between versions.
 * Fires `value-changed` with the new action.
 */
@customElement("kraftvakt-action-field")
export class KraftvaktActionField extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  /** The name of the field in the configuration, like `turn_on`. */
  @property() field = "";

  @property() label = "";

  @property({ attribute: false }) value: ActionConfig | null = null;

  @property({ attribute: false }) entityId: string | null = null;

  @property({ type: Boolean }) defaultAvailable = false;

  /** The variables the action gets. */
  @property({ attribute: false }) variables: string[] = [];

  @property() error?: string;

  @property({ type: Boolean }) disabled = false;

  protected render() {
    const mode = this.value?.mode;
    return html`
      <div class="field ${this.error ? "invalid" : ""}">
        <div class="label">${this.label}</div>
        <ha-form
          .hass=${this.hass}
          .data=${{ mode, action: this.value?.action ?? [] }}
          .schema=${this.schema(mode)}
          .disabled=${this.disabled}
          .computeLabel=${() => ""}
          @value-changed=${this.valueChanged}
        ></ha-form>
        <div class="helper">${this.helperText(mode)}</div>
        ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
      </div>
    `;
  }

  private schema(mode: ActionConfig["mode"] | undefined) {
    const options = [
      ...(this.defaultAvailable ? [{ value: "default", label: this.localize("action.default") }] : []),
      { value: "custom", label: this.localize("action.custom") },
    ];
    return [
      { name: "mode", selector: { select: { mode: "list", options } } },
      ...(mode === "custom" ? [{ name: "action", selector: { action: {} } }] : []),
    ];
  }

  private helperText(mode: ActionConfig["mode"] | undefined): string {
    if (mode === "custom") {
      return this.localize("action.variables", { variables: this.variables.join(", ") });
    }
    if (this.defaultAvailable && this.entityId) {
      return this.localize("action.default_runs", { service: this.defaultService(this.entityId) });
    }
    return this.localize(this.entityId ? "action.no_default" : "action.choose_entity");
  }

  private valueChanged(event: CustomEvent<{ value: { mode?: ActionConfig["mode"]; action?: unknown } }>): void {
    event.stopPropagation();
    const { mode, action } = event.detail.value;
    const value: ActionConfig | null =
      mode === "default"
        ? { mode }
        : mode === "custom"
          ? { mode, action: this.value?.mode === "custom" ? toList(action) : this.defaultSteps() }
          : null;
    this.dispatchEvent(new CustomEvent("value-changed", { detail: { value } }));
  }

  /** A custom action starts as the default action, when there is one, for the user to change. */
  private defaultSteps(): Record<string, unknown>[] {
    if (!this.defaultAvailable || !this.entityId) {
      return [];
    }
    const data = this.field === "set_current" ? { data: { value: "{{ current }}" } } : {};
    return [{ action: this.defaultService(this.entityId), target: { entity_id: this.entityId }, ...data }];
  }

  private defaultService(entityId: string): string {
    return `${entityId.split(".")[0]}.${DEFAULT_SERVICES[this.field]}`;
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
