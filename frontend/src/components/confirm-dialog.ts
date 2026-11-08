import { LitElement, html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * Asks the user to confirm an action, with `ha-dialog`.
 *
 * Fires `confirm` when the user confirms, and `cancel` when the dialog is
 * closed any other way.
 */
@customElement("kraftvakt-confirm-dialog")
export class KraftvaktConfirmDialog extends LitElement {
  @property({ type: Boolean }) open = false;

  @property() heading = "";

  @property() text = "";

  @property() confirmText = "";

  @property() cancelText = "";

  private confirmed = false;

  protected render() {
    return html`
      <ha-dialog .open=${this.open} .headerTitle=${this.heading} @closed=${this.closed}>
        <p>${this.text}</p>
        <div slot="footer">
          <ha-button appearance="plain" @click=${this.cancel}>${this.cancelText}</ha-button>
          <ha-button variant="danger" @click=${this.confirm}>${this.confirmText}</ha-button>
        </div>
      </ha-dialog>
    `;
  }

  private confirm(): void {
    this.confirmed = true;
    this.open = false;
  }

  private cancel(): void {
    this.open = false;
  }

  private closed(event: Event): void {
    event.stopPropagation();
    const type = this.confirmed ? "confirm" : "cancel";
    this.confirmed = false;
    this.open = false;
    this.dispatchEvent(new CustomEvent(type));
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-confirm-dialog": KraftvaktConfirmDialog;
  }
}
