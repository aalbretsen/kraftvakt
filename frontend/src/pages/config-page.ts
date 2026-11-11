import { mdiPlus } from "@mdi/js";
import { LitElement, css, html, type CSSResultGroup } from "lit";
import { property } from "lit/decorators.js";

import type { Capabilities, Issue, KraftvaktConfig } from "../api";
import "../components/sortable-list";
import type { ListRow } from "../components/sortable-list";
import { fireDraftChanged } from "../draft";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize, TranslationKey } from "../localize";
import type { HomeAssistant } from "../types";

/** A card with a sortable list of items and a button that adds one. */
export interface ListCard {
  title: TranslationKey;
  sub: TranslationKey;
  add: TranslationKey;
  empty: TranslationKey;
  rows: ListRow[];
  /** Locked lists can only be viewed: nothing can be added, moved or changed. */
  locked: boolean;
  onAdd: () => void;
  onMoved: (event: CustomEvent<{ oldIndex: number; newIndex: number }>) => void;
  onOpen: (event: CustomEvent<string>) => void;
}

/**
 * What every configuration page gets from the panel, and what the pages share.
 *
 * `config` is the draft while the regulation is stopped, and the saved
 * configuration while it runs and the configuration is locked.
 * `issues` are the mistakes and what is missing in the draft.
 */
export class ConfigPage extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;

  @property({ attribute: false }) localize!: Localize;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) config!: KraftvaktConfig;

  @property({ attribute: false }) entityNames: Record<string, string> = {};

  @property({ attribute: false }) capabilities!: Capabilities;

  @property({ attribute: false }) issues: Issue[] = [];

  /** The errors the backend gave when the draft was last saved, also included in `issues`. */
  @property({ attribute: false }) saveErrors: Issue[] = [];

  @property({ type: Boolean, reflect: true }) locked = false;

  protected changeConfig(config: KraftvaktConfig): void {
    fireDraftChanged(this, config);
  }

  protected describeIssue = (issue: Issue): string =>
    fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  protected formErrors(section: Issue["section"], target?: string, prefix = ""): Record<string, string> {
    const issues = this.issues.filter((issue) => issue.section === section && issue.target === target);
    return errorsByField(issues, prefix, this.describeIssue);
  }

  /** Return the entities other appliances and EV chargers than the item use, which it cannot use as well. */
  protected entitiesUsedBesides(itemId: string): string[] {
    return [...this.config.appliances, ...this.config.charging.chargers]
      .filter((item) => item.id !== itemId && item.entity_id)
      .map((item) => item.entity_id as string);
  }

  /** A sortable list of items in a card; `footer` goes at the bottom of the card. */
  protected renderListCard(list: ListCard, footer: unknown = "") {
    return html`
      <ha-card class=${list.locked ? "locked" : ""}>
        <div class="card-header">
          <div class="heading">
            <span>${this.localize(list.title)}</span>
            <span class="sub">${this.localize(list.sub)}</span>
          </div>
          <ha-button .disabled=${list.locked} @click=${list.onAdd}>
            <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
            ${this.localize(list.add)}
          </ha-button>
        </div>
        ${list.rows.length === 0
          ? html`<div class="empty">${this.localize(list.empty)}</div>`
          : html`
              <kraftvakt-sortable-list
                .localize=${this.localize}
                .rows=${list.rows}
                .locked=${list.locked}
                @item-moved=${list.onMoved}
                @open-row=${list.onOpen}
              ></kraftvakt-sortable-list>
            `}
        ${footer}
      </ha-card>
    `;
  }

  static styles: CSSResultGroup = css`
    :host {
      display: grid;
      gap: 16px;
    }
    :host([narrow]) {
      gap: 8px;
    }
    /* HA's number field keeps its full text colour when disabled. */
    :host([locked]) ha-form {
      opacity: 0.6;
    }
    .card-content {
      padding: 0 16px 16px;
    }
    .card-header {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 16px;
    }
    .heading {
      flex: 1;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 4px 12px;
      font-size: var(--ha-font-size-xl, 20px);
    }
    .sub {
      font-size: var(--ha-font-size-m, 14px);
      color: var(--secondary-text-color);
    }
    .empty {
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
    }
    .locked kraftvakt-sortable-list {
      opacity: 0.6;
    }
  `;
}
