import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { OVERRIDE_ENDS, type Charger, type Condition, type Issue, type OverrideEnd } from "../api";
import { changesForDevice, deviceEntities } from "../charger-device";
import type { TranslationKey } from "../localize";
import { carConnectedRequired, chargerErrors, missingInCharger } from "../validation";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

const ENTITY_VARIABLES = ["entity_id", "entity"];
const CURRENT_VARIABLES = ["current", "min_current", "max_current", ...ENTITY_VARIABLES];

/** Adds or edits one EV charger. */
@customElement("kraftvakt-charger-dialog")
export class KraftvaktChargerDialog extends ItemDialog<Charger> {
  protected readonly section = "chargers";

  protected readonly texts = "charger";

  protected actionsForEntity(entityId: string | null): Partial<Charger> {
    return {
      activate: this.actionForEntity("activate", this.draft.activate, entityId),
      deactivate: this.actionForEntity("deactivate", this.draft.deactivate, entityId),
      set_current: this.actionForEntity("set_current", this.draft.set_current, entityId),
    };
  }

  @property({ type: Boolean }) oneAtATime = false;

  protected errors(): Issue[] {
    return chargerErrors(this.draft, this.capabilities, this.hass);
  }

  /** Every entity of the charger is one of its device's. */
  protected get entityScope(): string[] {
    return deviceEntities(this.hass, this.draft.device_id);
  }

  protected missing(): Issue[] {
    return missingInCharger(this.draft, this.oneAtATime);
  }

  protected renderFields(issues: Issue[]) {
    return html`
      ${this.renderDevice(issues)} ${this.renderEntity(issues)} ${this.renderSection("charger.allowed_charging")}
      ${this.renderAction("activate", issues, ENTITY_VARIABLES)}
      ${this.renderAction("deactivate", issues, ENTITY_VARIABLES)}
      <div class="info">${this.localize("charger.minimum_first")}</div>
      ${this.renderSection("charger.charging_current")}
      ${this.renderForm(
        [this.numberField("min_current_a", "A", true), this.numberField("max_current_a", "A", true)],
        issues,
        (value) =>
          this.changeDraft({
            min_current_a: value.min_current_a as number,
            max_current_a: value.max_current_a as number,
          }),
      )}
      ${this.renderAction("set_current", issues, CURRENT_VARIABLES, true)}
      ${this.renderForm([this.numberField("power_reserve_w", "W", true)], issues, (value) =>
        this.changeDraft({ power_reserve_w: value.power_reserve_w as number }),
      )}
      ${this.renderConditionGroup(
        "car_connected",
        carConnectedRequired(this.draft, this.oneAtATime)
          ? "charger.car_connected_required"
          : "charger.car_connected_optional",
        issues,
      )}
      ${this.renderConditionGroup("actively_charging", "charger.actively_charging", issues)}
      ${this.renderChargingWindow(issues)}
    `;
  }

  private renderDevice(issues: Issue[]) {
    return this.renderForm([{ name: "device_id", required: true, selector: { device: {} } }], issues, (value) =>
      this.deviceChanged((value.device_id as string) || null),
    );
  }

  /** A new device clears the entities that are not on it, and fills the empty fields with its likely entities. */
  private deviceChanged(deviceId: string | null): void {
    if (deviceId === this.draft.device_id) {
      return;
    }
    const changes = changesForDevice(this.draft, deviceId, this.hass, this.capabilities, this.usedEntities);
    this.changeDraft(changes);
    this.entityChanged(changes.entity_id ?? null);
  }

  private renderConditionGroup(field: "car_connected" | "actively_charging", title: TranslationKey, issues: Issue[]) {
    const issue = issues.find((item) => item.field === field);
    const activelyCharging = field === "actively_charging";
    return html`
      <div class="group">
        <div class="group-title">${this.localize(title)}</div>
        <div class="info">${this.helper(field)}</div>
        <kraftvakt-condition-field
          .hass=${this.hass}
          .localize=${this.localize}
          .value=${this.draft[field]}
          .entityId=${this.draft.entity_id}
          .includeEntities=${this.entityScope}
          .kind=${activelyCharging ? "actively_charging" : "condition"}
          .optional=${!activelyCharging}
          .error=${issue ? this.describe(issue) : undefined}
          .disabled=${this.locked}
          @value-changed=${(event: CustomEvent<{ value: Condition | null }>) =>
            this.changeDraft({ [field]: event.detail.value })}
        ></kraftvakt-condition-field>
      </div>
    `;
  }

  private renderChargingWindow(issues: Issue[]) {
    const window = this.draft.charging_window;
    const schema = [
      { name: "charging_window", selector: { boolean: {} } },
      ...(window
        ? [
            {
              type: "grid",
              name: "",
              schema: [
                { name: "start", required: true, selector: { time: { no_second: true } } },
                { name: "end", required: true, selector: { time: { no_second: true } } },
              ],
            },
            { name: "finish_after_window", selector: { boolean: {} } },
            {
              name: "override_ends",
              required: true,
              selector: {
                select: {
                  mode: "dropdown",
                  options: OVERRIDE_ENDS.map((value) => ({
                    value,
                    label: this.localize(`charger.override_ends.${value}`),
                  })),
                },
              },
            },
          ]
        : []),
    ];
    const data = {
      charging_window: window !== null,
      start: window?.start ?? "",
      end: window?.end ?? "",
      finish_after_window: this.draft.finish_after_window,
      override_ends: this.draft.override_ends,
    };
    return html`
      <div class="group">
        ${this.renderForm(
          schema,
          issues,
          (value) =>
            this.changeDraft({
              charging_window: value.charging_window
                ? { start: wholeMinutes(value.start), end: wholeMinutes(value.end) }
                : null,
              finish_after_window: !!value.finish_after_window,
              override_ends: (value.override_ends as OverrideEnd | undefined) ?? this.draft.override_ends,
            }),
          data,
        )}
      </div>
    `;
  }

  static styles = [
    ItemDialog.styles,
    css`
      .group {
        display: grid;
        gap: 8px;
        padding: 12px;
        border: 1px solid var(--divider-color);
        border-radius: var(--ha-border-radius-md, 8px);
      }
      .group-title {
        font-weight: 500;
      }
      .group .info {
        margin-top: 0;
      }
    `,
  ];
}

/** The time selector may give seconds, but the charging window uses whole minutes. */
function wholeMinutes(value: unknown): string {
  return typeof value === "string" ? value.slice(0, 5) : "";
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-charger-dialog": KraftvaktChargerDialog;
  }
}
