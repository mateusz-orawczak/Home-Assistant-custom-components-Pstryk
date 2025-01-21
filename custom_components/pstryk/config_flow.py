"""Config flow for Pstryk integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.data_entry_flow import FlowResult
import aiohttp

from .api import PstrykApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pstryk."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            async with aiohttp.ClientSession() as session:
                client = PstrykApiClient(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    session,
                )
                if await client.authenticate():
                    await session.close()
                    return self.async_create_entry(
                        title=user_input[CONF_EMAIL],
                        data=user_input,
                    )
                errors["base"] = "auth"
                await session.close()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
