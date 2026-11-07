import { mdiCarElectric, mdiCog, mdiFormatListNumbered, mdiPulse } from "@mdi/js";
import { LitElement, css, html, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { localizer, type Localize } from "./localize";
import { navigateToPage, pageForPath, type Page } from "./navigation";
import "./pages/placeholder-page";
import type { HomeAssistant, Route } from "./types";

const TAB_ICONS: Record<Page, string> = {
  status: mdiPulse,
  general: mdiCog,
  appliances: mdiFormatListNumbered,
  charging: mdiCarElectric,
};

/**
 * The Kraftvakt panel in the Home Assistant sidebar (GUI-001).
 *
 * Home Assistant sets `hass`, `narrow`, `route` and `panel` on the element. The
 * panel shows a top menu with a tab for each page (GUI-002) and the page that
 * the route points to (5.2).
 */
@customElement("kraftvakt-panel")
export class KraftvaktPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) route?: Route;

  /** Home Assistant's own elements, like `ha-form`, are ready to use (5.4). */
  @state() private haElementsReady = false;

  private localize: Localize = localizer("en");

  connectedCallback(): void {
    super.connectedCallback();
    customElements.whenDefined("ha-form").then(() => {
      this.haElementsReady = true;
    });
  }

  protected willUpdate(changed: PropertyValues<this>): void {
    if (changed.has("hass") && this.hass?.language !== changed.get("hass")?.language) {
      this.localize = localizer(this.hass?.language ?? "en");
    }
  }

  protected updated(changed: PropertyValues<this>): void {
    if (changed.has("route")) {
      this.openAppliancesFromConfigureButton();
    }
  }

  protected render() {
    if (!this.hass || !this.haElementsReady) {
      return html``;
    }
    const page = this.currentPage;
    return html`
      <div class="toolbar">
        <ha-menu-button .hass=${this.hass} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${this.localize("panel.title")}</div>
        <ha-tab-group @wa-tab-show=${this.tabShown}>
          ${Object.entries(TAB_ICONS).map(
            ([tab, icon]) => html`
              <ha-tab-group-tab slot="nav" panel=${tab} .active=${tab === page} title=${this.tabLabel(tab as Page)}>
                <ha-svg-icon .path=${icon}></ha-svg-icon>
                <span class="tab-label">${this.tabLabel(tab as Page)}</span>
              </ha-tab-group-tab>
            `,
          )}
        </ha-tab-group>
      </div>
      <div class="content">${this.renderPage(page)}</div>
    `;
  }

  private renderPage(page: Page) {
    switch (page) {
      case "status":
      case "general":
      case "appliances":
      case "charging":
        return html`<kraftvakt-placeholder-page .localize=${this.localize}></kraftvakt-placeholder-page>`;
    }
  }

  private get currentPage(): Page {
    return pageForPath(this.route?.path ?? "");
  }

  private tabLabel(page: Page): string {
    return this.localize(`tabs.${page}`);
  }

  private tabShown(event: CustomEvent<{ name: Page }>): void {
    if (event.detail.name !== this.currentPage) {
      navigateToPage(event.detail.name);
    }
  }

  /** The configure button of the integration opens the appliances page (GUI-003, R1). */
  private openAppliancesFromConfigureButton(): void {
    if (new URLSearchParams(window.location.search).has("config_entry")) {
      navigateToPage("appliances", { replace: true });
    }
  }

  static styles = css`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: var(--header-height, 56px);
      padding: 0 12px;
      box-sizing: border-box;
      background: var(--app-header-background-color, var(--primary-color));
      color: var(--app-header-text-color, var(--text-primary-color));
      border-bottom: var(--app-header-border-bottom, none);
    }
    .title {
      font-size: var(--ha-font-size-xl, 20px);
      margin-inline-end: 16px;
    }
    ha-tab-group {
      flex: 1;
      min-width: 0;
      align-self: stretch;
      --ha-tab-active-text-color: var(--app-header-text-color, var(--text-primary-color));
      --ha-tab-indicator-color: var(--app-header-text-color, var(--text-primary-color));
      --ha-tab-track-color: transparent;
    }
    ha-tab-group-tab {
      height: 100%;
    }
    .tab-label {
      margin-inline-start: 8px;
    }
    :host([narrow]) .title {
      display: none;
    }
    :host([narrow]) .tab-label {
      display: none;
    }
    .content {
      max-width: 1040px;
      margin: 0 auto;
      padding: 16px;
    }
    :host([narrow]) .content {
      padding: 8px;
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "kraftvakt-panel": KraftvaktPanel;
  }
}
