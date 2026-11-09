import {
  mdiArrowDown,
  mdiCancel,
  mdiCarElectric,
  mdiClockFast,
  mdiClockOutline,
  mdiEvStation,
  mdiFlash,
  mdiLightningBolt,
  mdiPlay,
  mdiPlus,
  mdiPowerPlugOff,
  mdiStop,
  mdiTimerOutline,
  mdiTimerSand,
} from "@mdi/js";
import { LitElement, css, html, nothing, unsafeCSS } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
  ERROR_CONFIG_INCOMPLETE,
  isCommandError,
  setRunning,
  type ApplianceStatus,
  type ChargerStatus,
  type ConfigResponse,
  type StatusSnapshot,
} from "../api";
import "../components/countdown";
import { measuredPowerW } from "../entities";
import { formatClockTime, formatEnergy, formatNumber, formatPercent, formatPower } from "../format";
import { describeIssue, pageForIssue } from "../issues";
import type { Localize, TranslationKey } from "../localize";
import { navigateToPage, PANEL_PATH } from "../navigation";
import type { HomeAssistant } from "../types";

/** The width of the waiting column in pixels. */
const WAITING_WIDTH = 120;

/** How a chip looks: its colour and its icon, or a dot without one. */
interface Chip {
  kind: "on" | "off" | "warning" | "outline" | "info";
  icon?: string;
}

const CHIP_ON: Chip = { kind: "on" };
const CHIP_OFF: Chip = { kind: "off" };
const CHIP_CHARGING: Chip = { kind: "on", icon: mdiLightningBolt };
const CHIP_NO_POWER: Chip = { kind: "warning", icon: mdiPowerPlugOff };
const CHIP_QUEUED: Chip = { kind: "off", icon: mdiTimerSand };
const CHIP_EXCLUDED: Chip = { kind: "outline", icon: mdiCancel };
const CHIP_OUTSIDE_WINDOW: Chip = { kind: "outline", icon: mdiClockOutline };
const CHIP_OVERRIDE: Chip = { kind: "info", icon: mdiClockFast };
const CHIP_FIRST_DECISION: Chip = { kind: "off", icon: mdiTimerSand };

/** An entry in the priority list: an appliance, or «EV charging» with its EV chargers. */
type PriorityEntry =
  | { kind: "appliance"; appliance: ApplianceStatus; on: boolean }
  | { kind: "ev_charging"; chargers: ChargerStatus[]; on: boolean };

/** Return the entries of the priority list in order, with «EV charging» at its place. */
function priorityEntries(status: StatusSnapshot): PriorityEntry[] {
  const entries: PriorityEntry[] = status.appliances.map((appliance) => ({
    kind: "appliance",
    appliance,
    on: appliance.on,
  }));
  if (status.ev_charging_position !== null) {
    const chargers = status.chargers;
    const on = chargers.some((charger) => charger.activated && !charger.bypassed);
    entries.splice(status.ev_charging_position, 0, { kind: "ev_charging", chargers, on });
  }
  return entries;
}

/**
 * Return the index of the entry the cut-off line goes under: the last entry
 * that is on. There is no line (-1) when nothing is on or everything is on.
 * «EV charging» is on while one of its EV chargers is activated and not bypassed.
 */
function cutOffIndex(entries: PriorityEntry[]): number {
  const last = entries.map((entry) => entry.on).lastIndexOf(true);
  return last === entries.length - 1 ? -1 : last;
}

/** Return «22» for «22:00», and the time as it is otherwise. */
function shortTime(time: string): string {
  return time.endsWith(":00") ? time.slice(0, -3) : time;
}

/** The kW steps the meter's scale may use, and how many ticks it may have at most. */
const TICK_STEPS = [1, 2, 5, 10, 20, 50];
const MAX_TICKS = 15;

/** Return the step between ticks and the end of a scale that reaches at least `reach` kW. */
function meterScale(reach: number): { step: number; end: number } {
  const step = TICK_STEPS.find((candidate) => reach / candidate <= MAX_TICKS) ?? TICK_STEPS[TICK_STEPS.length - 1];
  return { step, end: Math.ceil(reach / step) * step };
}

