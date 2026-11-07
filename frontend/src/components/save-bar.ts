import { mdiContentSave } from "@mdi/js";
import { LitElement, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { Localize } from "../localize";

/**
 * «Save» and «Discard» for the draft of the configuration pages (B7).
 *
 * Fires `save` and `discard`. Saving is disabled while the draft has mistakes
 * the panel can see itself.
 */
@customElement("kraftvakt-save-bar")
export class KraftvaktSaveBar extends LitElement {
  @property({ attribute: false }) localize!: Localize;

  @property({ type: Number }) errorCount = 0;

  @property({ type: Boolean }) saving = false;

  /** Why the last attempt to save failed, if it did. */
  @property() message?: string;

  protected render() {
    const text =
      this.errorCount > 0 ? this.localize("config.fix_before_saving", { count: this.errorCount }) : this.message;
    return html`
      <div class="bar" role="region" aria-label=${this.localize("config.unsaved")}>
        <div class="text">
          <div class="title">${this.localize("config.unsaved")}</div>
          ${text ? html`<div class="error">${text}</div>` : nothing}
        </div>
        <ha-button appearance="plain" .disabled=${this.saving} @click=${() => this.fire("discard")}>
          ${this.localize("config.discard")}
        </ha-button>
        <ha-button .disabled=${this.saving || this.errorCount > 0} @click=${() => this.fire("save")}>
          <ha-svg-icon slot="start" .path=${mdiContentSave}></ha-svg-icon>
          ${this.localize("config.save")}
        </ha-button>
      </div>
    `;
  }

  private fire(type: "save" | "discard"): void {
    this.dispatchEvent(new CustomEvent(type));
  }

  static styles = css`
    :host {
      display: block;
      position: sticky;
      bottom: 0;
      z-index: 2;
      padding: 8px 0 16px;
    }
    .bar {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding: 8px 8px 8px 16px;
      border-radius: var(--ha-card-border-radius, 12px);
      background: var(--card-background-color);
      box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0, 0, 0, 0.25));
      border: 1px solid var(--divider-color);
    }
    .text {
      flex: 1;
      min-width: 160px;
    }
    .title {
      font-weight: 500;
    }
    .error {
      color: var(--error-color);
      font-size: var(--ha-font-size-s, 12px);
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-save-bar": KraftvaktSaveBar;
  }
}
