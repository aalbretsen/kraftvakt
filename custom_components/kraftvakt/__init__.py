"""Kraftvakt: prioritert effektstyring for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import (
    DOMAIN,
    PANEL_COMPONENT_NAME,
    PANEL_FILENAME,
    PANEL_ICON,
    PANEL_TITLE,
    PANEL_URL_PATH,
    STATIC_URL,
)

FRONTEND_DIR = Path(__file__).parent / "frontend"

type KraftvaktConfigEntry = ConfigEntry[None]


async def async_setup_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    """Sett opp Kraftvakt fra en config entry."""
    await _async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    """Last ut en config entry."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH)
    return True


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Registrer sidepanelet i sidemenyen."""
    # Statiske stier kan ikke avregistreres, så de registreres kun én gang
    # per kjøring av Home Assistant (også ved reload av config entry).
    if not hass.data.get(DOMAIN, {}).get("static_registered"):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
        )
        hass.data.setdefault(DOMAIN, {})["static_registered"] = True

    # Versjonen i URL-en tvinger nettleseren til å hente ny JS etter oppdatering.
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
    )
