import {
  mdiArrowDown,
  mdiCancel,
  mdiCarElectric,
  mdiCarOff,
  mdiClockEnd,
  mdiClockFast,
  mdiClockOutline,
  mdiEvStation,
  mdiFlash,
  mdiLightningBolt,
  mdiPlus,
  mdiPowerPlugOff,
  mdiTimerOutline,
  mdiTimerSand,
} from "@mdi/js";
import { LitElement, type TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
  type ApplianceStatus,
  type ChargerGroupStatus,
  type ChargerState,
  type ChargerStatus,
  type ConfigResponse,
  type StatusSnapshot,
} from "../api";
import "./countdown";
import { allChargers } from "../draft";
import { formatClockTime, formatPercent, formatPower } from "../format";
import type { Localize, TranslationKey } from "../localize";
import { cardHeaderStyles, chipStyles } from "../status-styles";
import type { HomeAssistant } from "../types";
import { WidthQuery } from "../width-query";

/** How a chip looks: its colour and its icon, or a dot without one. */
interface Chip {
  kind: "on" | "off" | "warning" | "outline" | "info";
  icon?: string;
}

const CHIP_ON: Chip = { kind: "on" };
const CHIP_OFF: Chip = { kind: "off" };
const CHIP_EXCLUDED: Chip = { kind: "outline", icon: mdiCancel };

/** The chip, its word and its sentence for each state of an EV charger. */
const CHARGER_CHIPS: Record<ChargerState, [Chip, TranslationKey, TranslationKey]> = {
  first_decision: [{ kind: "off", icon: mdiTimerSand }, "status.chip_first_decision", "status.first_decision"],
  excluded: [CHIP_EXCLUDED, "status.chip_excluded", "status.excluded"],
  outside_window: [{ kind: "outline", icon: mdiClockOutline }, "status.chip_window", "status.outside_window"],
  no_car: [{ kind: "warning", icon: mdiCarOff }, "status.chip_no_car", "status.bypassed_no_car"],
  not_charging: [{ kind: "warning", icon: mdiPowerPlugOff }, "status.chip_not_charging", "status.bypassed"],
  queued: [{ kind: "off", icon: mdiTimerSand }, "status.chip_queued", "status.waiting_charger"],
  override: [{ kind: "info", icon: mdiClockFast }, "status.chip_override", "status.window_overridden"],
  finishing: [{ kind: "info", icon: mdiClockEnd }, "status.chip_finishing", "status.finishing_at"],
  charging: [{ kind: "on", icon: mdiLightningBolt }, "status.chip_charging", "status.charging_at"],
  activated: [CHIP_ON, "status.activated", "status.activated_not_charging"],
  deactivated: [CHIP_OFF, "status.deactivated", "status.deactivated"],
};

/** An entry in the priority list: an appliance, or a group with its EV chargers. */
type PriorityEntry =
  | { kind: "appliance"; appliance: ApplianceStatus; on: boolean }
  | { kind: "charger_group"; group: ChargerGroupStatus; on: boolean };

/** Return the entries of the priority list, each with whether it is on. */
function priorityEntries(status: StatusSnapshot): PriorityEntry[] {
  return status.priority.map((row) =>
    row.type === "appliance"
      ? { kind: "appliance", appliance: row, on: row.on }
      : {
          kind: "charger_group",
          group: row,
          on: row.chargers.some((charger) => charger.activated && !charger.bypassed),
        },
  );
}

/**
 * Return the index of the entry the cut-off line goes under: the last entry
 * that is on. There is no line (-1) when nothing is on, or when only excluded
 * appliances are below the last entry that is on. A group is on while one of
 * its EV chargers is activated and not bypassed.
 */
function cutOffIndex(entries: PriorityEntry[]): number {
  const last = entries.map((entry) => entry.on).lastIndexOf(true);
  const regulatedBelow = entries
    .slice(last + 1)
    .some((entry) => entry.kind === "charger_group" || !entry.appliance.excluded);
  return last >= 0 && regulatedBelow ? last : -1;
}

/** Return «22» for «22:00», and the time as it is otherwise. */
function shortTime(time: string): string {
  return time.endsWith(":00") ? time.slice(0, -3) : time;
}

