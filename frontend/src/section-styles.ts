import { css, html, nothing } from "lit";

/**
 * The parts the configuration pages and the dialogs share: a section header
 * with its title and an optional control at the right end, the description
 * under a title, and the note in a footer.
 *
 * A section is a part of a card on a page, and a group in a dialog.
 */
export const sectionStyles = css`
  .section-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 12px;
    min-height: 40px;
  }
  .section-title {
    flex: 1;
    min-width: 0;
    font-size: var(--ha-font-size-l, 16px);
    font-weight: var(--ha-font-weight-medium, 500);
  }
  .description {
    margin: 0;
    color: var(--secondary-text-color);
  }
  .note {
    flex: 1;
    min-width: 0;
    font-size: var(--ha-font-size-s, 12px);
    color: var(--secondary-text-color);
  }
`;

export function renderSectionHeader(title: string, control: unknown = nothing) {
  return html`
    <div class="section-header">
      <span class="section-title">${title}</span>
      ${control}
    </div>
  `;
}

export function renderDescription(text: string | undefined) {
  return text ? html`<p class="description">${text}</p>` : nothing;
}
