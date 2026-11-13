import { mdiDragHorizontalVariant, mdiEye, mdiPencil } from "@mdi/js";
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

import type { Localize } from "../localize";

export interface ListRow {
  key: string;
  title: string;
  /** A label after the title, like the label of a variant. */
  tag?: string;
  iconPath?: string;
  details: (string | TemplateResult)[];
  errors: string[];
  /** Whether the row opens a dialog to edit or show it. */
  openable: boolean;
}

/** A row dragged in from another list: its key and its new index. */
export interface ItemAdded {
  key: string;
  index: number;
}

/**
 * A list the user sorts by dragging, with `ha-sortable`.
 *
 * Fires `item-moved` with the old and new index, `item-added` when a row is
 * dragged in from another list of the same group, and `open-row` with the key
 * of the row whose button was pressed. `ha-sortable` puts a dragged row back,
 * and the rows follow the new `rows`. While locked, the rows cannot be moved
 * and the button only shows them.
 */
@customElement("kraftvakt-sortable-list")
export class KraftvaktSortableList extends LitElement {
  @property({ attribute: false }) localize!: Localize;

  @property({ attribute: false }) rows: ListRow[] = [];

  @property({ type: Boolean }) locked = false;

  /** Lists of the same group share their rows by dragging. Set before the list is first shown. */
  @property() group?: string;

  /** Shown in an empty list, which stays a place to drop rows on. Nothing but the rows may be in the list. */
  @property() emptyText = "";

  protected render() {
    return html`
      <ha-sortable
        handle-selector=".handle"
        group=${ifDefined(this.group)}
        .disabled=${this.locked}
        @item-moved=${this.itemMoved}
        @item-added=${this.itemAdded}
        @item-removed=${this.itemRemoved}
      >
        <div class="list" data-empty=${this.emptyText}>${repeat(
          this.rows,
          (row) => row.key,
          (row, index) => this.renderRow(row, index),
        )}</div>
      </ha-sortable>
    `;
  }

  private renderRow(row: ListRow, index: number) {
    return html`
      <div class="row" data-key=${row.key}>
        ${this.locked
          ? nothing
          : html`<ha-svg-icon class="handle" .path=${mdiDragHorizontalVariant} title=${this.localize("list.drag")}></ha-svg-icon>`}
        <span class="rank">${index + 1}</span>
        ${row.iconPath ? html`<ha-svg-icon class="icon" .path=${row.iconPath}></ha-svg-icon>` : nothing}
        <div class="main">
          <div class="title">${row.title}${row.tag ? html`<span class="tag">${row.tag}</span>` : nothing}</div>
          ${row.details.length > 0 ? html`<div class="details">${joined(row.details)}</div>` : nothing}
          ${row.errors.map((error) => html`<div class="error">${error}</div>`)}
        </div>
        ${row.openable
          ? html`
              <ha-icon-button
                .path=${this.locked ? mdiEye : mdiPencil}
                .label=${this.localize(this.locked ? "list.view" : "list.edit")}
                @click=${() => this.dispatchEvent(new CustomEvent("open-row", { detail: row.key }))}
              ></ha-icon-button>
            `
          : nothing}
      </div>
    `;
  }

  private itemMoved(event: CustomEvent<{ oldIndex: number; newIndex: number }>): void {
    event.stopPropagation();
    this.dispatchEvent(new CustomEvent("item-moved", { detail: event.detail }));
  }

  private itemAdded(event: CustomEvent<{ index: number; item: HTMLElement }>): void {
    event.stopPropagation();
    const key = event.detail.item.dataset.key;
    if (key !== undefined) {
      this.dispatchEvent(new CustomEvent<ItemAdded>("item-added", { detail: { key, index: event.detail.index } }));
    }
  }

  /** The list the row was dragged to moves it. */
  private itemRemoved(event: Event): void {
    event.stopPropagation();
  }

  static styles = css`
    :host {
      display: block;
    }
    .list:empty {
      min-height: 48px;
    }
    .list:empty::before {
      content: attr(data-empty);
      display: block;
      padding: 0 16px 16px;
      color: var(--secondary-text-color);
    }
    .row {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: 56px;
      padding: 6px 8px 6px 16px;
      border-top: 1px solid var(--divider-color);
      box-sizing: border-box;
      background: var(--card-background-color);
    }
    .handle {
      flex: none;
      cursor: grab;
      color: var(--secondary-text-color);
    }
    .rank {
      flex: none;
      min-width: 20px;
      text-align: center;
      color: var(--secondary-text-color);
    }
    .icon {
      flex: none;
      color: var(--state-icon-color, var(--secondary-text-color));
    }
    .main {
      flex: 1;
      min-width: 0;
    }
    .title {
      overflow-wrap: anywhere;
    }
    .tag {
      display: inline-block;
      margin-inline-start: 6px;
      padding: 0 8px;
      border-radius: 999px;
      font-size: var(--ha-font-size-s, 12px);
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
      color: var(--primary-color);
    }
    .details,
    .error {
      font-size: var(--ha-font-size-s, 12px);
      overflow-wrap: anywhere;
    }
    .details {
      color: var(--secondary-text-color);
    }
    .details a {
      color: var(--primary-color);
    }
    .error {
      color: var(--error-color);
    }
  `;
}

/** Join the details with a dot between them. */
function joined(details: (string | TemplateResult)[]) {
  return details.map((detail, index) => html`${index > 0 ? " · " : ""}${detail}`);
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-sortable-list": KraftvaktSortableList;
  }
}
