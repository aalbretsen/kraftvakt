import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { Condition } from "../api";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/** The domains whose entities are on or off, and so can be boolean entities. */
const BOOLEAN_DOMAINS = ["binary_sensor", "input_boolean", "switch", "schedule"];

const PREVIEW_DELAY_MS = 500;

type ConditionType = Condition["type"] | "none";

interface TemplateResult {
  result?: unknown;
  error?: string;
}

/**
 * A true/false value from a boolean entity or a template, with what
 * it gives now.
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

  /** Whether the condition may be left out, like «car connected». */
  @property({ type: Boolean }) optional = false;

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
    const type: ConditionType = this.value?.type ?? "none";
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

  private schema(type: ConditionType) {
    const types: ConditionType[] = [...(this.optional ? ["none" as const] : []), "entity", "template"];
    const options = types.map((value) => ({ value, label: this.localize(`condition.${value}`) }));
    const valueField =
      type === "entity"
        ? [{ name: "value", required: true, selector: { entity: { filter: { domain: BOOLEAN_DOMAINS } } } }]
        : type === "template"
          ? [{ name: "value", required: true, selector: { template: {} } }]
          : [];
    return [{ name: "type", selector: { select: { mode: "list", options } } }, ...valueField];
  }

  private renderPreview() {
    if (!this.value?.value) {
      return nothing;
    }
    if (this.value.type === "entity") {
      return this.renderNow(this.hass.states[this.value.value]?.state === "on");
    }
    if (this.preview?.error !== undefined) {
      return html`<div class="preview error">${this.localize("condition.error", { message: this.preview.error })}</div>`;
    }
    if (!this.preview) {
      return nothing;
    }
    const result = this.preview.result;
    return html`
      ${this.renderNow(result === true)}
      ${typeof result === "boolean"
        ? nothing
        : html`<div class="warning">${this.localize("condition.not_boolean", { value: JSON.stringify(result) })}</div>`}
    `;
  }

  private renderNow(value: boolean) {
    const text = this.localize(value ? "condition.true" : "condition.false");
    return html`<div class="preview">${this.localize("condition.now", { value: "" })}<b>${text}</b></div>`;
  }

  private computeLabel = (field: { name: string }): string =>
    field.name === "value" ? this.localize(`condition.${this.value?.type ?? "entity"}_label`) : "";

  private computeHelper = (field: { name: string }): string =>
    field.name === "value" ? this.localize(`condition.${this.value?.type ?? "entity"}_helper`) : "";

  private valueChanged(event: CustomEvent<{ value: { type: ConditionType; value?: string } }>): void {
    event.stopPropagation();
    const { type, value } = event.detail.value;
    const sameType = type === this.value?.type;
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
    this.previewTimer = window.setTimeout(() => this.startPreview(template), PREVIEW_DELAY_MS);
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
