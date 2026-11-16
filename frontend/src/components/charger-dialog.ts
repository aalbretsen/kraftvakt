import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { OVERRIDE_ENDS, fetchChargerProfile, type Charger, type Condition, type Issue, type OverrideEnd } from "../api";
import { changesForDevice, deviceEntities } from "../charger-device";
import type { TranslationKey } from "../localize";
import { carConnectedRequired, chargerErrors, missingInCharger } from "../validation";
import "./condition-field";
import { ItemDialog } from "./item-dialog";

const ENTITY_VARIABLES = ["entity_id", "entity"];

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

  /** The charger profile that filled in the fields when the device was chosen. */
  @state() private profile: string | null = null;

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
      ${this.renderDevice(issues)} ${this.renderEntity(issues)}
      ${this.renderForm([this.numberField("power_reserve_w", "W", true)], issues, (value) =>
        this.changeDraft({ power_reserve_w: value.power_reserve_w as number }),
      )}
      ${this.renderActionGroup("activate", issues, ENTITY_VARIABLES)}
      ${this.renderActionGroup("deactivate", issues, ENTITY_VARIABLES)}
      ${this.renderChargingCurrent(issues)}
      ${this.renderConditionGroup(
        "car_connected",
        carConnectedRequired(this.draft, this.oneAtATime)
          ? "charger.car_connected_required"
          : "charger.car_connected_optional",
        issues,
      )}
      ${this.renderConditionGroup("actively_charging", "charger.actively_charging", issues)}
      ${this.renderCloudControl(issues)} ${this.renderChargingWindow(issues)}
    `;
  }

  private renderChargingCurrent(issues: Issue[]) {
    const currents = [
      {
        type: "grid",
        name: "",
        schema: [this.numberField("min_current_a", "A", true), this.numberField("max_current_a", "A", true)],
      },
    ];
    return this.renderGroup({
      title: this.localize("charger.charging_current"),
      description: this.localize("charger.charging_current_info"),
      content: html`
        ${this.renderForm(currents, issues, (value) =>
          this.changeDraft({
            min_current_a: value.min_current_a as number,
            max_current_a: value.max_current_a as number,
          }),
        )}
        ${this.renderAction("set_current", issues, ["current", "min_current", "max_current", ...ENTITY_VARIABLES], true)}
      `,
    });
  }

  private renderDevice(issues: Issue[]) {
    return html`
      ${this.renderForm([{ name: "device_id", required: true, selector: { device: {} } }], issues, (value) =>
        this.deviceChanged((value.device_id as string) || null),
      )}
      ${this.profile
        ? html`<ha-alert alert-type="info">${this.localize("charger.profile_applied", { profile: this.profile })}</ha-alert>`
        : nothing}
    `;
  }

  /** A new device clears the entities that are not on it, and fills in the fields from its charger profile when it has one. */
  private async deviceChanged(deviceId: string | null): Promise<void> {
    if (deviceId === this.draft.device_id) {
      return;
    }
    const changes = changesForDevice(this.draft, deviceId, this.hass);
    this.changeDraft(changes);
    this.entityChanged(changes.entity_id ?? null);
    this.profile = null;
    if (!deviceId) {
      return;
    }
    const { profile, fields } = await fetchChargerProfile(this.hass, deviceId).catch(() => ({ profile: null, fields: {} }));
    if (profile && this.draft.device_id === deviceId) {
      this.changeDraft(fields);
      this.profile = profile;
    }
  }

  private renderConditionGroup(field: "car_connected" | "actively_charging", title: TranslationKey, issues: Issue[]) {
    const issue = issues.find((item) => item.field === field);
    const activelyCharging = field === "actively_charging";
    return this.renderGroup({
      title: this.localize(title),
      description: this.helper(field),
      content: html`
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
      `,
    });
  }

  /**
   * The start delay is kept while the switch is off, since it has no effect then.
   * It stays in view while it has an error, so the error that keeps the draft from being saved can be seen.
   */
  private renderCloudControl(issues: Issue[]) {
    const showDelay = this.draft.cloud_controlled || issues.some((issue) => issue.field === "start_delay_s");
    return this.renderGroup({
      title: this.label("cloud_controlled"),
      description: this.helper("cloud_controlled"),
      toggle: { checked: this.draft.cloud_controlled, changed: (checked) => this.changeDraft({ cloud_controlled: checked }) },
      content: showDelay
        ? this.renderForm([this.numberField("start_delay_s", "s", true)], issues, (value) =>
            this.changeDraft({ start_delay_s: value.start_delay_s as number }),
          )
        : nothing,
    });
  }

  private renderChargingWindow(issues: Issue[]) {
    const window = this.draft.charging_window;
    const issue = issues.find((item) => item.field === "charging_window");
    return this.renderGroup({
      title: this.label("charging_window"),
      description: this.helper("charging_window"),
      toggle: {
        checked: window !== null,
        changed: (checked) => this.changeDraft({ charging_window: checked ? { start: "", end: "" } : null }),
      },
      content: window ? this.renderWindowFields(issues) : nothing,
      error: issue ? this.describe(issue) : undefined,
    });
  }

  private renderWindowFields(issues: Issue[]) {
    const window = this.draft.charging_window;
    const schema = [
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
            options: OVERRIDE_ENDS.map((value) => ({ value, label: this.localize(`charger.override_ends.${value}`) })),
          },
        },
      },
    ];
    const data = {
      start: window?.start ?? "",
      end: window?.end ?? "",
      finish_after_window: this.draft.finish_after_window,
      override_ends: this.draft.override_ends,
    };
    return this.renderForm(
      schema,
      issues,
      (value) =>
        this.changeDraft({
          charging_window: { start: wholeMinutes(value.start), end: wholeMinutes(value.end) },
          finish_after_window: !!value.finish_after_window,
          override_ends: (value.override_ends as OverrideEnd | undefined) ?? this.draft.override_ends,
        }),
      data,
    );
  }

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
