"""Config flow for Quandify integration."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import QuandifyAPI, QuandifyAPIError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

class QuandifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Quandify."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = QuandifyAPI(session, {})

            try:
                config = await api.login(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])

            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, QuandifyAPIError):
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("An unexpected error occurred during login: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()


                # Configure data stored on disk
                entry_data = {
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    **config
                }

                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=entry_data,
                )

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
