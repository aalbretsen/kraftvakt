import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { Condition } from "../api";
import { BOOLEAN_DOMAINS, measuredPowerW, ownEntities } from "../entities";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";

/** The same limit as the backend uses for a power sensor. */
const ACTIVELY_CHARGING_ABOVE_W = 100;

/** What the field gives, also the prefix of its texts. Only evidence counts as true. */
export type ConditionKind = "condition" | "actively_charging";

const TYPES: Record<ConditionKind, Condition["type"][]> = {
  condition: ["entity", "template"],
  actively_charging: ["entity", "power_sensor", "template"],
};

type ConditionType = Condition["type"] | "none";

interface TemplateResult {
  result?: unknown;
  error?: string;
}

/**
 * A true/false value from a boolean entity, a template or a power sensor, with
 * what it gives now, read as the backend reads it.
 *
 * The template is previewed with Home Assistant's `render_template`
 * subscription while the user writes. It gets `entity_id` and `entity`
 * of the appliance or charger, as in the regulation. Fires
 * `value-changed` with the new condition, or `null` when an optional one is
 * not set.
 */
@customElement("kraftvakt-condition-field")
export class KraftvaktConditionField extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ attribute: false }) value: Condition | null = null;

  /** The entity of the appliance or charger the condition belongs to. */
  @property({ attribute: false }) entityId: string | null = null;

  /** The only entities that may be chosen, when they are limited. */
  @property({ attribute: false }) includeEntities?: string[];

  /** Whether the condition may be left out, like «car connected». */
  @property({ type: Boolean }) optional = false;

  @property() kind: ConditionKind = "condition";

  @property() error?: string;

  @property({ type: Boolean }) disabled = false;

  @state() private preview?: TemplateResult;

  private previewTimer?: number;

  private unsubscribePreview?: Promise<() => Promise<void>>;

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.stopPreview();
  }

  protected updated(changed: PropertyValues<this>): void {
    if (changed.has("value") || changed.has("entityId")) {
      this.schedulePreview();
    }
  }

  protected render() {
    const type = this.shownType();
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${{ type, value: this.value?.value ?? "" }}
        .schema=${this.schema(type)}
        .disabled=${this.disabled}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        @value-changed=${this.valueChanged}
      ></ha-form>
      ${this.renderPreview()} ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
    `;
  }

  /** The type shown: a required condition that is not set yet shows its first type. */
  private shownType(): ConditionType {
    return this.value?.type ?? (this.optional ? "none" : TYPES[this.kind][0]);
  }

  private schema(type: ConditionType) {
    const types: ConditionType[] = [...(this.optional ? ["none" as const] : []), ...TYPES[this.kind]];
    const options = types.map((value) => ({ value, label: this.text(value) }));
    return [{ name: "type", selector: { select: { mode: "list", options } } }, ...this.valueField(type)];
  }

  private valueField(type: ConditionType) {
    switch (type) {
      case "entity":
        return [
          {
            name: "value",
            required: true,
            selector: { entity: { filter: { domain: BOOLEAN_DOMAINS }, include_entities: this.includeEntities } },
          },
        ];
      case "power_sensor":
        return [
          {
            name: "value",
            required: true,
            selector: {
              entity: {
                filter: { domain: "sensor", device_class: "power" },
                include_entities: this.includeEntities,
                exclude_entities: ownEntities(this.hass),
              },
            },
          },
        ];
      case "template":
        return [{ name: "value", required: true, selector: { template: {} } }];
      default:
        return [];
    }
  }

  private renderPreview() {
    if (!this.value?.value) {
      return nothing;
    }
    if (this.value.type === "template" && this.preview?.error !== undefined) {
      return html`<div class="preview error">${this.localize("condition.error", { message: this.preview.error })}</div>`;
    }
    if (this.value.type === "template" && !this.preview) {
      return nothing;
    }
    const evidence = this.evidence(this.value);
    return html`
      ${this.renderNow(evidence === true)}
      ${this.value.type === "template" && evidence === null
        ? html`<div class="warning">${this.text("not_boolean", { value: JSON.stringify(this.preview?.result) })}</div>`
        : nothing}
    `;
  }

  /** What the condition shows now, or null when it shows nothing valid. */
  private evidence(condition: Condition): boolean | null {
    switch (condition.type) {
      case "template":
        return typeof this.preview?.result === "boolean" ? this.preview.result : null;
      case "power_sensor": {
        const power = measuredPowerW(this.hass, condition.value);
        return power === null ? null : power > ACTIVELY_CHARGING_ABOVE_W;
      }
      default: {
        const state = this.hass.states[condition.value]?.state;
        return state === "on" ? true : state === "off" ? false : null;
      }
    }
  }

  private renderNow(value: boolean) {
    const text = this.text(value ? "true" : "false");
    return html`<div class="preview">${this.localize("condition.now", { value: "" })}<b>${text}</b></div>`;
  }

  private text(key: string, params?: Record<string, string | number>): string {
    return this.localize(`${this.kind}.${key}` as TranslationKey, params);
  }

  private computeLabel = (field: { name: string }): string =>
    field.name === "value" ? this.text(`${this.shownType()}_label`) : "";

  private computeHelper = (field: { name: string }): string =>
    field.name === "value" ? this.text(`${this.shownType()}_helper`) : "";

  private valueChanged(event: CustomEvent<{ value: { type: ConditionType; value?: string } }>): void {
    event.stopPropagation();
    const { type, value } = event.detail.value;
    const sameType = type === this.shownType();
    const condition: Condition | null = type === "none" ? null : { type, value: sameType ? (value ?? "") : "" };
    this.dispatchEvent(new CustomEvent("value-changed", { detail: { value: condition } }));
  }

  /** Render the template a short while after the user stops writing. */
  private schedulePreview(): void {
    this.stopPreview();
    if (this.value?.type !== "template" || !this.value.value.trim()) {
      this.preview = undefined;
      return;
    }
    const template = this.value.value;
    this.previewTimer = window.setTimeout(() => this.startPreview(template), 500);
  }

  private startPreview(template: string): void {
    const entity = this.entityId ? (this.hass.states[this.entityId] ?? null) : null;
    this.unsubscribePreview = this.hass.connection.subscribeMessage<TemplateResult>(
      (result) => (this.preview = result),
      {
        type: "render_template",
        template,
        variables: { entity_id: this.entityId, entity },
        report_errors: true,
      },
    );
    this.unsubscribePreview.catch((error: unknown) => {
      this.preview = { error: error instanceof Object && "message" in error ? String(error.message) : String(error) };
    });
  }

  private stopPreview(): void {
    window.clearTimeout(this.previewTimer);
    this.unsubscribePreview?.then((unsubscribe) => unsubscribe()).catch(() => undefined);
    this.unsubscribePreview = undefined;
  }

  static styles = css`
    :host {
      display: block;
    }
    .preview {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .error {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--error-color);
    }
    .warning {
      margin-top: 4px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--warning-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-condition-field": KraftvaktConditionField;
  }
}
