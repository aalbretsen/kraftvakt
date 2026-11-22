import { mdiArrowCollapseDown, mdiArrowDown, mdiCarElectric, mdiEvStation, mdiFlash, mdiLightningBolt, mdiTimerOutline } from "@mdi/js";
import { LitElement, type TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import { type ApplianceStatus, type ChargerGroupStatus, type ChargerStatus, type ConfigResponse, type StatusSnapshot, type WaitingFields } from "../api";
import "./countdown";
import { CHARGER_CHIPS, CHIP_EXCLUDED, type Chip } from "../charger-chips";
import { allChargers } from "../draft";
import { controlledEntity, existingEntity } from "../entities";
import { formatClockTime, formatNumber, formatPercent, formatPower } from "../format";
import type { Localize, TranslationKey } from "../localize";
import { showMoreInfo } from "../navigation";
import { cardHeaderStyles, chipStyles } from "../status-styles";
import type { HomeAssistant } from "../types";
import { WidthQuery } from "../width-query";

const CHIP_ON: Chip = { kind: "on" };
const CHIP_OFF: Chip = { kind: "off" };

/** An entry in the priority list: an appliance, or a group with its EV chargers. */
type PriorityEntry = { kind: "appliance"; appliance: ApplianceStatus; on: boolean } | { kind: "charger_group"; group: ChargerGroupStatus; on: boolean };

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
  const regulatedBelow = entries.slice(last + 1).some((entry) => entry.kind === "charger_group" || !entry.appliance.excluded);
  return last >= 0 && regulatedBelow ? last : -1;
}

