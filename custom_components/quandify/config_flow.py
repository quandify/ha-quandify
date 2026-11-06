"""Config flow for Quandify integration."""

import logging
from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import QuandifyAPI, QuandifyAPIError, QuandifyAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)


class QuandifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Quandify."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)

            config_wrapper = {}
            api = QuandifyAPI(session, config_wrapper)

            try:
                config_obj = await api.login(
                    user_input.get(CONF_EMAIL), user_input.get(CONF_PASSWORD)
                )

            except (ConfigEntryAuthFailed, QuandifyAuthError):
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, QuandifyAPIError):
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("An unexpected error occurred during login: %s", err)
                errors["base"] = "unknown"
            else:
                email = (user_input.get(CONF_EMAIL) or "").lower()
                await self.async_set_unique_id(email)
                self._abort_if_unique_id_configured()

                # Configure data stored on disk
                cfg = (
                    config_obj.to_dict()
                    if hasattr(config_obj, "to_dict")
                    else dict(config_obj)
                )
                entry_data = {
                    CONF_EMAIL: user_input.get(CONF_EMAIL),
                    **cfg,
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

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Start reauthentication when the stored tokens are no longer valid."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for the password again and store fresh tokens."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        email = entry.data.get(CONF_EMAIL, entry.title)
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = QuandifyAPI(session, {})

            try:
                new_config = await api.login(email, user_input[CONF_PASSWORD])

            except QuandifyAuthError:
                errors["base"] = "invalid_auth"
            except (aiohttp.ClientError, QuandifyAPIError):
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("An unexpected error occurred during reauth: %s", err)
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **dict(new_config)},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"email": email},
            errors=errors,
        )
