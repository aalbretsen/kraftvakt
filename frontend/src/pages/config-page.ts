import { LitElement } from "lit";
import { property } from "lit/decorators.js";

import type { Capabilities, Issue, KraftvaktConfig } from "../api";
import { fireDraftChanged } from "../draft";
import { errorsByField, fieldErrorText } from "../issues";
import type { Localize } from "../localize";
import type { HomeAssistant } from "../types";

/**
 * What every configuration page gets from the panel.
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

  /** Replace the draft with a changed configuration. */
  protected changeConfig(config: KraftvaktConfig): void {
    fireDraftChanged(this, config);
  }

  protected describeIssue = (issue: Issue): string =>
    fieldErrorText(issue, this.localize, this.capabilities, this.hass.language);

  /** The error text per field for `ha-form`, of the issues in a section. */
  protected formErrors(section: Issue["section"], target?: string, prefix = ""): Record<string, string> {
    const issues = this.issues.filter((issue) => issue.section === section && issue.target === target);
    return errorsByField(issues, prefix, this.describeIssue);
  }
}
