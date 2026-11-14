"""Kraftvakt: prioritized power management for Home Assistant."""

from __future__ import annotations

import asyncio
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .config_model import ConfigValidationError
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
from .settings import Settings
from .storage import KraftvaktStorage
from .websocket_api import async_forward_status, async_register_commands

FRONTEND_DIR = Path(__file__).parent / "frontend"
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the WebSocket commands for the panel."""
    async_register_commands(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    """A stored configuration that cannot be read stops the setup and is kept."""
    storage = KraftvaktStorage(hass)
    try:
        stored = await storage.async_load()
    except ConfigValidationError as error:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="unreadable_configuration",
            translation_placeholders={"issues": str(error)},
        ) from error
    runtime = KraftvaktRuntime(hass, Settings(hass, storage, stored), _action_lock(hass))
    entry.runtime_data = runtime
    entry.async_on_unload(runtime.async_shutdown)
    runtime.async_start()
    entry.async_on_unload(async_forward_status(hass, runtime))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await _async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KraftvaktConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    return unloaded


def _action_lock(hass: HomeAssistant) -> asyncio.Lock:
    """Return the lock for the actions, shared over reloads of the config entry."""
    lock: asyncio.Lock = hass.data.setdefault(DOMAIN, {}).setdefault("action_lock", asyncio.Lock())
    return lock


async def _async_register_panel(hass: HomeAssistant) -> None:
    # Static paths cannot be unregistered, so they are registered only once
    # per run of Home Assistant, also when the config entry is reloaded.
    if not hass.data.get(DOMAIN, {}).get("static_registered"):
        await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)])
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
