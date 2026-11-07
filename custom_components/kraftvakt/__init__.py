"""Kraftvakt: prioritized power control for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .charger_switches import ChargerSwitchBoard
from .const import (
    DOMAIN,
    PANEL_COMPONENT_NAME,
    PANEL_FILENAME,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL_PATH,
    STATIC_URL,
)
from .runtime import KraftvaktConfigEntry, KraftvaktRuntime
from .storage import KraftvaktStorage

FRONTEND_DIR = Path(__file__).parent / "frontend"
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    """Set up Kraftvakt from a config entry."""
    storage = KraftvaktStorage(hass)
    stored = await storage.async_load()
    runtime = KraftvaktRuntime(
        hass, stored.config, ChargerSwitchBoard(hass, storage, stored)
    )
    entry.runtime_data = runtime
    entry.async_on_unload(runtime.async_shutdown)
    runtime.async_start()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    return unloaded


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the panel in the sidebar."""
    # Static paths cannot be unregistered, so they are registered only once
    # per run of Home Assistant, also when the config entry is reloaded.
    if not hass.data.get(DOMAIN, {}).get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
        )
        hass.data.setdefault(DOMAIN, {})["static_registered"] = True

    # The version in the URL makes the browser fetch new JS after an update.
    integration = await async_get_integration(hass, DOMAIN)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_COMPONENT_NAME,
        module_url=f"{STATIC_URL}/{PANEL_FILENAME}?v={integration.version}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=True,
        config={},
        config_panel_domain=DOMAIN,
    )
