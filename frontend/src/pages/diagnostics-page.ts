import { LitElement, css, html, nothing, svg, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
  subscribeDiagnostics,
  type Charger,
  type ConfigResponse,
  type DecisionCommand,
  type DecisionRecord,
  type DiagnosticsEvent,
  type Measurement,
  type StatusSnapshot,
} from "../api";
import { applianceRows, chargerRows, lanes, logRows, mergePart, repeatsDue, type Lanes, type LogRow, type Segment } from "../diagnostics";
import { formatClockTime, formatDateTime, formatDuration, formatMoment, formatNumber, formatPower } from "../format";
import type { Localize, TranslationKey } from "../localize";
import { cardHeaderStyles, chipStyles } from "../status-styles";
import type { HomeAssistant } from "../types";

type LogFilter = "all" | "commands" | "failed";

/** One lane in the chart: an appliance or an EV charger, in priority order. */
interface LaneRow {
  id: string;
  name: string;
  essential: boolean;
  charger?: Charger;
}

/** What Kraftvakt holds in memory: whether the inputs are healthy, the last hour, and the commands and failed actions. */
@customElement("kraftvakt-diagnostics-page")
export class KraftvaktDiagnosticsPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) status?: StatusSnapshot;

  @property({ attribute: false }) config?: ConfigResponse;

  @state() private diagnostics?: DiagnosticsEvent;

  @state() private measurements: Measurement[] = [];

  @state() private decisions: DecisionRecord[] = [];

  @state() private error?: unknown;

  @state() private filter: LogFilter = "all";

  /** The key of the log row that is open, whose time is marked in the chart. */
  @state() private openRow?: { key: string; time: string };

  @state() private hoverMs?: number;

  @state() private chartWidth = 0;

  private unsubscribe?: Promise<() => Promise<void>>;

  private readonly chartResize = new ResizeObserver(([entry]) => (this.chartWidth = entry.contentRect.width));

  connectedCallback(): void {
    super.connectedCallback();
    this.subscribe();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this.unsubscribe?.then((unsubscribe) => unsubscribe()).catch(() => undefined);
    this.unsubscribe = undefined;
    this.chartResize.disconnect();
  }

  protected willUpdate(changed: PropertyValues<this>): void {
    if (changed.has("hass")) {
      this.subscribe();
    }
  }

  protected updated(): void {
    const chart = this.renderRoot.querySelector(".chart");
    if (chart) {
      this.chartResize.observe(chart);
    }
  }

  private subscribe(): void {
    if (!this.hass || this.unsubscribe) {
      return;
    }
    this.unsubscribe = subscribeDiagnostics(this.hass, (event) => this.received(event));
    this.unsubscribe.catch((error: unknown) => {
      this.error = error;
      this.unsubscribe = undefined;
    });
  }

  private received(event: DiagnosticsEvent): void {
    this.diagnostics = event;
    this.measurements = mergePart(this.measurements, event.measurements, (measurement) => measurement.start);
    this.decisions = mergePart(this.decisions, event.decisions, (decision) => decision.time);
    this.error = undefined;
  }

  protected render() {
    if (this.error !== undefined) {
      return html`<ha-alert alert-type="error">${this.localize("panel.error", { message: String(this.error) })}</ha-alert>`;
    }
    if (!this.diagnostics || !this.status || !this.config) {
      return nothing;
    }
    const now = Date.now();
    const history = lanes(this.decisions, this.diagnostics.commands_before_decisions, this.status, this.diagnostics.started_at, now);
    return html` <div class="cards">${this.renderHealth(this.diagnostics, this.status, this.config)} ${this.renderTimeline(history, now)} ${this.renderLog()}</div> `;
  }

  private renderHealth(diagnostics: DiagnosticsEvent, status: StatusSnapshot, config: ConfigResponse) {
    const language = this.hass.language;
    const general = config.config.general;
    const sensor = diagnostics.power_sensor;
    const seconds = (value: number | null) => (value === null ? "–" : this.localize("diagnostics.seconds", { seconds: formatNumber(language, value, 0) }));
    const interval =
      sensor.reported_interval_s === null
        ? seconds(sensor.update_interval_s)
        : this.localize("diagnostics.reports_every", { seconds: formatNumber(language, sensor.reported_interval_s, 1) });
    const missed = sensor.last_missed_windows;
    const failed = diagnostics.failed_actions;
    const repeats = repeatsDue(diagnostics.repeats_due_at);
    const running = diagnostics.started_at !== null;
    return html`
      <div class="tiles">
        ${this.renderTile(
          "diagnostics.power_sensor",
          !sensor.valid ? "alarm" : sensor.reported_interval_s !== null ? "warning" : "ok",
          this.localize(sensor.valid ? "diagnostics.valid" : "diagnostics.not_valid"),
          [
            ["diagnostics.update_interval", interval],
            ["diagnostics.stored_interval", seconds(general.power_sensor_interval_s)],
            [
              "diagnostics.regulation_window",
              general.regulation_window_updates === null || general.power_sensor_interval_s === null
                ? "–"
                : this.localize("diagnostics.window_updates", {
                    seconds: formatNumber(language, status.regulation_window_s, 0),
                    updates: general.regulation_window_updates,
                    interval: formatNumber(language, general.power_sensor_interval_s, 0),
                  }),
            ],
            [
              "diagnostics.last_missed_windows",
              missed === null ? this.localize("diagnostics.none") : `${formatMoment(language, missed.start)}–${formatClockTime(language, missed.end)}`,
            ],
          ],
        )}
        ${this.renderTile("diagnostics.actions", failed.length > 0 ? "warning" : "ok", this.localize("diagnostics.failed_count", { count: failed.length }), [
          ["diagnostics.last_failed", failed.length > 0 ? formatMoment(language, failed[failed.length - 1].time) : this.localize("diagnostics.none")],
          ["diagnostics.commands_waiting", String(diagnostics.queued_commands)],
          ["diagnostics.action_timeout", seconds(general.action_timeout_s)],
        ])}
        ${this.renderTile(
          "status.regulation",
          !running ? "off" : status.safe_state || status.penalty.active ? "alarm" : "ok",
          diagnostics.started_at === null
            ? this.localize("status.stopped")
            : this.localize("diagnostics.running_for", { duration: formatDuration(language, Date.now() - Date.parse(diagnostics.started_at)) }),
          [
            ...(diagnostics.started_at === null ? [] : ([["diagnostics.started", formatDateTime(language, diagnostics.started_at)]] as [TranslationKey, string][])),
            ["status.safe_state_title", this.localize(status.safe_state ? "diagnostics.yes" : "diagnostics.no")],
            ["status.penalty_title", this.localize(status.penalty.active ? "diagnostics.yes" : "diagnostics.no")],
            ["diagnostics.overconsumption", this.localize("diagnostics.watt_hours", { energy: formatNumber(language, Math.max(0, status.penalty.overconsumption_wh), 0) })],
          ],
        )}
        ${this.renderTile(
          "diagnostics.command_repeat",
          "off",
          repeats.length > 0 ? this.localize("diagnostics.next_at", { time: formatClockTime(language, repeats[0].dueAt) }) : this.localize("diagnostics.none"),
          repeats.slice(0, 3).map((repeat) => [this.itemName(repeat.type, repeat.id), formatClockTime(language, repeat.dueAt)]),
        )}
      </div>
    `;
  }

  private renderTile(title: TranslationKey, health: "ok" | "warning" | "alarm" | "off", value: string, rows: [TranslationKey | string, string][]) {
    return html`
      <ha-card class="tile">
        <div class="tile-title"><span class="dot ${health}"></span>${this.localize(title)}</div>
        <div class="tile-value">${value}</div>
        <dl>
          ${rows.map(
            ([label, text]) =>
              html`<dt>${label.startsWith("diagnostics.") || label.startsWith("status.") ? this.localize(label as TranslationKey) : label}</dt>
                <dd>${text}</dd>`,
          )}
        </dl>
      </ha-card>
    `;
  }

  private renderTimeline(history: Lanes, now: number) {
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("diagnostics.timeline")}</span>
        </div>
        <div class="legend">
          <span><i class="swatch consumption"></i>${this.localize("diagnostics.consumption")}</span>
          <span><i class="swatch line"></i>${this.localize("status.regulation_average")}</span>
          <span><i class="swatch line tariff"></i>${this.localize("status.tariff_average")}</span>
          <span><i class="swatch line limit"></i>${this.localize("status.power_limit")}</span>
          <span><i class="swatch waiting"></i>${this.localize("diagnostics.waiting")}</span>
          <span><i class="swatch unknown"></i>${this.localize("diagnostics.not_known")}</span>
          <span><i class="swatch oldest"></i>${this.localize("diagnostics.oldest_decision")}</span>
        </div>
        <div class="chart" @pointermove=${this.pointerMoved} @pointerleave=${() => (this.hoverMs = undefined)}>
          ${this.chartWidth > 0 ? this.renderChart(history, now) : nothing} ${this.renderTooltip(now)}
        </div>
      </ha-card>
    `;
  }

  /** A chart on a phone, by the chart's own width, since Home Assistant's sidebar may take much of the viewport. */
  private get compactChart(): boolean {
    return this.chartWidth < 560;
  }

  /** The horizontal scale of the chart and the lanes, which share it. */
  private scale(now: number) {
    const width = this.chartWidth;
    const left = this.compactChart ? 96 : 176;
    const right = 8;
    const start = now - 3_600_000;
    const x = (moment: number) => left + ((Math.min(Math.max(moment, start), now) - start) / (now - start)) * (width - left - right);
    return { width, left, right, start, x };
  }

  private renderChart(history: Lanes, now: number) {
    const { width, left, right, start, x } = this.scale(now);
    const language = this.hass.language;
    const status = this.status!;
    const height = this.compactChart ? 160 : 200;
    const top = 8;
    const bottom = 22;
    const visible = this.measurements.filter((_, index) => (Date.parse(this.measurements[index + 1]?.start ?? "") || now) > start);
    const highest = Math.max(status.power_limit_w, ...visible.map((measurement) => measurement.power_w), ...this.decisions.map((decision) => decision.regulation_average_w ?? 0));
    const stepKw = highest > 20_000 ? 5 : 2;
    const topKw = Math.ceil((highest * 1.1) / 1000 / stepKw) * stepKw;
    const y = (watt: number) => top + (1 - watt / 1000 / topKw) * (height - top - bottom);
    const area = visible
      .map((measurement, index) => {
        const from = x(Date.parse(measurement.start));
        const to = x(Date.parse(visible[index + 1]?.start ?? "") || now);
        return `L${from},${y(measurement.power_w)}L${to},${y(measurement.power_w)}`;
      })
      .join("");
    const firstX = visible.length > 0 ? x(Date.parse(visible[0].start)) : x(now);
    const window = status.regulation_window_s * 1000;
    const averages = this.decisions.filter((decision) => decision.regulation_average_w !== null && Date.parse(decision.time) > start);
    const regulationPath = averages
      .map((decision, index) => {
        const end = Date.parse(decision.time);
        return `${index === 0 ? "M" : "L"}${x(end - window)},${y(decision.regulation_average_w!)}L${x(end)},${y(decision.regulation_average_w!)}`;
      })
      .join("");
    const tariffPath = averages
      .filter((decision) => decision.tariff_average_w !== null)
      .map((decision, index) => `${index === 0 ? "M" : "L"}${x(Date.parse(decision.time))},${y(decision.tariff_average_w!)}`)
      .join("");
    const tickStep = (this.compactChart ? 20 : 10) * 60_000;
    const ticks: number[] = [];
    for (let tick = Math.ceil(start / tickStep) * tickStep; tick < now - tickStep / 2; tick += tickStep) {
      ticks.push(tick);
    }
    const kwTicks = Array.from({ length: topKw / stepKw + 1 }, (_, index) => index * stepKw);
    const oldest = this.decisions[0] ? Date.parse(this.decisions[0].time) : undefined;
    const marked = this.openRow && Date.parse(this.openRow.time);
    return html`
      <svg class="power" width=${width} height=${height} viewBox="0 0 ${width} ${height}" role="img" aria-label=${this.localize("diagnostics.chart_label")}>
        ${kwTicks.map(
          (kw) => svg`
            <line class="grid" x1=${left} x2=${width - right} y1=${y(kw * 1000)} y2=${y(kw * 1000)}></line>
            <text x=${left - 6} y=${y(kw * 1000) + 4} text-anchor="end">${kw === topKw ? `${kw} kW` : kw}</text>
          `,
        )}
        ${ticks.map((tick) => svg`<text x=${x(tick)} y=${height - 6} text-anchor="middle">${new Date(tick).toLocaleTimeString(language, { hour: "2-digit", minute: "2-digit" })}</text>`)}
        <text x=${width - right} y=${height - 6} text-anchor="end">${this.localize("diagnostics.now")}</text>
        ${area ? svg`<path class="consumption" d="M${firstX},${y(0)}${area}L${x(now)},${y(0)}Z"></path>` : nothing}
        <path class="tariff" d=${tariffPath}></path>
        <path class="regulation" d=${regulationPath}></path>
        <line class="limit" x1=${left} x2=${width - right} y1=${y(status.power_limit_w)} y2=${y(status.power_limit_w)}></line>
        ${oldest !== undefined && oldest > start ? svg`<line class="oldest" x1=${x(oldest)} x2=${x(oldest)} y1=${top} y2=${height - bottom}></line>` : nothing}
        ${this.renderCursor(marked, top, height - bottom, x, start)} ${this.renderCursor(this.hoverMs, top, height - bottom, x, start, "hover")}
      </svg>
      ${this.renderLanes(history, now)}
    `;
  }

  private renderCursor(moment: number | undefined, from: number, to: number, x: (moment: number) => number, start: number, className = "marked") {
    return moment !== undefined && moment > start ? svg`<line class=${className} x1=${x(moment)} x2=${x(moment)} y1=${from} y2=${to}></line>` : nothing;
  }

  private renderLanes(history: Lanes, now: number) {
    const { width, start, x } = this.scale(now);
    const rows = this.laneRows();
    const rowHeight = 26;
    const height = rowHeight * rows.length + 2;
    const hover = this.hoverMs;
    const marked = this.openRow && Date.parse(this.openRow.time);
    const bar = (segment: Segment<unknown>, top: number, share = 1, className = "on") => {
      const barHeight = Math.max(2, (rowHeight - 10) * share);
      return svg`<rect class=${className} x=${x(segment.start)} y=${top + 5 + (rowHeight - 10 - barHeight)} width=${Math.max(1.5, x(segment.end) - x(segment.start))} height=${barHeight}></rect>`;
    };
    return html`
      <svg class="lanes" width=${width} height=${height} viewBox="0 0 ${width} ${height}" role="img" aria-label=${this.localize("diagnostics.lanes_label")}>
        <defs>
          <pattern id="unknown" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
            <line x1="0" y1="0" x2="0" y2="6" class="unknown-line"></line>
          </pattern>
          <pattern id="waiting" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="5" class="waiting-line"></line>
          </pattern>
        </defs>
        ${rows.map((row, index) => {
          const top = index * rowHeight + 1;
          const known: Segment<unknown>[] = row.charger ? (history.chargers[row.id] ?? []) : (history.appliances[row.id] ?? []);
          const charger = row.charger;
          return svg`
            ${row.essential ? svg`<rect class="essential" x="0" y=${top} width=${width} height=${rowHeight}></rect>` : nothing}
            <line class="row-line" x1="0" x2=${width} y1=${top} y2=${top}></line>
            <text class="lane-name" x="4" y=${top + rowHeight / 2 + 4}>${this.shortName(row.name)}<title>${row.name}</title></text>
            <rect class="unknown" x=${x(start)} y=${top + 3} width=${x(now) - x(start)} height=${rowHeight - 6}></rect>
            ${known.map((segment) => svg`<rect class="known" x=${x(segment.start)} y=${top + 3} width=${Math.max(0, x(segment.end) - x(segment.start))} height=${rowHeight - 6}></rect>`)}
            ${
              charger
                ? (history.chargers[row.id] ?? []).map((segment) =>
                    segment.value === null
                      ? nothing
                      : bar(segment, top, (segment.value - charger.min_current_a + 1) / (charger.max_current_a - charger.min_current_a + 1), "current"),
                  )
                : (history.appliances[row.id] ?? []).map((segment) => (segment.value ? bar(segment, top) : nothing))
            }
            ${(history.waiting[row.id] ?? []).map((segment) => bar(segment, top, 1, "waiting"))}
          `;
        })}
        ${this.renderCursor(marked, 0, height, x, start)} ${this.renderCursor(hover, 0, height, x, start, "hover")}
      </svg>
    `;
  }

  private shortName(name: string): string {
    const longest = this.compactChart ? 11 : 22;
    return name.length > longest ? `${name.slice(0, longest - 1)}…` : name;
  }

  private laneRows(): LaneRow[] {
    const chargers = new Map((this.config?.config.charger_groups ?? []).flatMap((group) => group.chargers).map((charger) => [charger.id, charger]));
    return this.status!.priority.flatMap((row) =>
      row.type === "appliance"
        ? [{ id: row.id, name: row.name, essential: row.essential }]
        : row.chargers.map((charger) => ({ id: charger.id, name: charger.name, essential: false, charger: chargers.get(charger.id) })),
    );
  }

  private pointerMoved(event: PointerEvent): void {
    const chart = event.currentTarget as HTMLElement;
    const { width, left, right, start } = this.scale(Date.now());
    const offset = event.clientX - chart.getBoundingClientRect().left;
    this.hoverMs = offset < left || offset > width - right ? undefined : start + ((offset - left) / (width - left - right)) * (Date.now() - start);
  }

  private renderTooltip(now: number) {
    const moment = this.hoverMs;
    if (moment === undefined) {
      return nothing;
    }
    const language = this.hass.language;
    const measurement = [...this.measurements].reverse().find((item) => Date.parse(item.start) <= moment);
    const window = (this.status?.regulation_window_s ?? 0) * 1000;
    const decision = this.decisions.find((item) => Date.parse(item.time) >= moment && Date.parse(item.time) - window < moment);
    const { x, width } = this.scale(now);
    const position = x(moment);
    const style = position > width / 2 ? `right: ${width - position + 12}px` : `left: ${position + 12}px`;
    return html`
      <div class="tooltip" style=${style}>
        <b>${new Date(moment).toLocaleTimeString(language)}</b>
        <div>${this.localize("diagnostics.consumption")}: ${measurement ? `${formatPower(language, measurement.power_w)} kW` : "–"}</div>
        ${
          decision
            ? html`
                <div class="tooltip-decision">
                  <b>${this.localize("diagnostics.decision_at", { time: formatClockTime(language, decision.time) })}</b>
                  <div>${this.localize("status.regulation_average")}: ${formatPower(language, decision.regulation_average_w)} kW</div>
                  <div>${this.localize("status.tariff_average")}: ${formatPower(language, decision.tariff_average_w)} kW</div>
                  ${decision.commands.map((command) => html`<div>${this.commandText(command)}</div>`)}
                </div>
              `
            : html`<div>${this.localize("diagnostics.no_decision_kept")}</div>`
        }
      </div>
    `;
  }

  private renderLog() {
    const rows = logRows(this.decisions, this.diagnostics?.failed_actions ?? []).filter((row) => this.filter === "all" || (this.filter === "failed") === "failed" in row);
    const language = this.hass.language;
    return html`
      <ha-card>
        <div class="card-header">
          <span>${this.localize("diagnostics.event_log")}</span>
          <span class="spacer"></span>
          <span class="toggles">
            ${(["all", "commands", "failed"] as const).map(
              (filter) => html`
                <button class="toggle" aria-pressed=${filter === this.filter} @click=${() => (this.filter = filter)}>${this.localize(`diagnostics.filter_${filter}`)}</button>
              `,
            )}
          </span>
        </div>
        ${
          rows.length === 0
            ? html`<p class="description">${this.localize("diagnostics.no_events")}</p>`
            : html`
                <div class="table">
                  <table>
                    <tbody>
                      ${rows.map((row) => this.renderLogRow(row, language))}
                    </tbody>
                  </table>
                </div>
              `
        }
        <div class="card-footer">
          <span>${this.localize("diagnostics.log_kept")}</span>
          <a href="/config/integrations/integration/kraftvakt">${this.localize("diagnostics.download")}</a>
        </div>
      </ha-card>
    `;
  }

  private renderLogRow(row: LogRow, language: string) {
    const key = `${row.time} ${"failed" in row ? row.failed.action : JSON.stringify(row.command)}`;
    const open = this.openRow?.key === key;
    const toggle = () => (this.openRow = open ? undefined : { key, time: row.time });
    const kind = "failed" in row ? "failed" : this.commandKind(row.command);
    return html`
      <tr
        class="event ${open ? "open" : ""}"
        tabindex="0"
        @click=${toggle}
        @keydown=${(event: KeyboardEvent) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggle();
          }
        }}
      >
        <td class="time">${formatClockTime(language, row.time)}</td>
        <td class="kind"><span class="chip ${kind}">${this.localize(`diagnostics.kind_${kind}`)}</span></td>
        <td>${"failed" in row ? row.failed.action : this.commandText(row.command)}</td>
      </tr>
      ${
        open
          ? html`<tr class="details">
              <td></td>
              <td colspan="2">${"failed" in row ? this.renderFailed(row.failed.error) : this.renderDecision(row.decision)}</td>
            </tr>`
          : nothing
      }
    `;
  }

  private renderFailed(error: string) {
    return html`<dl class="facts">
      <dt>${this.localize("diagnostics.error")}</dt>
      <dd>${error}</dd>
    </dl>`;
  }

  private renderDecision(decision: DecisionRecord) {
    const language = this.hass.language;
    const waiting = decision.waiting;
    const yesNo = (value: boolean) => this.localize(value ? "diagnostics.yes" : "diagnostics.no");
    const waitingItem = waiting && ("appliance_id" in waiting.key ? this.itemName("appliance", waiting.key.appliance_id) : this.itemName("charger", waiting.key.charger_id));
    return html`
      <dl class="facts">
        <dt>${this.localize("status.regulation_average")}</dt>
        <dd>${formatPower(language, decision.regulation_average_w)} kW</dd>
        <dt>${this.localize("status.tariff_average")}</dt>
        <dd>${formatPower(language, decision.tariff_average_w)} kW</dd>
        <dt>${this.localize("diagnostics.power_sensor_valid")}</dt>
        <dd>${yesNo(decision.power_sensor_valid)}</dd>
        <dt>${this.localize("status.safe_state_title")}</dt>
        <dd>${yesNo(decision.safe_state)}</dd>
        <dt>${this.localize("status.penalty_title")}</dt>
        <dd>${yesNo(decision.penalty_active)}</dd>
        <dt>${this.localize("diagnostics.overconsumption")}</dt>
        <dd>${this.localize("diagnostics.watt_hours", { energy: formatNumber(language, decision.overconsumption_wh, 0) })}</dd>
        <dt>${this.localize("diagnostics.waiting")}</dt>
        <dd>${waiting ? `${waitingItem}, ${formatClockTime(language, waiting.started_at)}–${formatClockTime(language, waiting.until)}` : this.localize("diagnostics.none")}</dd>
        <dt>${this.localize("diagnostics.commands")}</dt>
        <dd>${decision.commands.map((command) => this.commandText(command)).join(", ")}</dd>
      </dl>
    `;
  }

  private commandKind(command: DecisionCommand): "on" | "off" | "current" {
    switch (command.command) {
      case "TurnOnAppliance":
      case "ActivateCharger":
        return "on";
      case "TurnOffAppliance":
      case "DeactivateCharger":
        return "off";
      case "SetChargingCurrent":
        return "current";
    }
  }

  private commandText(command: DecisionCommand): string {
    switch (command.command) {
      case "TurnOnAppliance":
      case "TurnOffAppliance": {
        const name = this.itemName("appliance", command.appliance_id);
        const variant = this.config?.config.appliances.find((appliance) => appliance.id === command.appliance_id)?.variants.find((item) => item.id === command.variant_id);
        const key = command.command === "TurnOnAppliance" ? "diagnostics.turn_on" : "diagnostics.turn_off";
        return this.localize(key, { name: variant ? `${name} (${variant.label})` : name });
      }
      case "ActivateCharger":
        return this.localize("diagnostics.activate", { name: this.itemName("charger", command.charger_id) });
      case "DeactivateCharger":
        return this.localize("diagnostics.deactivate", { name: this.itemName("charger", command.charger_id) });
      case "SetChargingCurrent":
        return this.localize("diagnostics.set_current", { name: this.itemName("charger", command.charger_id), current: command.current_a });
    }
  }

  /** The name of an appliance or EV charger as the status has it, or its id when it is no longer configured. */
  private itemName(type: "appliance" | "charger", id: string): string {
    const status = this.status;
    const rows = !status ? [] : type === "appliance" ? applianceRows(status) : chargerRows(status);
    return rows.find((row) => row.id === id)?.name ?? id;
  }

  static styles = [
    cardHeaderStyles,
    chipStyles,
    css`
      :host {
        display: block;
        --kraftvakt-grid-color: var(--energy-grid-consumption-color, #488fc2);
        --kraftvakt-ev-color: var(--teal-color, #009688);
        --kraftvakt-on-color: var(--state-active-color, var(--amber-color, #ffc107));
        --kraftvakt-waiting-color: var(--purple-color, #926bc7);
      }
      .cards {
        display: grid;
        grid-template-columns: minmax(0, 1fr);
        gap: 16px;
      }
      :host([narrow]) .cards {
        gap: 8px;
      }
      .spacer {
        flex: 1;
      }
      .tiles {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
      }
      :host([narrow]) .tiles {
        gap: 8px;
      }
      .tile {
        display: grid;
        gap: 6px;
        align-content: start;
        padding: 14px 16px;
      }
      .tile-title {
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--disabled-text-color);
      }
      .dot.ok {
        background: var(--success-color, #43a047);
      }
      .dot.warning {
        background: var(--warning-color, #ffa600);
      }
      .dot.alarm {
        background: var(--error-color, #db4437);
      }
      .tile-value {
        font-size: var(--ha-font-size-xl, 20px);
      }
      dl {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 2px 12px;
        margin: 0;
        font-size: var(--ha-font-size-s, 12px);
      }
      dt {
        color: var(--secondary-text-color);
      }
      dd {
        margin: 0;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
      }
      .tile dd {
        text-align: end;
      }
      .description {
        margin: 0;
        padding: 0 16px 8px;
        color: var(--secondary-text-color);
      }
      .toggles {
        display: inline-flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .toggle {
        font: inherit;
        font-size: var(--ha-font-size-s, 12px);
        font-weight: 500;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid var(--divider-color);
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
      }
      .toggle[aria-pressed="true"] {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: var(--text-primary-color, #fff);
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 14px;
        padding: 0 16px 4px;
        font-size: var(--ha-font-size-s, 12px);
        color: var(--secondary-text-color);
      }
      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .swatch {
        display: inline-block;
        width: 16px;
        height: 10px;
      }
      .swatch.consumption {
        background: color-mix(in srgb, var(--secondary-text-color) 30%, transparent);
      }
      .swatch.line {
        height: 0;
        border-top: 2px solid var(--primary-text-color);
      }
      .swatch.line.tariff {
        border-top-color: var(--kraftvakt-grid-color);
      }
      .swatch.line.limit {
        border-top: 2px dashed var(--error-color, #db4437);
      }
      .swatch.waiting {
        border: 1px solid var(--kraftvakt-waiting-color);
        background: repeating-linear-gradient(45deg, transparent 0 3px, var(--kraftvakt-waiting-color) 3px 4px);
        box-sizing: border-box;
      }
      .swatch.unknown {
        border: 1px solid var(--divider-color);
        background: repeating-linear-gradient(-45deg, transparent 0 3px, var(--divider-color) 3px 5px);
        box-sizing: border-box;
      }
      .swatch.oldest {
        width: 0;
        height: 12px;
        border-left: 1px dashed var(--secondary-text-color);
      }
      .chart {
        position: relative;
        padding: 4px 0 12px;
        touch-action: pan-y;
      }
      svg {
        display: block;
        overflow: visible;
      }
      svg text {
        font-size: 11px;
        fill: var(--secondary-text-color);
      }
      svg .lane-name {
        font-size: var(--ha-font-size-s, 12px);
        fill: var(--primary-text-color);
      }
      .grid,
      .row-line {
        stroke: var(--divider-color);
      }
      .consumption {
        fill: color-mix(in srgb, var(--secondary-text-color) 30%, transparent);
      }
      .regulation {
        fill: none;
        stroke: var(--primary-text-color);
        stroke-width: 1.4;
      }
      .tariff {
        fill: none;
        stroke: var(--kraftvakt-grid-color);
        stroke-width: 2;
      }
      .limit {
        stroke: var(--error-color, #db4437);
        stroke-width: 1.5;
        stroke-dasharray: 6 4;
      }
      .oldest {
        stroke: var(--secondary-text-color);
        stroke-dasharray: 2 3;
      }
      .marked {
        stroke: var(--primary-color);
        stroke-width: 2;
      }
      .hover {
        stroke: var(--secondary-text-color);
      }
      .essential {
        fill: var(--kraftvakt-essential-background);
      }
      .unknown {
        fill: url(#unknown);
      }
      .unknown-line {
        stroke: var(--divider-color);
        stroke-width: 2;
      }
      .known {
        fill: var(--card-background-color, var(--ha-card-background, #fff));
      }
      rect.on {
        fill: var(--kraftvakt-on-color);
      }
      rect.current {
        fill: color-mix(in srgb, var(--kraftvakt-ev-color) 45%, transparent);
        stroke: var(--kraftvakt-ev-color);
      }
      rect.waiting {
        fill: url(#waiting);
        stroke: var(--kraftvakt-waiting-color);
        stroke-width: 0.8;
      }
      .waiting-line {
        stroke: var(--kraftvakt-waiting-color);
        stroke-width: 1.6;
      }
      .tooltip {
        position: absolute;
        top: 8px;
        z-index: 1;
        pointer-events: none;
        min-width: 180px;
        max-width: 260px;
        padding: 8px 10px;
        border-radius: 8px;
        background: var(--card-background-color, #fff);
        box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.25));
        border: 1px solid var(--divider-color);
        font-size: var(--ha-font-size-s, 12px);
        font-variant-numeric: tabular-nums;
      }
      .tooltip b {
        font-weight: 500;
      }
      .tooltip-decision {
        margin-top: 4px;
        padding-top: 4px;
        border-top: 1px solid var(--divider-color);
      }
      .table {
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      td {
        padding: 8px 16px;
        border-top: 1px solid var(--divider-color);
        vertical-align: top;
      }
      td.time,
      td.kind {
        width: 1%;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
        color: var(--secondary-text-color);
      }
      tr.event {
        cursor: pointer;
      }
      tr.event:hover td,
      tr.event.open td {
        background: color-mix(in srgb, var(--primary-color) 8%, transparent);
      }
      tr.event:focus-visible {
        outline: 2px solid var(--primary-color);
        outline-offset: -2px;
      }
      tr.details td {
        border-top: none;
        background: var(--secondary-background-color);
      }
      .chip.current {
        background: color-mix(in srgb, var(--kraftvakt-ev-color) 16%, transparent);
        color: var(--kraftvakt-ev-color);
      }
      .chip.failed {
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
        color: var(--error-color, #db4437);
      }
      .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 16px;
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
        color: var(--secondary-text-color);
        font-size: var(--ha-font-size-s, 12px);
      }
      .card-footer a {
        color: var(--primary-color);
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-diagnostics-page": KraftvaktDiagnosticsPage;
  }
}
