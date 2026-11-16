import { LitElement, css, html, nothing, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import type { Condition } from "../api";
import { BOOLEAN_DOMAINS, measuredPowerW, ownEntities } from "../entities";
import { reportedStates, stateEvidence, stateHistory } from "../entity-states";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";

/** The same limit as the backend uses for a power sensor. */
const ACTIVELY_CHARGING_ABOVE_W = 100;

/** What the field gives, also the prefix of its texts. Only evidence counts as true. */
export type ConditionKind = "condition" | "actively_charging" | "charging_power" | "fault";

const TYPES: Record<ConditionKind, Condition["type"][]> = {
  condition: ["entity", "template"],
  actively_charging: ["entity", "template"],
  charging_power: ["power_sensor", "template"],
  fault: ["entity", "template"],
};

interface TemplateResult {
  result?: unknown;
  error?: string;
}

/**
 * A true/false value from a boolean entity, the states of an entity, a template
 * or a power sensor, with what it gives now, read as the backend reads it. A
 * charging power template gives a number in W.
 *
 * The template is previewed with Home Assistant's `render_template`
 * subscription while the user writes. It gets `entity_id` and `entity`
 * of the appliance or charger, as in the regulation. Fires
 * `value-changed` with the new condition.
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

  @property() kind: ConditionKind = "condition";

  @property() error?: string;

  @property({ type: Boolean }) disabled = false;

  /** Whether the field may be left empty. */
  @property({ type: Boolean }) optional = false;

  /** Whether the condition may be states of an entity, as for an EV charger. */
  @property({ type: Boolean }) withState = false;

  /** The states the chosen entity has reported in Home Assistant's history, with the entity they belong to. */
  @state() private history: { entityId: string; states: string[] } = { entityId: "", states: [] };

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
    if (changed.has("value")) {
      this.loadHistory();
    }
  }

  protected render() {
    const type = this.shownType();
    return html`
      <ha-form
        .hass=${this.hass}
        .data=${{ type, value: this.value?.value ?? "", states: this.value?.states ?? [] }}
        .schema=${this.schema(type)}
        .disabled=${this.disabled}
        .computeLabel=${this.computeLabel}
        .computeHelper=${this.computeHelper}
        @value-changed=${this.valueChanged}
      ></ha-form>
      ${this.renderPreview()} ${this.error ? html`<div class="error">${this.error}</div>` : nothing}
    `;
  }

  /** The type shown: a condition that is not set yet shows its first type. */
  private shownType(): Condition["type"] {
    return this.value?.type ?? this.types()[0];
  }

  /** A state comes right after a boolean entity, since both name an entity. */
  private types(): Condition["type"][] {
    const types = TYPES[this.kind];
    return this.withState ? types.flatMap((type) => (type === "entity" ? [type, "state" as const] : [type])) : types;
  }

  private schema(type: Condition["type"]) {
    const options = this.types().map((value) => ({ value, label: this.text(value) }));
    return [{ name: "type", selector: { select: { mode: "list", options } } }, ...this.valueField(type)];
  }

  private valueField(type: Condition["type"]) {
    switch (type) {
      case "entity":
        return [
          {
            name: "value",
            required: !this.optional,
            selector: { entity: { filter: { domain: BOOLEAN_DOMAINS }, include_entities: this.includeEntities } },
          },
        ];
      case "power_sensor":
        return [
          {
            name: "value",
            required: !this.optional,
            selector: {
              entity: {
                filter: { domain: "sensor", device_class: "power" },
                include_entities: this.includeEntities,
                exclude_entities: ownEntities(this.hass),
              },
            },
          },
        ];
      case "state":
        return [
          { name: "value", required: !this.optional, selector: { entity: { include_entities: this.includeEntities } } },
          ...(this.value?.value
            ? [{ name: "states", required: !this.optional, selector: { select: { multiple: true, custom_value: true, options: this.stateOptions() } } }]
            : []),
        ];
      case "template":
        return [{ name: "value", required: !this.optional, selector: { template: {} } }];
    }
  }

  /** Each state the entity reports, named as Home Assistant shows it, with the state itself when that differs. */
  private stateOptions() {
    const entityId = this.value?.value ?? "";
    const stateObj = this.hass.states[entityId];
    const history = this.history.entityId === entityId ? this.history.states : [];
    return reportedStates(stateObj, history, this.value?.states ?? []).map((state) => {
      const shown = stateObj ? this.hass.formatEntityState(stateObj, state) : state;
      return { value: state, label: shown === state ? state : `${shown} (${state})` };
    });
  }

  private loadHistory(): void {
    const entityId = this.value?.type === "state" ? this.value.value : "";
    if (!entityId || this.history.entityId === entityId) {
      return;
    }
    this.history = { entityId, states: [] };
    stateHistory(this.hass, entityId)
      .then((states) => {
        if (this.history.entityId === entityId) {
          this.history = { entityId, states };
        }
      })
      .catch(() => undefined);
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
      ${this.renderNow(this.value, evidence === true)}
      ${this.value.type === "template" && evidence === null
        ? html`<div class="warning">${this.text("invalid", { value: JSON.stringify(this.preview?.result) })}</div>`
        : nothing}
    `;
  }

  /** What the condition shows now, or null when it shows nothing valid. */
  private evidence(condition: Condition): boolean | null {
    switch (condition.type) {
      case "template":
        if (this.kind === "charging_power") {
          const power = templatePowerW(this.preview?.result);
          return power === null ? null : power > ACTIVELY_CHARGING_ABOVE_W;
        }
        return typeof this.preview?.result === "boolean" ? this.preview.result : null;
      case "power_sensor": {
        const power = measuredPowerW(this.hass, condition.value);
        return power === null ? null : power > ACTIVELY_CHARGING_ABOVE_W;
      }
      case "state":
        return stateEvidence(this.hass.states[condition.value]?.state, condition.states ?? []);
      default: {
        const state = this.hass.states[condition.value]?.state;
        return state === "on" ? true : state === "off" ? false : null;
      }
    }
  }

  /**
   * An entity's state is shown as Home Assistant formats it, before what it
   * counts as. On and off count as just that, so they are shown alone.
   */
  private renderNow(condition: Condition, value: boolean) {
    const text = this.text(value ? "true" : "false");
    const stateObj = condition.type === "template" ? undefined : this.hass.states[condition.value];
    const onOrOff = condition.type === "entity" && (stateObj?.state === "on" || stateObj?.state === "off");
    const templatePower = condition.type === "template" && this.kind === "charging_power" ? templatePowerW(this.preview?.result) : null;
    return html`
      <div class="preview">
        ${this.localize("condition.now", { value: "" })}${stateObj
          ? html`<b>${this.hass.formatEntityState(stateObj)}</b>${onOrOff ? nothing : html` · ${text}`}`
          : templatePower !== null
            ? html`<b>${new Intl.NumberFormat(this.hass.language).format(templatePower)} W</b> · ${text}`
            : html`<b>${text}</b>`}
      </div>
    `;
  }

  private text(key: string, params?: Record<string, string | number>): string {
    return this.localize(`${this.kind}.${key}` as TranslationKey, params);
  }

  /** A text the kind may leave out, empty when it does. */
  private optionalText(key: string): string {
    const text = this.text(key);
    return text === `${this.kind}.${key}` ? "" : text;
  }

  private computeLabel = (field: { name: string }): string => {
    switch (field.name) {
      case "value":
        return this.text(`${this.shownType()}_label`);
      case "states":
        return this.text("states_label");
      default:
        return this.optionalText("type_label");
    }
  };

  private computeHelper = (field: { name: string }): string => {
    switch (field.name) {
      case "value":
        return this.text(`${this.shownType()}_helper`);
      case "states":
        return this.text("states_helper");
      default:
        return "";
    }
  };

  /** Another type starts empty, and another entity starts without chosen states. */
  private valueChanged(event: CustomEvent<{ value: { type: Condition["type"]; value?: string; states?: string[] } }>): void {
    event.stopPropagation();
    const { type, value, states } = event.detail.value;
    const sameType = type === this.shownType();
    const condition: Condition = { type, value: sameType ? (value ?? "") : "" };
    if (type === "state") {
      condition.states = sameType && condition.value === this.value?.value ? (states ?? []) : [];
    }
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
    /* Indented as Home Assistant indents the helper text of a field. */
    .preview,
    .error,
    .warning {
      padding-inline-start: 16px;
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

/** A template's result read as power in W, as the backend reads it: a number, or null. */
function templatePowerW(result: unknown): number | null {
  const power = typeof result === "string" && result.trim() !== "" ? Number(result) : result;
  return typeof power === "number" && Number.isFinite(power) ? Math.max(power, 0) : null;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-condition-field": KraftvaktConditionField;
  }
}
