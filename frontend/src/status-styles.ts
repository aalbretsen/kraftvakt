import { css } from "lit";

/** The header of the cards on the status page. */
export const cardHeaderStyles = css`
  .card-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    min-height: 40px;
    padding: 12px 16px;
    font-size: var(--ha-font-size-xl, 20px);
  }
`;

/** A rounded chip with an icon or a dot and a word, in the colour of its kind. */
export const chipStyles = css`
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: var(--ha-font-size-s, 12px);
    font-weight: 500;
    line-height: 20px;
    white-space: nowrap;
    background: var(--kraftvakt-chip-off-background, rgba(127, 127, 127, 0.16));
    color: var(--secondary-text-color);
  }
  .chip .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }
  .chip ha-svg-icon {
    --mdc-icon-size: 16px;
  }
  .chip.running,
  .chip.on {
    background: rgba(var(--rgb-success-color, 67, 160, 71), 0.16);
    color: var(--success-color, #43a047);
  }
  .chip.alarm {
    background: rgba(var(--rgb-error-color, 219, 68, 55), 0.16);
    color: var(--error-color, #db4437);
  }
  .chip.warning {
    background: rgba(var(--rgb-warning-color, 255, 166, 0), 0.16);
    color: var(--warning-color, #ffa600);
  }
  .chip.outline {
    background: none;
    box-shadow: inset 0 0 0 1px var(--divider-color);
  }
  .chip.info {
    background: rgba(var(--rgb-info-color, 3, 155, 229), 0.16);
    color: var(--info-color, #039be5);
  }
`;
