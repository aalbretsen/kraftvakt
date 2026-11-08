import { LitElement, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import type { Localize } from "../localize";

/** Warns against turning regulated appliances or EV chargers on or off outside Kraftvakt. */
@customElement("kraftvakt-manual-control-warning")
export class KraftvaktManualControlWarning extends LitElement {
  @property({ attribute: false }) localize!: Localize;

  @property() kind: "appliances" | "chargers" = "appliances";

  @property({ type: Boolean }) narrow = false;

  protected render() {
    return html`
      <ha-alert alert-type="warning" .title=${this.localize(`warning.${this.kind}_title`)} .narrow=${this.narrow}>
        ${this.localize("warning.text")}
      </ha-alert>
    `;
  }

  static styles = css`
    :host {
      display: block;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-manual-control-warning": KraftvaktManualControlWarning;
  }
}
