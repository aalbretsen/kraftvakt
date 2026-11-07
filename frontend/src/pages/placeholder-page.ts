import { LitElement, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { Localize } from "../localize";

/** Stands in for a configuration page until it is made (phase 9). */
@customElement("kraftvakt-placeholder-page")
export class KraftvaktPlaceholderPage extends LitElement {
  @property({ attribute: false }) localize!: Localize;

  protected render() {
    return html`<ha-card><div class="content">${this.localize("placeholder.not_ready")}</div></ha-card>`;
  }

  static styles = css`
    .content {
      padding: 16px;
    }
  `;
}
