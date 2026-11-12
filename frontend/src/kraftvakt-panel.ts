import { mdiCarElectric, mdiCog, mdiFormatListNumbered, mdiPulse, mdiTune } from "@mdi/js";
import { LitElement, css, html, type PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { live } from "lit/directives/live.js";
import { literal, html as staticHtml } from "lit/static-html.js";

import {
  ERROR_NOT_LOADED,
  ERROR_REGULATION_RUNNING,
  errorMessage,
  fetchCapabilities,
  fetchConfig,
  isCommandError,
  saveConfig,
  subscribeStatus,
  type Capabilities,
  type ConfigResponse,
  type Issue,
  type KraftvaktConfig,
  type StatusSnapshot,
} from "./api";
import "./components/confirm-dialog";
import "./components/locked-banner";
import "./components/save-bar";
import { DRAFT_CHANGED, sameConfig, withCompletePriority } from "./draft";
import { localizer, type Localize } from "./localize";
import { navigateToPage, pageForPath, type Page } from "./navigation";
import "./pages/advanced-page";
import "./pages/appliances-page";
import "./pages/charging-page";
import "./pages/general-page";
import "./pages/status-page";
import type { HomeAssistant, Route } from "./types";
import { draftErrors, missingItems } from "./validation";

const TAB_ICONS: Record<Page, string> = {
  status: mdiPulse,
  general: mdiCog,
  appliances: mdiFormatListNumbered,
  charging: mdiCarElectric,
  advanced: mdiTune,
};

/** The element of each configuration page; they all get the same properties. */
const CONFIG_PAGE_ELEMENTS = {
  general: literal`kraftvakt-general-page`,
  appliances: literal`kraftvakt-appliances-page`,
  charging: literal`kraftvakt-charging-page`,
  advanced: literal`kraftvakt-advanced-page`,
};

/** The Kraftvakt panel in the Home Assistant sidebar. */
@customElement("kraftvakt-panel")
export class KraftvaktPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;

  @property({ type: Boolean, reflect: true }) narrow = false;

  @property({ attribute: false }) route?: Route;

  @state() private haElementsReady = false;

  @state() private status?: StatusSnapshot;

  @state() private config?: ConfigResponse;

  @state() private loadError?: unknown;

  @state() private capabilities?: Capabilities;

  @state() private draft?: KraftvaktConfig;

  @state() private saveErrors: Issue[] = [];

  @state() private saveMessage?: string;

  @state() private saving = false;

  /** The page the user wants to go to, while the panel asks to discard the changes. */
  @state() private leavingTo?: Page;

  private localize: Localize = localizer("en");

  private unsubscribeStatus?: Promise<() => Promise<void>>;

  connectedCallback(): void {
    super.connectedCallback();
    window.addEventListener("beforeunload", this.warnBeforeUnload);
    customElements.whenDefined("ha-form").then(() => {
      this.haElementsReady = true;
    });
    if (this.hass) {
      this.subscribe();
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener("beforeunload", this.warnBeforeUnload);
    this.unsubscribe();
  }

  protected willUpdate(changed: PropertyValues<this>): void {
    if (changed.has("hass") && this.hass?.language !== changed.get("hass")?.language) {
      this.localize = localizer(this.hass?.language ?? "en");
      // Home Assistant's action editor uses texts that only its own configuration panel loads.
      this.hass?.loadFragmentTranslation("config");
    }
    if (changed.has("hass") && this.hass && !this.unsubscribeStatus) {
      this.subscribe();
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
              <ha-tab-group-tab
                slot="nav"
                panel=${tab}
                .active=${live(tab === page)}
                title=${this.tabLabel(tab as Page)}
              >
                <ha-svg-icon .path=${icon}></ha-svg-icon>
                <span class="tab-label">${this.tabLabel(tab as Page)}</span>
              </ha-tab-group-tab>
            `,
          )}
        </ha-tab-group>
      </div>
      <div class="content" @draft-changed=${this.draftChanged}>${this.renderLoadError()} ${this.renderPage(page)}</div>
      <kraftvakt-confirm-dialog
        .open=${this.leavingTo !== undefined}
        .heading=${this.localize("config.leave_title")}
        .text=${this.localize("config.leave_text")}
        .confirmText=${this.localize("config.leave")}
        .cancelText=${this.localize("config.stay")}
        @confirm=${this.leaveConfirmed}
        @cancel=${this.leaveCancelled}
      ></kraftvakt-confirm-dialog>
    `;
  }

  private renderLoadError() {
    if (this.loadError === undefined) {
      return "";
    }
    const message =
      isCommandError(this.loadError) && this.loadError.code === ERROR_NOT_LOADED
        ? this.localize("panel.not_loaded")
        : this.localize("panel.error", { message: errorMessage(this.loadError) });
    return html`<ha-alert alert-type="error">${message}</ha-alert>`;
  }

  private renderPage(page: Page) {
    switch (page) {
      case "status":
        return html`
          <kraftvakt-status-page
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
            .status=${this.status}
            .config=${this.config}
          ></kraftvakt-status-page>
        `;
      case "general":
      case "appliances":
      case "charging":
      case "advanced":
        return this.renderConfigPage(page);
    }
  }

  private renderConfigPage(page: Exclude<Page, "status">) {
    if (!this.hass || !this.status || !this.config || !this.draft || !this.capabilities) {
      return "";
    }
    const locked = this.status.running;
    const errors = locked ? [] : draftErrors(this.draft, this.capabilities, this.hass);
    const showSaveBar = !locked && (this.dirty || this.saveErrors.length > 0);
    const issues = locked ? [] : this.pageIssues(errors);
    return html`
      ${locked
        ? html`<kraftvakt-locked-banner
            .hass=${this.hass}
            .localize=${this.localize}
            .narrow=${this.narrow}
          ></kraftvakt-locked-banner>`
        : ""}
      ${this.renderConfigPageContent(page, locked ? this.config.config : this.draft, issues, locked)}
      ${showSaveBar
        ? html`
            <kraftvakt-save-bar
              .localize=${this.localize}
              .errorCount=${errors.length}
              .saving=${this.saving}
              .message=${this.saveMessage}
              @save=${this.save}
              @discard=${this.discard}
            ></kraftvakt-save-bar>
          `
        : ""}
    `;
  }

  private renderConfigPageContent(
    page: Exclude<Page, "status">,
    config: KraftvaktConfig,
    issues: Issue[],
    locked: boolean,
  ) {
    const tag = CONFIG_PAGE_ELEMENTS[page];
    return staticHtml`
      <${tag}
        .hass=${this.hass}
        .localize=${this.localize}
        .narrow=${this.narrow}
        .config=${config}
        .entityNames=${this.config?.entity_names ?? {}}
        .capabilities=${this.capabilities}
        .issues=${issues}
        .saveErrors=${this.saveErrors}
        .locked=${locked}
      ></${tag}>
    `;
  }

  private pageIssues(errors: Issue[]): Issue[] {
    return this.draft ? [...errors, ...this.saveErrors, ...missingItems(this.draft)] : [];
  }

  private get dirty(): boolean {
    return this.draft !== undefined && !sameConfig(this.draft, this.savedConfig);
  }

  private get savedConfig(): KraftvaktConfig | undefined {
    return this.config && withCompletePriority(this.config.config);
  }

  private draftChanged(event: CustomEvent<KraftvaktConfig>): void {
    if (event.type === DRAFT_CHANGED && !this.status?.running) {
      this.draft = withCompletePriority(event.detail);
    }
  }

  private async save(): Promise<void> {
    if (!this.hass || !this.draft) {
      return;
    }
    this.saving = true;
    this.saveMessage = undefined;
    try {
      const result = await saveConfig(this.hass, this.draft);
      if (result.saved) {
        this.saveErrors = [];
        await this.loadConfig({ resetDraft: true });
      } else {
        this.saveErrors = result.errors;
        this.saveMessage = this.localize("config.not_saved");
      }
    } catch (error) {
      this.saveMessage =
        isCommandError(error) && error.code === ERROR_REGULATION_RUNNING
          ? this.localize("config.save_refused_running")
          : this.localize("panel.error", { message: errorMessage(error) });
    } finally {
      this.saving = false;
    }
  }

  private discard(): void {
    this.resetDraft();
  }

  private resetDraft(): void {
    this.draft = this.savedConfig;
    this.saveErrors = [];
    this.saveMessage = undefined;
  }

  private leaveConfirmed(): void {
    const page = this.leavingTo;
    this.leavingTo = undefined;
    this.resetDraft();
    if (page) {
      navigateToPage(page);
    }
  }

  private leaveCancelled(): void {
    this.leavingTo = undefined;
  }

  private warnBeforeUnload = (event: BeforeUnloadEvent): void => {
    if (this.dirty) {
      event.preventDefault();
    }
  };

  private get currentPage(): Page {
    return pageForPath(this.route?.path ?? "");
  }

  private tabLabel(page: Page): string {
    return this.localize(`tabs.${page}`);
  }

  /**
   * The draft is shared by the configuration pages, so the panel asks to discard
   * unsaved changes only when going to the status page.
   */
  private tabShown(event: CustomEvent<{ name: Page }>): void {
    const page = event.detail.name;
    if (page === this.currentPage) {
      return;
    }
    if (page === "status" && this.dirty) {
      this.leavingTo = page;
      return;
    }
    navigateToPage(page);
  }

  private subscribe(): void {
    if (!this.hass) {
      return;
    }
    this.unsubscribeStatus = subscribeStatus(this.hass, (status) => this.statusReceived(status));
    this.unsubscribeStatus.catch((error: unknown) => {
      this.loadError = error;
      this.unsubscribeStatus = undefined;
    });
    fetchCapabilities(this.hass)
      .then((capabilities) => (this.capabilities = capabilities))
      .catch((error: unknown) => (this.loadError = error));
  }

  private unsubscribe(): void {
    this.unsubscribeStatus?.then((unsubscribe) => unsubscribe()).catch(() => undefined);
    this.unsubscribeStatus = undefined;
  }

  /** Entities, like the power limit, can change the stored configuration at any time. */
  private statusReceived(status: StatusSnapshot): void {
    const previous = this.status;
    this.status = status;
    this.loadError = undefined;
    if (
      previous === undefined ||
      previous.running !== status.running ||
      previous.config_version !== status.config_version ||
      JSON.stringify(previous.missing) !== JSON.stringify(status.missing)
    ) {
      this.loadConfig();
    }
  }

  /**
   * The draft follows the configuration unless it has unsaved changes while the
   * regulation is stopped.
   */
  private async loadConfig(options: { resetDraft?: boolean } = {}): Promise<void> {
    if (!this.hass) {
      return;
    }
    try {
      const keepDraft = this.dirty && !options.resetDraft && !this.status?.running;
      this.config = await fetchConfig(this.hass);
      if (!keepDraft) {
        this.resetDraft();
      }
    } catch (error) {
      this.loadError = error;
    }
  }

  /** The configure button of the integration opens the appliances page. */
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
