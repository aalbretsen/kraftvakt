"""Config flow for Kraftvakt."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, NAME


class KraftvaktConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up Kraftvakt without any settings (GUI-004).

    The configuration (power limit, appliances and priority) is done in the
    Kraftvakt panel in the sidebar. This flow only creates the integration.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm the setup."""
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user")
