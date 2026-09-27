/**
 * Kraftvakt-panel for Home Assistant-sidemenyen.
 *
 * Home Assistant setter egenskapene `hass`, `narrow`, `route` og `panel`
 * på elementet. Dette er et skall som skal bygges ut med konfigurasjon av
 * effektmål, apparater og prioritet.
 */
class KraftvaktPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._narrow = false;
  }

  set hass(hass) {
    const first = this._hass === null;
    this._hass = hass;
    if (first) this._render();
  }

  set narrow(narrow) {
    this._narrow = narrow;
    this._render();
  }

  connectedCallback() {
    this._render();
  }

  _render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          min-height: 100vh;
          background: var(--primary-background-color);
          color: var(--primary-text-color);
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        .toolbar {
          display: flex;
          align-items: center;
          gap: 8px;
          height: var(--header-height, 56px);
          padding: 0 16px;
          background: var(--app-header-background-color, var(--primary-color));
          color: var(--app-header-text-color, var(--text-primary-color));
          font-size: 20px;
        }
        .content {
          max-width: 960px;
          margin: 0 auto;
          padding: 16px;
        }
        ha-card { display: block; padding: 16px; }
      </style>
      <div class="toolbar">
        <ha-menu-button></ha-menu-button>
        <span>Kraftvakt</span>
      </div>
      <div class="content">
        <ha-card header="Kraftvakt">
          <p>Prioritert effektstyring. Konfigurasjon kommer her.</p>
        </ha-card>
      </div>
    `;
    const menu = this.shadowRoot.querySelector("ha-menu-button");
    if (menu) {
      menu.hass = this._hass;
      menu.narrow = this._narrow;
    }
  }
}

if (!customElements.get("kraftvakt-panel")) {
  customElements.define("kraftvakt-panel", KraftvaktPanel);
}
