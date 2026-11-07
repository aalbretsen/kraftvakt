/** The pages of the panel, with their address under the panel (5.2). */
export const PAGES = ["status", "general", "appliances", "charging"] as const;

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
