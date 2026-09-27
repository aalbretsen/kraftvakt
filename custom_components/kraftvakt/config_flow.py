"""Config flow for Kraftvakt."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DOMAIN, NAME


class KraftvaktConfigFlow(ConfigFlow, domain=DOMAIN):
    """Oppsett av Kraftvakt.

    Selve konfigurasjonen (effektmål, apparater og prioritet) gjøres i
    Kraftvakt-panelet i sidemenyen. Denne flyten oppretter bare integrasjonen.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Bekreft oppsett."""
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user")
