/** The pages of the panel, with their address under the panel. */
export const PAGES = ["status", "general", "appliances", "charging", "advanced"] as const;

export type Page = (typeof PAGES)[number];

export const PANEL_PATH = "/kraftvakt";

/** Return the page for the panel's part of the address, the status page by default. */
export function pageForPath(path: string): Page {
  const name = path.split("/")[1] ?? "";
  return (PAGES as readonly string[]).includes(name) ? (name as Page) : "status";
}

/** Go to a page of the panel the way Home Assistant's own pages do. */
export function navigateToPage(page: Page, options: { replace?: boolean } = {}): void {
  const url = `${PANEL_PATH}/${page}`;
  if (options.replace) {
    history.replaceState(null, "", url);
  } else {
    history.pushState(null, "", url);
  }
  window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: options.replace ?? false } }));
}

/** Open Home Assistant's more-info dialog for an entity, with its history and settings. */
export function showMoreInfo(element: EventTarget, entityId: string): void {
  element.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
}
