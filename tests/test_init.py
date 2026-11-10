"""Tester for oppsett og utlasting av integrasjonen."""

from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN, PANEL_URL_PATH
from custom_components.kraftvakt.storage import STORAGE_KEY, STORAGE_VERSION


async def test_setup_and_unload_registers_panel(hass: HomeAssistant) -> None:
    """Setting up again must not register the static path twice."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert PANEL_URL_PATH in hass.data["frontend_panels"]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert PANEL_URL_PATH not in hass.data["frontend_panels"]

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_panel_is_config_panel_for_integration(hass: HomeAssistant) -> None:
    """The configure button for the integration opens the panel."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    panel = hass.data["frontend_panels"][PANEL_URL_PATH]
    assert panel.config_panel_domain == DOMAIN
    assert panel.require_admin


async def test_panel_module_is_served(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """The built panel is found and served at the URL the panel loads."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    panel = hass.data["frontend_panels"][PANEL_URL_PATH]
    client = await hass_client()

    response = await client.get(panel.config["_panel_custom"]["module_url"])

    assert response.status == 200
    assert '"kraftvakt-panel"' in await response.text()


async def test_integration_runs_locally(hass: HomeAssistant) -> None:
    """No cloud services and no packages beyond Home Assistant."""
    integration = await async_get_integration(hass, DOMAIN)

    assert integration.requirements == []
    assert integration.manifest["iot_class"] == "calculated"


async def test_unreadable_configuration_gives_a_clear_error(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """The setup stops with a message, and the stored file is kept."""
    stored = {
        "version": STORAGE_VERSION,
        "key": STORAGE_KEY,
        "data": {"general": {"power_limit_w": "ti"}},
    }
    hass_storage[STORAGE_KEY] = stored
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert entry.error_reason_translation_key == "unreadable_configuration"
    assert hass_storage[STORAGE_KEY] == stored