/** Shows how the regulation stands now, and starts and stops it. */
@customElement("kraftvakt-status-page")
export class KraftvaktStatusPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status?: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  @state() private changingRunning = false;

  @state() private runningError?: string;

  protected render() {
    if (!this.status) {
      return nothing;
    }
    const status = this.status;
    return html`
      <div class="cards">
        ${this.renderRegulationCard(status)} ${status.running ? this.renderPriorityCard(status) : nothing}
      </div>
    `;
  }

  private renderRegulationCard(status: StatusSnapshot) {
    return html`
      <ha-card class="regulation">
        <div class="card-header">
          <span>${this.localize("status.regulation")}</span>
          <span class="chip ${status.running ? "running" : "off"}">
            <span class="dot"></span>
            ${this.localize(status.running ? "status.running" : "status.stopped")}
          </span>
          ${status.running && status.safe_state
            ? html`<span class="chip alarm">${this.localize("status.safe_state_chip")}</span>`
            : nothing}
          ${status.running && status.penalty.active
            ? html`<span class="chip alarm">${this.localize("status.penalty_chip")}</span>`
            : nothing}
          <span class="spacer"></span>
          ${status.running && status.next_decision_at ? this.renderNextDecision(status, status.next_decision_at) : nothing}
        </div>
        <div class="card-content">
          ${this.runningError ? html`<ha-alert alert-type="error">${this.runningError}</ha-alert>` : nothing}
          ${status.running ? this.renderRunning(status) : this.renderStopped(status)}
        </div>
        <div class="card-actions">${this.renderStartStop(status)}</div>
      </ha-card>
    `;
  }

  private renderStartStop(status: StatusSnapshot) {
    if (status.running) {
      return html`
        <ha-button
          variant="danger"
          appearance="plain"
          .disabled=${this.changingRunning}
          @click=${() => this.changeRunning(false)}
        >
          <ha-svg-icon slot="start" .path=${mdiStop}></ha-svg-icon>
          ${this.localize("status.stop")}
        </ha-button>
      `;
    }
    return html`
      <ha-button
        .disabled=${this.changingRunning || status.missing.length > 0}
        @click=${() => this.changeRunning(true)}
      >
        <ha-svg-icon slot="start" .path=${mdiPlay}></ha-svg-icon>
        ${this.localize("status.start")}
      </ha-button>
    `;
  }

  /** What the status page shows in addition while the regulation runs. */
  private renderRunning(status: StatusSnapshot) {
    const language = this.hass.language;
    const overLimit = (value: number | null) => value !== null && value > status.power_limit_w;
    const powerNow = measuredPowerW(this.hass, this.config?.config.general.power_sensor ?? "");
    return html`
      ${status.safe_state ? this.renderSafeState(powerNow !== null) : nothing} ${status.penalty.active ? this.renderPenalty(status) : nothing}
      <div class="stats">
        ${this.renderStat("power-now", "status.power_now", formatPower(language, powerNow), this.localize("status.momentary"))}
        ${this.renderStat(
          "regulation-average",
          "status.regulation_average",
          formatPower(language, status.regulation_average_w),
          this.localize("status.average_over_seconds", { seconds: status.regulation_window_s }),
        )}
        ${this.renderStat(
          "capacity-average",
          "status.capacity_average",
          formatPower(language, status.capacity_average_w),
          this.localize("status.average_over_hour"),
          overLimit(status.capacity_average_w),
        )}
        ${this.renderStat("power-limit", "status.power_limit", formatPower(language, status.power_limit_w))}
      </div>
      ${this.renderMeter(status, powerNow)}
    `;
  }

  /** «Next decision» and a ring that empties until it, with the time as a tooltip. */
  private renderNextDecision(status: StatusSnapshot, nextDecisionAt: string) {
    const end = Date.parse(nextDecisionAt);
    const interval = status.regulation_window_s * status.regulation_interval * 1000;
    const time = formatClockTime(this.hass.language, nextDecisionAt);
    return html`
      <span class="next-decision" title=${this.localize("status.next_decision_at", { time })}>
        ${this.narrow ? nothing : this.localize("status.next_decision")}
        <kraftvakt-countdown-ring .start=${end - interval} .end=${end}></kraftvakt-countdown-ring>
      </span>
    `;
  }

  /**
   * The safe state lasts until the next decision, also after the sensor gives
   * a valid value again.
   */
  private renderSafeState(sensorBack: boolean) {
    const sensor = this.config?.config.general.power_sensor ?? "";
    const name = this.hass.states[sensor]?.attributes.friendly_name ?? sensor;
    return html`
      <ha-alert alert-type=${sensorBack ? "info" : "error"} .title=${this.localize("status.safe_state_title")}>
        ${this.localize(sensorBack ? "status.safe_state_back_text" : "status.safe_state_text", { sensor: name })}
      </ha-alert>
    `;
  }

  private renderPenalty(status: StatusSnapshot) {
    const energy = formatEnergy(this.hass.language, Math.max(0, status.penalty.overconsumption_wh));
    const recovery = status.penalty.recovery_started ? "status.recovery_started" : "status.recovery_not_started";
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("status.penalty_title")}>
        ${this.localize("status.penalty_text")}
        <div class="penalty-details">${this.localize("status.overconsumption_left", { energy })} · ${this.localize(recovery)}</div>
      </ha-alert>
    `;
  }

  private renderStat(swatch: string, label: Parameters<Localize>[0], value: string, period?: string, alarm = false) {
    return html`
      <div class="stat">
        <div class="stat-label">${swatch ? html`<span class="swatch ${swatch}"></span>` : nothing}${this.localize(label)}</div>
        <div class="stat-value ${alarm ? "alarm" : ""}">${value} <small>kW</small></div>
        ${period ? html`<div class="stat-period">${period}</div>` : nothing}
      </div>
    `;
  }

  /** The averages as bars against the power limit. */
  /**
   * The consumption now as a bar, with a triangle for each average and the
   * power limit, and a scale in whole kW with a value at every second tick
   * (every third on a narrow screen).
   */
  private renderMeter(status: StatusSnapshot, powerNowW: number | null) {
    const kilowatt = (watt: number | null) => (watt === null ? null : watt / 1000);
    const limit = status.power_limit_w / 1000;
    const powerNow = kilowatt(powerNowW);
    const capacityAverage = kilowatt(status.capacity_average_w);
    const regulationAverage = kilowatt(status.regulation_average_w);
    const values = [powerNow, capacityAverage, regulationAverage];
    const { step, end } = meterScale(Math.max(limit * 1.2, ...values.map((value) => value ?? 0)));
    const percent = (value: number) => `${(100 * Math.min(value, end)) / end}%`;
    const language = this.hass.language;
    const ticks = Array.from({ length: end / step + 1 }, (_, index) => index * step);
    const labelEvery = this.narrow ? 3 : 2;
    const labelled = ticks.filter((_, index) => index % labelEvery === 0);
    const marker = (kind: string, label: Parameters<Localize>[0], value: number | null) =>
      value === null
        ? nothing
        : html`<span
            class="marker ${kind}"
            style="left: ${percent(value)}"
            title="${this.localize(label)} ${formatNumber(language, value, 2)} kW"
          ></span>`;
    return html`
      <div class="meter">
        <div class="markers">
          ${marker("power-limit", "status.power_limit", limit)}
          ${marker("capacity-average", "status.capacity_average", capacityAverage)}
          ${marker("regulation-average", "status.regulation_average", regulationAverage)}
        </div>
        <div class="bar">
          ${powerNow === null ? nothing : html`<div class="fill power-now" style="width: ${percent(powerNow)}"></div>`}
        </div>
        <div class="ticks">${ticks.map((tick) => html`<span style="left: ${percent(tick)}"></span>`)}</div>
        <div class="scale">
          ${labelled.map(
            (tick, index) =>
              html`<span class=${tick === 0 ? "start" : tick === end ? "end" : ""} style="left: ${percent(tick)}"
                >${formatNumber(language, tick, 0)}${index === labelled.length - 1 ? " kW" : ""}</span
              >`,
          )}
        </div>
      </div>
    `;
  }

  /**
   * The appliances in order of priority, with the EV chargers grouped at the
   * place of «EV charging», and a line under the last entry that is on.
   */
  private renderPriorityCard(status: StatusSnapshot) {
    const entries = priorityEntries(status);
    const cutAfter = cutOffIndex(entries);
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("status.priority_list")}</span>
        </div>
        ${entries.length === 0
          ? html`<div class="card-content empty">${this.localize("status.no_appliances")}</div>`
          : html`<div class="list">
              ${entries.map(
                (entry, index) => html`
                  ${entry.kind === "appliance"
                    ? this.renderApplianceRow(entry.appliance, index + 1)
                    : this.renderEvCharging(entry.chargers, index + 1)}
                  ${index === cutAfter ? this.renderCutOff(status) : nothing}
                `,
              )}
            </div>`}
      </ha-card>
    `;
  }

  private renderApplianceRow(appliance: ApplianceStatus, rank: number) {
    return html`
      <div class="row ${appliance.on ? "" : "off"}">
        <span class="rank">${rank}</span>
        <div class="row-title">
          ${this.renderApplianceIcon(appliance)}<span class="name">${appliance.name}</span>
          ${appliance.variant ? html`<span class="variant">${appliance.variant}</span>` : nothing}
        </div>
        <span></span>
        ${this.renderWaiting(appliance, mdiTimerOutline, "status.delayed_turn_on", "status.waiting_ends_at")}
        ${appliance.on
          ? this.renderChip(CHIP_ON, "status.on", "status.on")
          : this.renderChip(CHIP_OFF, "status.off", "status.off")}
      </div>
    `;
  }

  /** The icon of the appliance's entity, coloured like Home Assistant colours a switch that is on. */
  private renderApplianceIcon(appliance: ApplianceStatus) {
    const entityId = this.config?.config.appliances.find((item) => item.id === appliance.id)?.entity_id;
    const stateObj = entityId ? this.hass.states[entityId] : undefined;
    const on = appliance.on ? "on" : "";
    return stateObj
      ? html`<ha-state-icon class="device-icon ${on}" .hass=${this.hass} .stateObj=${stateObj}></ha-state-icon>`
      : html`<ha-svg-icon class="device-icon ${on}" .path=${mdiFlash}></ha-svg-icon>`;
  }

  /** The «EV charging» entry, with each EV charger in the current charging priority under it. */
  private renderEvCharging(chargers: ChargerStatus[], rank: number) {
    const charging = chargers.filter((charger) => charger.charging).length;
    return html`
      <div class="row group">
        <span class="rank">${rank}</span>
        <div class="row-title">
          <ha-svg-icon class="ev-icon" .path=${mdiCarElectric}></ha-svg-icon>
          <span class="name">${this.localize("status.ev_charging")}</span>
          ${chargers.length === 0 ? html`<span class="row-sub">${this.localize("status.no_chargers")}</span>` : nothing}
        </div>
        ${chargers.length === 0
          ? html`<span></span>`
          : html`<span
              class="charging-count"
              title=${this.localize("status.chargers_charging", { charging, total: chargers.length })}
            >
              <ha-svg-icon .path=${mdiLightningBolt}></ha-svg-icon>${charging} / ${chargers.length}
            </span>`}
      </div>
      ${chargers.map(
        (charger) => html`
          <div class="row charger ${charger.activated ? "" : "off"}">
            <span class="rank"></span>
            <div class="row-title">
              <ha-svg-icon class="device-icon ev ${charger.activated ? "on" : ""}" .path=${mdiEvStation}></ha-svg-icon>
              <span class="name">${charger.name}</span>
            </div>
            ${this.renderAmperes(charger)}
            ${this.renderWaiting(charger, mdiPlus, "status.delayed_turn_on", "status.next_ampere_at")}
            ${this.renderChargerChip(charger)}
          </div>
        `,
      )}
    `;
  }

  /**
   * An icon and a bar that empties from when the waiting started until the
   * decision that ends it. Left out on a narrow screen.
   */
  private renderWaiting(
    item: ApplianceStatus | ChargerStatus,
    icon: string,
    label: TranslationKey,
    endsAt: TranslationKey,
  ) {
    if (this.narrow) {
      return nothing;
    }
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

  /**
   * The current, and one bar per ampere from the minimum to the maximum,
   * filled up to the current. The current is left out on a narrow screen.
   */
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
        ${this.narrow
          ? nothing
          : html`<span class="current ${charger.current_a === null ? "none" : ""}"
              >${charger.current_a === null ? "–" : this.localize("status.amperes", { current: charger.current_a })}</span
            >`}
        <span class="ampere-steps ${steps > 16 ? "small" : ""}">
          ${Array.from({ length: steps }, (_, index) => html`<span class="ampere ${index < on ? filled : ""}"></span>`)}
        </span>
      </span>
    `;
  }

  /** The chip with the most important reason why the EV charger stands as it does. */
  private renderChargerChip(charger: ChargerStatus) {
    const window = this.chargerConfig(charger)?.charging_window;
    if (charger.excluded === null) {
      return this.renderChip(CHIP_FIRST_DECISION, "status.chip_first_decision", "status.first_decision");
    }
    if (charger.excluded) {
      return this.renderChip(CHIP_EXCLUDED, "status.chip_excluded", "status.excluded");
    }
    if (!charger.allowed && window) {
      const short = { start: shortTime(window.start), end: shortTime(window.end) };
      return this.renderChip(CHIP_OUTSIDE_WINDOW, "status.chip_window", "status.outside_window", short, { ...window });
    }
    if (charger.bypassed) {
      return this.renderChip(CHIP_NO_POWER, "status.chip_no_power", "status.bypassed");
    }
    if (charger.waiting) {
      return this.renderChip(CHIP_QUEUED, "status.chip_queued", "status.waiting_charger");
    }
    if (charger.window_overridden && charger.activated) {
      return this.renderChip(CHIP_OVERRIDE, "status.chip_override", "status.window_overridden");
    }
    if (charger.charging) {
      const current = { current: charger.current_a ?? 0 };
      return this.renderChip(CHIP_CHARGING, "status.chip_charging", "status.charging_at", {}, current);
    }
    return charger.activated
      ? this.renderChip(CHIP_ON, "status.activated", "status.activated_not_charging")
      : this.renderChip(CHIP_OFF, "status.deactivated", "status.deactivated");
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
  private renderCutOff(status: StatusSnapshot) {
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
    return this.config?.config.charging.chargers.find((item) => item.id === charger.id);
  }

  private renderStopped(status: StatusSnapshot) {
    if (status.missing.length === 0) {
      return html`<ha-alert alert-type="info">${this.localize("status.stopped_info")}</ha-alert>`;
    }
    return html`
      <ha-alert alert-type="warning" .title=${this.localize("status.incomplete_title")}>
        <ul class="missing">
          ${status.missing.map((issue) => {
            const page = pageForIssue(issue);
            return html`
              <li>
                ${describeIssue(issue, this.config, this.localize)}
                <a href="${PANEL_PATH}/${page}" @click=${(event: Event) => this.openPage(event, page)}>
                  ${this.localize(`tabs.${page}`)}
                </a>
              </li>
            `;
          })}
        </ul>
      </ha-alert>
    `;
  }

  /** Start or stop the regulation. The new status comes with the status subscription. */
  private async changeRunning(running: boolean): Promise<void> {
    this.changingRunning = true;
    this.runningError = undefined;
    try {
      await setRunning(this.hass, running);
    } catch (error) {
      this.runningError =
        isCommandError(error) && error.code === ERROR_CONFIG_INCOMPLETE
          ? this.localize("status.start_refused")
          : this.localize("panel.error", { message: isCommandError(error) ? error.message : String(error) });
    } finally {
      this.changingRunning = false;
    }
  }

  private openPage(event: Event, page: Parameters<typeof navigateToPage>[0]): void {
    event.preventDefault();
    navigateToPage(page);
  }

  static styles = css`
    :host {
      display: block;
      --kraftvakt-grid-color: var(--energy-grid-consumption-color, #488fc2);
      --kraftvakt-now-color: var(--secondary-text-color);
      --kraftvakt-ev-color: var(--teal-color, #009688);
      --kraftvakt-on-color: var(--state-active-color, var(--amber-color, #ffc107));
    }
    .cards {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 16px;
    }
    :host([narrow]) .cards {
      gap: 8px;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      min-height: 40px;
      padding: 12px 16px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .spacer {
      flex: 1;
    }
    .card-content {
      display: grid;
      gap: 16px;
      padding: 0 16px 16px;
    }
    .card-content:empty {
      display: none;
    }
    .card-actions {
      display: flex;
      justify-content: flex-end;
      padding: 8px 16px;
      border-top: 1px solid var(--divider-color);
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      font-weight: 500;
      line-height: 20px;
      white-space: nowrap;
      background: var(--kraftvakt-chip-off-background, rgba(127, 127, 127, 0.16));
      color: var(--secondary-text-color);
    }
    .chip .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .chip.running,
    .chip.on {
      background: rgba(var(--rgb-success-color, 67, 160, 71), 0.16);
      color: var(--success-color, #43a047);
    }
    .chip.alarm {
      background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
      color: var(--error-color, #db4437);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }
    .stat {
      padding: 10px 12px;
      border-radius: var(--ha-border-radius-lg, 12px);
      background: var(--secondary-background-color);
    }
    .stat-label {
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value {
      font-size: 26px;
    }
    .stat-period {
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .stat-value small {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    :host([narrow]) .stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    :host([narrow]) .stat {
      padding: 8px;
    }
    :host([narrow]) .stat-value {
      font-size: 20px;
    }
    .stat-value.alarm {
      color: var(--error-color);
    }
    .swatch {
      display: inline-block;
      flex: none;
    }
    .swatch.power-now {
      width: 12px;
      height: 8px;
      border-radius: 4px;
      background: var(--kraftvakt-now-color);
    }
    .swatch:not(.power-now),
    .meter .marker {
      width: 0;
      height: 0;
      border-inline: 5px solid transparent;
      border-top: 7px solid var(--marker-color);
    }
    .capacity-average {
      --marker-color: var(--kraftvakt-grid-color);
    }
    .regulation-average {
      --marker-color: var(--primary-text-color);
    }
    .power-limit {
      --marker-color: var(--error-color);
    }
    .meter .markers {
      position: relative;
      height: 9px;
    }
    .meter .marker {
      position: absolute;
      top: 0;
      transform: translateX(-50%);
      transition: left 0.6s ease;
    }
    .meter .bar {
      position: relative;
      height: 12px;
      overflow: hidden;
      border-radius: 6px;
      background: var(--secondary-background-color);
    }
    .meter .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 6px;
      background: var(--kraftvakt-now-color);
      transition: width 0.6s ease;
    }
    .meter .ticks {
      position: relative;
      height: 5px;
      margin-top: 2px;
    }
    .meter .ticks span {
      position: absolute;
      top: 0;
      width: 1px;
      height: 100%;
      margin-left: -0.5px;
      background: var(--secondary-text-color);
      opacity: 0.6;
    }
    .meter .scale {
      position: relative;
      height: 18px;
      margin-top: 2px;
      font-size: var(--ha-font-size-s, 12px);
      color: var(--secondary-text-color);
    }
    .meter .scale span {
      position: absolute;
      transform: translateX(-50%);
      white-space: nowrap;
    }
    .meter .scale .start {
      transform: none;
    }
    .meter .scale .end {
      transform: translateX(-100%);
    }
    .penalty-details {
      margin-top: 8px;
    }
    .empty {
      color: var(--secondary-text-color);
    }
    .list {
      display: grid;
      grid-template-columns: 24px minmax(0, 2fr) minmax(max-content, 1.3fr) ${unsafeCSS(WAITING_WIDTH)}px max-content;
      column-gap: 12px;
    }
    :host([narrow]) .list {
      grid-template-columns: 20px minmax(0, 1fr) max-content max-content;
      column-gap: 8px;
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
    .row.charger .row-title {
      padding-inline-start: 24px;
    }
    :host([narrow]) .row.charger .row-title {
      padding-inline-start: 16px;
    }
    .rank {
      text-align: center;
      color: var(--secondary-text-color);
    }
    .row > .chip {
      justify-self: start;
    }
    :host([narrow]) .row > .chip {
      justify-self: end;
    }
    .chip ha-svg-icon {
      --mdc-icon-size: 16px;
    }
    .chip.warning {
      background: rgba(var(--rgb-warning-color, 255, 166, 0), 0.16);
      color: var(--warning-color, #ffa600);
    }
    .chip.outline {
      background: none;
      box-shadow: inset 0 0 0 1px var(--divider-color);
    }
    .chip.info {
      background: rgba(var(--rgb-info-color, 3, 155, 229), 0.16);
      color: var(--info-color, #039be5);
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
    .next-decision {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
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
    .amperes .current {
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
    :host([narrow]) .ampere-steps {
      gap: 1px;
    }
    :host([narrow]) .ampere {
      width: 2px;
      height: 12px;
    }
    .row-title {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px 10px;
      overflow-wrap: anywhere;
    }
    .row-title ha-svg-icon,
    .row-title ha-state-icon {
      flex: none;
      --mdc-icon-size: 20px;
      color: var(--state-inactive-color, var(--secondary-text-color));
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
      color: var(--secondary-text-color);
      font-size: var(--ha-font-size-s, 12px);
    }
    .variant {
      display: inline-block;
      padding: 0 8px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
      color: var(--primary-color);
    }
    ul.missing {
      margin: 6px 0 0;
      padding-inline-start: 18px;
    }
    ul.missing a {
      color: var(--primary-color);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-status-page": KraftvaktStatusPage;
  }
}
