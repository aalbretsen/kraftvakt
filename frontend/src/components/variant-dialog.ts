import { LitElement, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/**
 * Tells that a variant is configured in the dialog of its appliance, with
 * `ha-dialog`. Fires `closed` when the dialog has closed.
 */
@customElement("kraftvakt-variant-dialog")
export class KraftvaktVariantDialog extends LitElement {
  @property() heading = "";

  @property() text = "";

  @property() closeText = "";

  @state() private open = true;

  protected render() {
    return html`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button @click=${this.close}>${this.closeText}</ha-button>
        </div>
      </ha-dialog>
    `;
  }

  private close(): void {
    this.open = false;
  }

  private closed(event: Event): void {
    event.stopPropagation();
    this.open = false;
    this.dispatchEvent(new CustomEvent("closed"));
  }

  static styles = css`
    div[slot="footer"] {
      display: flex;
      justify-content: flex-end;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-variant-dialog": KraftvaktVariantDialog;
  }
}
