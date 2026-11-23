import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import { OVERRIDE_ENDS, SWITCHED_BY, type Charger, type Condition, type Issue, type OverrideEnd, type SwitchedBy } from "../api";
import { changesForDevice, chargerProfileOf, deviceEntities } from "../devices";
import { chargerErrors, defaultActionOf, missingInCharger } from "../validation";
import "./condition-field";
import type { ConditionKind } from "./condition-field";
import { ItemDialog } from "./item-dialog";

/** Adds or edits one EV charger. */
@customElement("kraftvakt-charger-dialog")
export class KraftvaktChargerDialog extends ItemDialog<Charger> {
  protected readonly section = "chargers";

  protected readonly texts = "charger";

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
    return missingInCharger(this.draft);
  }

  protected renderFields(issues: Issue[]) {
    return html`
      ${this.renderDevice(issues)}
      ${this.renderForm([this.numberField("min_current_power_w", "W", true)], issues, (value) => this.changeDraft({ min_current_power_w: value.min_current_power_w as number }))}
      ${this.renderOnOff(issues)} ${this.renderChargingCurrent(issues)} ${this.renderCarConnected(issues)} ${this.renderActivelyCharging(issues)} ${this.renderCloudControl()}
      ${this.renderChargingWindow(issues)} ${this.renderDeactivateOnFault(issues)}
    `;
  }

  /** The on/off entity and the actions are kept while the charger is switched another way, since it uses neither. */
  private renderOnOff(issues: Issue[]) {
    const options = SWITCHED_BY.map((value) => ({ value, label: this.localize(`charger.switched_by.${value}`) }));
    const switchedBy = this.renderForm([{ name: "switched_by", required: true, selector: { select: { mode: "list", options } } }], issues, (value) =>
      this.switchedByChanged(value.switched_by as SwitchedBy),
    );
    return this.renderGroup({
      title: this.localize("charger.on_off"),
      description: this.localize("charger.on_off_info"),
      content: [switchedBy, ...this.renderOnOffChoice(issues)],
    });
  }

  /** The parts the choice shows, each in the group's list of parts. */
  private renderOnOffChoice(issues: Issue[]) {
    switch (this.draft.switched_by) {
      case "on_off_entity":
        return [
          this.renderEntityField(
            "on_off_entity",
            issues,
            (entityId) => this.changeDraft({ on_off_entity: entityId }),
            defaultActionOf(this.capabilities, "chargers", "activate").domains,
          ),
        ];
      case "actions":
        return [this.renderAction("activate", issues), this.renderAction("deactivate", issues)];
      case "current":
        return [html`<div class="helper">${this.localize("charger.switched_by_current_info")}</div>`];
    }
  }

  /** Actions that are not given start as empty custom actions, the only kind an EV charger has. */
  private switchedByChanged(switchedBy: SwitchedBy | undefined): void {
    const empty = { mode: "custom" as const, action: [] };
    this.changeDraft({
      switched_by: switchedBy ?? this.draft.switched_by,
      activate: this.draft.activate ?? empty,
      deactivate: this.draft.deactivate ?? empty,
    });
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
      content: [
        this.renderForm(currents, issues, (value) =>
          this.changeDraft({
            min_current_a: value.min_current_a as number,
            max_current_a: value.max_current_a as number,
          }),
        ),
        this.renderAction("set_current", issues, { entityAllowed: true, extraVariables: ["current", "min_current", "max_current"] }),
      ],
    });
  }

  private renderDevice(issues: Issue[]) {
    return html`
      ${this.renderForm([{ name: "device_id", required: true, selector: { device: {} } }], issues, (value) => this.deviceChanged((value.device_id as string) || null))}
      ${this.profile ? html`<ha-alert alert-type="info">${this.localize("charger.profile_applied", { profile: this.profile })}</ha-alert>` : nothing}
    `;
  }

  /** A new device clears the entities that are not on it, and fills in the fields from its charger profile, or the settings of the default profile without one. */
  private async deviceChanged(deviceId: string | null): Promise<void> {
    if (deviceId === this.draft.device_id) {
      return;
    }
    this.changeDraft(changesForDevice(this.draft, deviceId, this.hass));
    this.profile = null;
    if (!deviceId) {
      return;
    }
    const { profile, fields } = await chargerProfileOf(this.hass, deviceId, this.capabilities);
    if (this.draft.device_id === deviceId) {
      this.changeDraft(fields);
      this.profile = profile;
    }
  }

  private renderCarConnected(issues: Issue[]) {
    return this.renderGroup({
      title: this.label("car_connected"),
      description: this.helper("car_connected"),
      content: this.renderCondition("car_connected", "condition", issues),
    });
  }

  /**
   * The charging power, which every EV charger needs, the optional car charging, which may tell sooner that the car charges,
   * and the start delay, how long the car may take to charge after the EV charger is activated.
   */
  private renderActivelyCharging(issues: Issue[]) {
    return this.renderGroup({
      title: this.label("actively_charging"),
      description: this.helper("actively_charging"),
      content: [
        this.renderCondition("charging_power", "charging_power", issues),
        this.renderCondition("actively_charging", "actively_charging", issues, true),
        this.renderForm([this.numberField("start_delay_s", "s", true)], issues, (value) => this.changeDraft({ start_delay_s: value.start_delay_s as number })),
      ],
    });
  }

  private stateChoices(field: "car_connected" | "actively_charging" | "fault_flag") {
    return {
      true: this.localize(`charger.state_choices.${field}.true`),
      false: this.localize(`charger.state_choices.${field}.false`),
    };
  }

  private renderCondition(field: "car_connected" | "actively_charging" | "charging_power" | "fault_flag", kind: ConditionKind, issues: Issue[], optional = false) {
    const issue = issues.find((item) => item.field === field);
    return html`
      <kraftvakt-condition-field
        .hass=${this.hass}
        .localize=${this.localize}
        .value=${this.draft[field]}
        .variables=${this.variables}
        .includeEntities=${this.entityScope}
        .kind=${kind}
        .optional=${optional}
        .stateChoices=${field === "charging_power" ? undefined : this.stateChoices(field)}
        .error=${issue ? this.describe(issue) : undefined}
        .disabled=${this.locked}
        @value-changed=${(event: CustomEvent<{ value: Condition }>) => this.changeDraft({ [field]: event.detail.value })}
      ></kraftvakt-condition-field>
    `;
  }

  private renderCloudControl() {
    return this.renderGroup({
      title: this.label("cloud_controlled"),
      description: this.helper("cloud_controlled"),
      toggle: { checked: this.draft.cloud_controlled, changed: (checked) => this.changeDraft({ cloud_controlled: checked }) },
      content: nothing,
    });
  }

  /**
   * The fault flag is kept while the switch is off, since it has no effect then.
   * It stays in view while it has an error, so the error that keeps the draft from being saved can be seen.
   */
  private renderDeactivateOnFault(issues: Issue[]) {
    const showFlag = this.draft.deactivate_on_fault || issues.some((issue) => issue.field === "fault_flag");
    return this.renderGroup({
      title: this.label("deactivate_on_fault"),
      description: this.helper("deactivate_on_fault"),
      toggle: { checked: this.draft.deactivate_on_fault, changed: (checked) => this.changeDraft({ deactivate_on_fault: checked }) },
      content: showFlag ? this.renderCondition("fault_flag", "fault", issues) : nothing,
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
      { name: "charge_until_disconnected", selector: { boolean: {} } },
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
      charge_until_disconnected: this.draft.charge_until_disconnected,
      override_ends: this.draft.override_ends,
    };
    return this.renderForm(
      schema,
      issues,
      (value) =>
        this.changeDraft({
          charging_window: { start: wholeMinutes(value.start), end: wholeMinutes(value.end) },
          charge_until_disconnected: !!value.charge_until_disconnected,
          override_ends: (value.override_ends as OverrideEnd | undefined) ?? this.draft.override_ends,
        }),
      data,
    );
  }

  static styles = [
    ItemDialog.styles,
    css`
      /* Indented as Home Assistant indents the helper text of a field. */
      .helper {
        padding-inline-start: 16px;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
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