/** The card with the priority list as it stands: appliances, and groups with their EV chargers. */
@customElement("kraftvakt-priority-list")
export class KraftvaktPriorityList extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status!: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  /** The widest list, in pixels, that gets the phone layout. It is as wide as the status page. */
  private readonly phoneQuery = new WidthQuery(this, 600);

  private get phone(): boolean {
    return this.phoneQuery.matches;
  }

  protected render() {
    const entries = priorityEntries(this.status);
    const cutAfter = cutOffIndex(entries);
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.priority_list")}</span>
        </div>
        ${entries.length === 0
          ? html`<div class="empty">${this.localize("status.no_appliances")}</div>`
          : html`<div class="list ${this.phone ? "phone" : ""}">
              ${entries.map(
                (entry, index) => html`
                  ${entry.kind === "appliance"
                    ? this.renderApplianceRow(entry.appliance, index + 1)
                    : this.renderChargerGroup(entry.group, index + 1)}
                  ${index === cutAfter ? this.renderCutOff() : nothing}
                `,
              )}
            </div>`}
      </ha-card>
    `;
  }

  private renderApplianceRow(appliance: ApplianceStatus, rank: number) {
    return html`
      <div class="row ${appliance.on ? "" : "off"} ${appliance.excluded ? "excluded" : ""}">
        ${this.renderRank(rank)}
        <div class="row-title">
          ${this.renderApplianceIcon(appliance)}${this.renderName(appliance.name)}
          ${appliance.variant && !this.phone
            ? html`<span class="variant" title=${appliance.variant}>${appliance.variant}</span>`
            : nothing}
        </div>
        <span></span>
        ${this.renderWideOnly(
          this.renderWaiting(appliance, mdiTimerOutline, "status.delayed_turn_on", "status.waiting_ends_at"),
        )}
        ${this.renderApplianceChip(appliance)}
      </div>
    `;
  }

  /**
   * The rank column. Like the other columns between the title and the chip, except the current,
   * it is left out on a phone.
   */
  private renderRank(rank: number | null) {
    return this.renderWideOnly(html`<span class="rank">${rank ?? nothing}</span>`);
  }

  private renderWideOnly(content: TemplateResult) {
    return this.phone ? nothing : content;
  }

  /** The name, on one line cut with an ellipsis when it is too long, with the whole name as a tooltip. */
  private renderName(name: string) {
    return html`<span class="name" title=${name}>${name}</span>`;
  }

  private renderApplianceChip(appliance: ApplianceStatus) {
    if (appliance.excluded) {
      return this.renderChip(CHIP_EXCLUDED, "status.chip_excluded", "status.excluded");
    }
    return appliance.on
      ? this.renderChip(CHIP_ON, "status.on", "status.on")
      : this.renderChip(CHIP_OFF, "status.off", "status.off");
  }

  /**
   * The icon of the appliance's entity, coloured as Home Assistant colours a switch that is on, or
   * a default icon.
   */
  private renderApplianceIcon(appliance: ApplianceStatus) {
    const entityId = this.config?.config.appliances.find((item) => item.id === appliance.id)?.entity_id;
    const stateObj = entityId ? this.hass.states[entityId] : undefined;
    // The slot is one icon wide. The entity's icon pushes the default icon out of it; an icon
    // Home Assistant cannot load takes no width and leaves the default icon in view.
    return html`
      <span class="device-icon ${appliance.on ? "on" : ""}">
        ${stateObj ? html`<ha-state-icon .hass=${this.hass} .stateObj=${stateObj}></ha-state-icon>` : nothing}
        <ha-svg-icon .path=${mdiFlash}></ha-svg-icon>
      </span>
    `;
  }

  private renderChargerGroup(group: ChargerGroupStatus, rank: number) {
    const chargers = group.chargers;
    const charging = chargers.filter((charger) => charger.charging).length;
    return html`
      <div class="row group">
        ${this.renderRank(rank)}
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${mdiCarElectric}></ha-svg-icon>
          ${this.renderName(group.name)}
          ${chargers.length === 0 && !this.phone
            ? html`<span class="row-sub">${this.localize("status.no_chargers")}</span>`
            : nothing}
        </div>
        ${this.renderWideOnly(
          chargers.length === 0
            ? html`<span></span>`
            : html`<span
                class="charging-count"
                title=${this.localize("status.chargers_charging", { charging, total: chargers.length })}
              >
                <ha-svg-icon .path=${mdiLightningBolt}></ha-svg-icon>${charging} / ${chargers.length}
              </span>`,
        )}
      </div>
      ${chargers.map((charger) => this.renderChargerRow(charger))}
    `;
  }

  private renderChargerRow(charger: ChargerStatus) {
    return html`
      <div class="row charger ${charger.activated ? "" : "off"}">
        ${this.renderRank(null)}
        <div class="row-title">
          <ha-svg-icon class="device-icon ev ${charger.activated ? "on" : ""}" .path=${mdiEvStation}></ha-svg-icon>
          ${this.renderName(charger.name)}
        </div>
        ${this.phone ? this.renderPhoneCurrent(charger) : this.renderAmperes(charger)}
        ${this.renderWideOnly(this.renderWaiting(charger, mdiPlus, "status.delayed_turn_on", "status.next_ampere_at"))}
        ${this.renderChargerChip(charger)}
      </div>
    `;
  }

  /** An icon and a bar that empties from when the waiting started until the decision that ends it. */
  private renderWaiting(
    item: ApplianceStatus | ChargerStatus,
    icon: string,
    label: TranslationKey,
    endsAt: TranslationKey,
  ) {
    if (!item.waiting_since || !item.waiting_ends_at) {
      return html`<span></span>`;
    }
    const time = formatClockTime(this.hass.language, item.waiting_ends_at);
    return html`
      <span class="waiting" title="${this.localize(label)}: ${this.localize(endsAt, { time })}">
        <ha-svg-icon .path=${icon}></ha-svg-icon>
        <kraftvakt-countdown-bar
          .start=${Date.parse(item.waiting_since)}
          .end=${Date.parse(item.waiting_ends_at)}
        ></kraftvakt-countdown-bar>
      </span>
    `;
  }

  /** The current, and one bar per ampere from the minimum to the maximum, filled up to the current. */
  private renderAmperes(charger: ChargerStatus) {
    const config = this.chargerConfig(charger);
    if (!config) {
      return html`<span></span>`;
    }
    const steps = config.max_current_a - config.min_current_a + 1;
    const on = charger.current_a === null ? 0 : charger.current_a - config.min_current_a + 1;
    const filled = charger.bypassed ? "on bypassed" : "on";
    return html`
      <span class="amperes">
        <span class="current ${charger.current_a === null ? "none" : ""}"
          >${charger.current_a === null ? "–" : this.localize("status.amperes", { current: charger.current_a })}</span
        >
        <span class="ampere-steps ${steps > 16 ? "small" : ""}">
          ${Array.from({ length: steps }, (_, index) => html`<span class="ampere ${index < on ? filled : ""}"></span>`)}
        </span>
      </span>
    `;
  }

  /** On a phone, the current alone, and nothing for a charger without one. */
  private renderPhoneCurrent(charger: ChargerStatus) {
    return charger.current_a === null
      ? html`<span></span>`
      : html`<span class="current">${this.localize("status.amperes", { current: charger.current_a })}</span>`;
  }

  private renderChargerChip(charger: ChargerStatus) {
    const [chip, word, sentence] = CHARGER_CHIPS[charger.state];
    const window = this.chargerConfig(charger)?.charging_window;
    if (charger.state === "outside_window" && window) {
      const short = { start: shortTime(window.start), end: shortTime(window.end) };
      return this.renderChip(chip, word, sentence, short, { ...window });
    }
    return this.renderChip(chip, word, sentence, {}, { current: charger.current_a ?? 0 });
  }

  /** A chip with an icon (or a dot) and a word, and the whole sentence as a tooltip. */
  private renderChip(
    chip: Chip,
    word: TranslationKey,
    sentence: TranslationKey,
    wordParams: Record<string, string | number> = {},
    sentenceParams: Record<string, string | number> = wordParams,
  ) {
    return html`
      <span class="state chip ${chip.kind}" title=${this.localize(sentence, sentenceParams)}>
        ${chip.icon ? html`<ha-svg-icon .path=${chip.icon}></ha-svg-icon>` : html`<span class="dot"></span>`}
        ${this.localize(word, wordParams)}
      </span>
    `;
  }

  /** The line where the power runs out, with the free power and its share of the limit while there is any. */
  private renderCutOff() {
    const status = this.status;
    const language = this.hass.language;
    const average = status.regulation_average_w;
    const free = average === null ? 0 : status.power_limit_w - average;
    return html`
      <div class="cut-off" title=${this.localize("status.power_runs_out")}>
        <ha-svg-icon .path=${mdiArrowDown}></ha-svg-icon>
        ${free > 0
          ? this.localize("status.free_power", {
              power: formatPower(language, free),
              share: formatPercent(language, free / status.power_limit_w),
            })
          : nothing}
      </div>
    `;
  }

  private chargerConfig(charger: ChargerStatus) {
    return this.config && allChargers(this.config.config).find((item) => item.id === charger.id);
  }

  static styles = [
    cardHeaderStyles,
    chipStyles,
    css`
      :host {
        display: block;
      }
      .empty {
        padding: 0 16px 16px;
        color: var(--secondary-text-color);
      }
      .list {
        display: grid;
        grid-template-columns: minmax(24px, max-content) minmax(0, 2fr) minmax(max-content, 1.3fr) 120px max-content;
        column-gap: 12px;
      }
      .row {
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: subgrid;
        align-items: center;
        min-height: 48px;
        padding: 4px 16px;
        border-top: 1px solid var(--divider-color);
        box-sizing: border-box;
      }
      :host([narrow]) .row {
        padding: 4px 12px;
      }
      .row.group,
      .row.charger {
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 7%, transparent);
      }
      .row.charger {
        min-height: 44px;
        border-top-style: dashed;
      }
      .row.off .name {
        color: var(--secondary-text-color);
      }
      .row.excluded .row-title {
        opacity: 0.5;
      }
      .row.charger .row-title {
        padding-inline-start: 24px;
      }
      :host([narrow]) .row.charger .row-title {
        padding-inline-start: 16px;
      }
      .rank {
        text-align: end;
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }
      .row > .chip {
        justify-self: start;
      }
      .cut-off {
        grid-column: 1 / -1;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 16px;
        border-top: 1px solid var(--divider-color);
        color: var(--primary-color);
        font-size: var(--ha-font-size-s, 12px);
        white-space: nowrap;
      }
      .cut-off::before,
      .cut-off::after {
        content: "";
        flex: 1;
        border-top: 2px dashed var(--primary-color);
      }
      .cut-off ha-svg-icon {
        --mdc-icon-size: 14px;
      }
      .waiting {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .waiting kraftvakt-countdown-bar {
        flex: 1;
      }
      .waiting ha-svg-icon,
      .charging-count ha-svg-icon {
        flex: none;
        --mdc-icon-size: 16px;
        color: var(--secondary-text-color);
      }
      .charging-count {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
      }
      .charging-count ha-svg-icon {
        color: var(--kraftvakt-ev-color);
      }
      .amperes {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .current {
        min-width: 40px;
        text-align: end;
        font-weight: 500;
      }
      .amperes .current.none {
        color: var(--secondary-text-color);
        font-weight: normal;
      }
      .ampere-steps {
        display: inline-flex;
        gap: 2px;
      }
      .ampere {
        width: 3px;
        height: 14px;
        border-radius: 1px;
        background: rgba(127, 127, 127, 0.32);
      }
      .ampere-steps.small {
        gap: 1px;
      }
      .ampere-steps.small .ampere {
        width: 2px;
      }
      .ampere.on {
        background: var(--kraftvakt-ev-color);
      }
      .ampere.on.bypassed {
        background: repeating-linear-gradient(
          45deg,
          var(--secondary-text-color) 0 2px,
          rgba(127, 127, 127, 0.16) 2px 4px
        );
      }
      .row-title {
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 0;
      }
      .name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .row-title ha-svg-icon,
      .row-title ha-state-icon {
        flex: none;
        --mdc-icon-size: 20px;
      }
      .row-title ha-svg-icon,
      .row-title .device-icon {
        color: var(--state-inactive-color, var(--secondary-text-color));
      }
      .row-title .device-icon > * {
        color: inherit;
      }
      span.device-icon {
        display: flex;
        flex: none;
        width: 20px;
        height: 20px;
        overflow: hidden;
      }
      .row-title .device-icon.on {
        color: var(--kraftvakt-on-color);
      }
      .row-title .device-icon.ev.on,
      .row-title .ev-icon {
        color: var(--kraftvakt-ev-color);
      }
      .row.group .name {
        font-weight: 500;
      }
      .row-sub {
        flex: none;
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
      }
      .variant {
        flex: 0 1000 auto;
        min-width: 3em;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        padding: 0 8px;
        border-radius: 999px;
        font-size: var(--ha-font-size-s, 12px);
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
        color: var(--primary-color);
      }
      .list.phone {
        grid-template-columns: minmax(0, 1fr) max-content max-content;
        column-gap: 8px;
      }
      .list.phone .row > .chip {
        justify-self: end;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-priority-list": KraftvaktPriorityList;
  }
}
