"""Tester for oppsett og utlasting av integrasjonen."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.kraftvakt.const import DOMAIN, PANEL_URL_PATH


async def test_setup_and_unload_registers_panel(hass: HomeAssistant) -> None:
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

    # Reload skal ikke feile på dobbel registrering av statisk sti.
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED


async def test_panel_is_config_panel_for_integration(hass: HomeAssistant) -> None:
    """The configure button for the integration opens the panel (GUI-003)."""
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
    """The built panel is found and served at the URL the panel loads (B1)."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    panel = hass.data["frontend_panels"][PANEL_URL_PATH]
    client = await hass_client()

    response = await client.get(panel.config["_panel_custom"]["module_url"])

    assert response.status == 200
    assert '"kraftvakt-panel"' in await response.text()
