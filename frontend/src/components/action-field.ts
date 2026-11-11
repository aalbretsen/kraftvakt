import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { ActionConfig, DefaultAction } from "../api";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/**
 * An action as the default action for the entity, the default action of another
 * entity, or a custom one made with Home Assistant's action editor.
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
          .data=${{ mode, action: this.value?.action ?? [], entity_id: this.value?.entity_id ?? undefined }}
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
      ...(this.entityDomains.length ? [{ value: "entity", label: this.localize("action.entity") }] : []),
      { value: "custom", label: this.localize("action.custom") },
    ];
    return [
      { name: "mode", selector: { select: { mode: "list", options } } },
      ...(mode === "entity" ? [{ name: "entity_id", selector: { entity: { filter: { domain: this.entityDomains } } } }] : []),
      ...(mode === "custom" ? [{ name: "action", selector: { action: {} } }] : []),
    ];
  }

  private helperText(mode: ActionConfig["mode"] | undefined): string {
    if (mode === "custom") {
      return this.localize("action.variables", { variables: this.variables.join(", ") });
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

  private valueChanged(
    event: CustomEvent<{ value: { mode?: ActionConfig["mode"]; action?: unknown; entity_id?: string } }>,
  ): void {
    event.stopPropagation();
    const { mode, action, entity_id } = event.detail.value;
    const value: ActionConfig | null =
      mode === "default"
        ? { mode }
        : mode === "entity"
          ? { mode, entity_id: entity_id || null }
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
