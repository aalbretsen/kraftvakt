import { mdiPlus } from "@mdi/js";
import { LitElement, css, html, nothing, type CSSResultGroup } from "lit";
import { property } from "lit/decorators.js";

import type { Capabilities, Issue, KraftvaktConfig } from "../api";
import "../components/sortable-list";
import type { ItemAdded, ListRow } from "../components/sortable-list";
import { allChargers, fireDraftChanged } from "../draft";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize } from "../localize";
import { renderDescription, sectionStyles } from "../section-styles";
import type { HomeAssistant } from "../types";
import { issuesFor } from "../validation";

/** A sortable list of items with a button that adds one. The texts are translated. */
export interface ItemList {
  add: string;
  empty: string;
  rows: ListRow[];
  /** Locked lists can only be viewed: nothing can be added, moved or changed. */
  locked: boolean;
  onAdd: () => void;
  onMoved: (event: CustomEvent<{ oldIndex: number; newIndex: number }>) => void;
  onOpen: (event: CustomEvent<string>) => void;
  /** Rows can be dragged between the lists of the same group, which then stay in view while empty. */
  group?: string;
  onAdded?: (event: CustomEvent<ItemAdded>) => void;
}

/**
 * A card on a configuration page: a header with the title and an optional
 * control at the right end, the description, the content, a list from edge
 * to edge and a footer.
 */
export interface Card {
  title: string;
  control?: unknown;
  description?: string;
  content?: unknown;
  list?: unknown;
  footer?: unknown;
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

  protected describeIssue = (issue: Issue): string => fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  protected formErrors(section: Issue["section"], target?: string, prefix = ""): Record<string, string> {
    return errorsByField(issuesFor(this.issues, section, target), prefix, this.describeIssue);
  }

  /** Return the entities other appliances and EV chargers than the item use, which it cannot use as well. */
  protected entitiesUsedBesides(itemId: string): string[] {
    return [...this.config.appliances, ...allChargers(this.config)].filter((item) => item.id !== itemId && item.entity_id).map((item) => item.entity_id as string);
  }

  protected renderCard(card: Card) {
    const hasContent = card.description || (card.content !== undefined && card.content !== nothing);
    return html`
      <ha-card>
        <div class="card-header">
          <h2 class="card-title">${card.title}</h2>
          ${card.control ?? nothing}
        </div>
        ${hasContent ? html`<div class="card-content">${renderDescription(card.description)} ${card.content ?? nothing}</div>` : nothing} ${card.list ?? nothing}
        ${card.footer ?? nothing}
      </ha-card>
    `;
  }

  /** A footer under a divider at the bottom of a card, with a note to the left of its control. */
  protected renderCardFooter(note: string, control: unknown) {
    return html`<div class="card-footer"><span class="note">${note}</span>${control}</div>`;
  }

  /** The row under the last card, with a note to the left of its control. */
  protected renderPageFooter(note: string, control: unknown) {
    return html`<div class="page-footer"><span class="note">${note}</span>${control}</div>`;
  }

  protected renderAddButton(list: ItemList) {
    return html`
      <ha-button .disabled=${list.locked} @click=${list.onAdd}>
        <ha-svg-icon slot="start" .path=${mdiPlus}></ha-svg-icon>
        ${list.add}
      </ha-button>
    `;
  }

  protected renderItemList(list: ItemList) {
    return list.rows.length === 0 && !list.group
      ? html`<div class="empty">${list.empty}</div>`
      : html`
          <kraftvakt-sortable-list
            class=${list.locked ? "locked" : ""}
            .localize=${this.localize}
            .rows=${list.rows}
            .locked=${list.locked}
            .group=${list.group}
            .emptyText=${list.empty}
            @item-moved=${list.onMoved}
            @item-added=${list.onAdded}
            @open-row=${list.onOpen}
          ></kraftvakt-sortable-list>
        `;
  }

  static styles: CSSResultGroup = [
    sectionStyles,
    css`
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
      .card-header {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px 12px;
        padding: 12px 16px 16px;
      }
      .card-title {
        flex: 1;
        min-width: 0;
        margin: 0;
        font-size: var(--ha-card-header-font-size, var(--ha-font-size-2xl, 24px));
        font-weight: var(--ha-font-weight-normal, 400);
        line-height: var(--ha-line-height-expanded, 1.5);
        letter-spacing: -0.012em;
        overflow-wrap: anywhere;
      }
      .card-content {
        display: grid;
        gap: 16px;
        padding: 0 16px 16px;
      }
      .card-footer {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding: 8px 8px 8px 16px;
        border-top: 1px solid var(--divider-color);
      }
      .page-footer {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding-inline-start: 16px;
      }
      .empty {
        padding: 0 16px 16px;
        color: var(--secondary-text-color);
      }
      kraftvakt-sortable-list.locked {
        opacity: 0.6;
      }
    `,
  ];
}