/** Return whether some row, an appliance or an EV charger, has a power. */
function hasPower(status: StatusSnapshot): boolean {
  const rows = status.priority.flatMap((row): (ApplianceStatus | ChargerStatus)[] => (row.type === "appliance" ? [row] : row.chargers));
  return rows.some((row) => row.power_w !== null);
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

  /** Whether some row has a power; without one, the column is left out, so it takes no room and no gap. */
  private hasPower = false;

  protected render() {
    const entries = priorityEntries(this.status);
    const cutAfter = cutOffIndex(entries);
    this.hasPower = hasPower(this.status);
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.appliances_and_chargers")}</span>
        </div>
        ${
          entries.length === 0
            ? html`<div class="empty">${this.localize("status.no_appliances")}</div>`
            : html`<div class="list ${this.phone ? "phone" : ""}" style=${this.phone ? "" : this.columns()}>
                ${entries.map(
                  (entry, index) => html`
                    ${entry.kind === "appliance" ? this.renderApplianceRow(entry.appliance, index + 1) : this.renderChargerGroup(entry.group, index + 1)}
                    ${index === cutAfter ? this.renderCutOff() : nothing}
                  `,
                )}
              </div>`
        }
      </ha-card>
    `;
  }

  /**
   * The columns of the list: rank, name, current, power, waiting and state.
   * The name takes the room that is left, so the other columns, as wide as their content, line up at the right.
   * An appliance's temperature is in the current column, since an EV charger never has one.
   */
  private columns(): string {
    const columns = ["minmax(24px, max-content)", "minmax(0, 1fr)", "max-content", ...(this.hasPower ? ["max-content"] : []), "var(--waiting-width)", "max-content"];
    return `grid-template-columns: ${columns.join(" ")}`;
  }

  /** A row of an appliance or EV charger opens Home Assistant's more-info dialog for its entity, while the entity exists. */
  private renderRow(classes: string, entityId: string | null, content: TemplateResult) {
    if (!entityId) {
      return html`<div class="row ${classes}">${content}</div>`;
    }
    const open = (event: Event) => {
      event.preventDefault();
      showMoreInfo(event, entityId);
    };
    return html`
      <div
        class="row ${classes} clickable"
        role="button"
        tabindex="0"
        @click=${open}
        @keydown=${(event: KeyboardEvent) => (event.key === "Enter" || event.key === " " ? open(event) : undefined)}
      >
        ${content}
      </div>
    `;
  }

  /** The name takes the current column too, unless the appliance has a temperature to show there. */
  private renderApplianceRow(appliance: ApplianceStatus, rank: number) {
    const temperature = appliance.temperature !== null && !this.phone;
    return this.renderRow(
      `appliance ${appliance.on ? "" : "off"} ${appliance.excluded ? "excluded" : ""} ${appliance.essential ? "essential" : ""} ${temperature ? "with-temperature" : ""}`,
      existingEntity(this.hass, this.applianceEntity(appliance)),
      html`
        ${this.renderRank(rank)}
        <div class="row-title">
          ${this.renderApplianceIcon(appliance)}${this.renderName(appliance.name)}
          ${appliance.variant && !this.phone ? html`<span class="variant" title=${appliance.variant}>${appliance.variant}</span>` : nothing}
        </div>
        ${this.renderTemperature(appliance)} ${this.renderPower(appliance.power_w)} ${this.renderApplianceWaiting(appliance)} ${this.renderApplianceChip(appliance)}
      `,
    );
  }

  /** The rank column, left out on a phone. */
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
    return appliance.on ? this.renderChip(CHIP_ON, "status.on", "status.on") : this.renderChip(CHIP_OFF, "status.off", "status.off");
  }

  /**
   * The icon of the appliance's entity, coloured as Home Assistant colours a switch that is on, or
   * a default icon.
   */
  private renderApplianceIcon(appliance: ApplianceStatus) {
    const entityId = this.applianceEntity(appliance);
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

  /** A group with one EV charger is shown as that EV charger alone, since the group's settings make no difference then. */
  private renderChargerGroup(group: ChargerGroupStatus, rank: number) {
    const chargers = group.chargers;
    if (chargers.length === 1) {
      return this.renderChargerRow(chargers[0], rank);
    }
    const charging = chargers.filter((charger) => charger.charging).length;
    return html`
      <div class="row group">
        ${this.renderRank(rank)}
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${mdiCarElectric}></ha-svg-icon>
          ${this.renderName(group.name)} ${chargers.length === 0 && !this.phone ? html`<span class="row-sub">${this.localize("status.no_chargers")}</span>` : nothing}
        </div>
        ${this.renderWideOnly(
          chargers.length === 0
            ? html`<span></span>`
            : html`<span class="charging-count" title=${this.localize("status.chargers_charging", { charging, total: chargers.length })}>
                <ha-svg-icon .path=${mdiLightningBolt}></ha-svg-icon>${charging} / ${chargers.length}
              </span>`,
        )}
      </div>
      ${chargers.map((charger) => this.renderChargerRow(charger, null))}
    `;
  }

  /** An EV charger with a rank stands alone, and one without is indented under its group. */
  private renderChargerRow(charger: ChargerStatus, rank: number | null) {
    return this.renderRow(
      `charger ${rank === null ? "" : "alone"} ${charger.activated ? "" : "off"}`,
      existingEntity(this.hass, this.chargerEntity(charger)),
      html`
        ${this.renderRank(rank)}
        <div class="row-title">
          <ha-svg-icon class="device-icon ev ${charger.activated ? "on" : ""}" .path=${mdiEvStation}></ha-svg-icon>
          ${this.renderName(charger.name)}
        </div>
        ${this.phone ? this.renderPhoneCurrent(charger) : this.renderAmperes(charger)} ${this.renderPower(charger.power_w)} ${this.renderChargerWaiting(charger)}
        ${this.renderChargerChip(charger)}
      `,
    );
  }

  private renderApplianceWaiting(appliance: ApplianceStatus) {
    return this.renderWaiting(
      appliance,
      (time) => `${this.localize("status.delayed_turn_on")}: ${this.localize("status.waiting_ends_at", { time })}`,
      () => this.renderPowerToFree(appliance.power_to_free_w, "status.power_to_free_turn_on"),
    );
  }

  /**
   * While it holds back the next step, that is shown instead of the power to free: the damping of an ampere taken back,
   * the start delay that holds back the steps below it, or the waiting time of an EV charger activated again.
   */
  private renderChargerWaiting(charger: ChargerStatus) {
    return this.renderWaiting(
      charger,
      (time) => {
        switch (charger.waiting_reason) {
          case "damping":
            return `${this.localize("status.damping")}: ${this.localize("status.damping_ampere_at", { time })}`;
          case "start_delay":
            return `${this.localize("status.start_delay")}: ${this.localize("status.start_delay_ends_at", { time })}`;
          default:
            return `${this.localize("status.delayed_activation")}: ${this.localize("status.activated_at", { time })}`;
        }
      },
      () => this.renderPowerToFree(charger.power_to_free_w, charger.activated ? "status.power_to_free_ampere" : "status.power_to_free_activate"),
    );
  }

  /**
   * An icon and a bar that empties from when the waiting started until the decision that ends it,
   * or else what `otherwise` renders. On a phone, the icon alone.
   */
  private renderWaiting(row: WaitingFields, title: (time: string) => string, otherwise: () => unknown) {
    if (!row.waiting_since || !row.waiting_ends_at) {
      return otherwise();
    }
    return html`
      <span class="waiting" title=${title(formatClockTime(this.hass.language, row.waiting_ends_at))}>
        <ha-svg-icon .path=${mdiTimerOutline}></ha-svg-icon>
        ${this.renderWideOnly(html`<kraftvakt-countdown-bar .start=${Date.parse(row.waiting_since)} .end=${Date.parse(row.waiting_ends_at)}></kraftvakt-countdown-bar>`)}
      </span>
    `;
  }

  /** An icon and the power in kW that must be freed before the next step is turned on, in the waiting column. On a phone, the icon alone. */
  private renderPowerToFree(powerW: number | null, sentence: TranslationKey) {
    if (powerW === null) {
      return this.phone ? nothing : html`<span></span>`;
    }
    const power = formatPower(this.hass.language, powerW);
    return html`
      <span class="waiting" title=${this.localize(sentence, { power })}>
        <ha-svg-icon .path=${mdiArrowCollapseDown}></ha-svg-icon>
        ${this.renderWideOnly(html`<span class="power-to-free">${power} kW</span>`)}
      </span>
    `;
  }

  /** The power in kW, left out on a phone and when no row has one. */
  private renderPower(powerW: number | null) {
    if (!this.hasPower) {
      return nothing;
    }
    return this.renderWideOnly(
      html`<span class="measured" title=${this.localize("status.power")}>${powerW === null ? nothing : `${formatPower(this.hass.language, powerW)} kW`}</span>`,
    );
  }

  /** The temperature with one decimal and its unit, right aligned in the current column with the ampere bars. Left out on a phone. */
  private renderTemperature(appliance: ApplianceStatus) {
    const temperature = appliance.temperature;
    if (temperature === null || this.phone) {
      return nothing;
    }
    return html`<span class="measured" title=${this.localize("status.temperature")}>${formatNumber(this.hass.language, temperature.value, 1)} ${temperature.unit}</span>`;
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
    return charger.current_a === null ? nothing : html`<span class="current">${this.localize("status.amperes", { current: charger.current_a })}</span>`;
  }

  private renderChargerChip(charger: ChargerStatus) {
    const [chip, word, sentence] = CHARGER_CHIPS[charger.state];
    const window = this.chargerConfig(charger)?.charging_window;
    if (charger.state === "outside_window" && window) {
      const short = { start: shortTime(window.start), end: shortTime(window.end) };
      return this.renderChip(chip, word, sentence, short, { ...window });
    }
    if (charger.starting_until) {
      return this.renderChip(chip, word, sentence, {}, { time: formatClockTime(this.hass.language, charger.starting_until) });
    }
    if (charger.state === "queued" && this.sharesByChargingPower(charger)) {
      return this.renderChip(chip, word, "status.queued_for_room");
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
        ${chip.icon ? html`<ha-svg-icon .path=${chip.icon}></ha-svg-icon>` : html`<span class="dot"></span>`} ${this.localize(word, wordParams)}
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
        ${
          free > 0
            ? this.localize("status.free_power", {
                power: formatPower(language, free),
                share: formatPercent(language, free / status.power_limit_w),
              })
            : nothing
        }
      </div>
    `;
  }

  private applianceEntity(appliance: ApplianceStatus) {
    return this.config?.config.appliances.find((item) => item.id === appliance.id)?.entity_id;
  }

  private chargerConfig(charger: ChargerStatus) {
    return this.config && allChargers(this.config.config).find((item) => item.id === charger.id);
  }

  /** The on/off entity of the charger, when it is switched by one. */
  private chargerEntity(charger: ChargerStatus): string | null {
    const config = this.chargerConfig(charger);
    return config ? controlledEntity(config) : null;
  }

  private sharesByChargingPower(charger: ChargerStatus): boolean {
    const group = this.config?.config.charger_groups.find((item) => item.chargers.some((other) => other.id === charger.id));
    return !!group && group.dynamic_order && !group.one_at_a_time;
  }

  static styles = [
    cardHeaderStyles,
    chipStyles,
    css`
      :host {
        display: block;
        container-type: inline-size;
      }
      /*
       * The spacing grows with the list's width, from tight just above the phone layout (600 px)
       * to the widest list the panel gets (1040 px), where the columns after the name take its right half.
       */
      ha-card {
        --column-gap: clamp(12px, 5.455cqi - 20.7px, 36px);
        --waiting-width: clamp(72px, 14.545cqi - 15.3px, 136px);
        --row-padding-end: clamp(16px, 3.636cqi - 5.8px, 32px);
      }
      .empty {
        padding: 0 16px 16px;
        color: var(--secondary-text-color);
      }
      .list {
        display: grid;
        column-gap: var(--column-gap);
      }
      .row {
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: subgrid;
        align-items: center;
        min-height: 48px;
        padding: 4px var(--row-padding-end) 4px 16px;
        border-top: 1px solid var(--divider-color);
        box-sizing: border-box;
      }
      :host([narrow]) .row {
        padding-inline-start: 12px;
      }
      .row.group,
      .row.charger {
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 7%, transparent);
      }
      .row.essential {
        background: var(--kraftvakt-essential-background);
      }
      .row.clickable {
        cursor: pointer;
      }
      .row.clickable:hover {
        background-image: linear-gradient(color-mix(in srgb, var(--primary-text-color) 6%, transparent) 0 0);
      }
      .row.clickable:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
      }
      .row.charger:not(.alone) {
        min-height: 44px;
        border-top-style: dashed;
      }
      .row.off .name {
        color: var(--secondary-text-color);
      }
      .row.excluded .row-title {
        opacity: 0.5;
      }
      .row.appliance:not(.with-temperature) .row-title {
        grid-column: span 2;
      }
      .row.charger:not(.alone) .row-title {
        padding-inline-start: 24px;
      }
      :host([narrow]) .row.charger:not(.alone) .row-title {
        padding-inline-start: 16px;
      }
      /* The rank stays close to the name, whatever the gap between the columns. */
      .rank {
        margin-inline-end: calc(12px - var(--column-gap));
        text-align: end;
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }
      .row > .chip {
        justify-self: start;
      }
      .measured {
        text-align: end;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        overflow: hidden;
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
      .power-to-free {
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
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
        white-space: nowrap;
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
        background: repeating-linear-gradient(45deg, var(--secondary-text-color) 0 2px, rgba(127, 127, 127, 0.16) 2px 4px);
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
        display: block;
      }
      .list.phone .row {
        display: flex;
        gap: 8px;
      }
      .list.phone .row-title {
        flex: 1;
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-priority-list": KraftvaktPriorityList;
  }
}
