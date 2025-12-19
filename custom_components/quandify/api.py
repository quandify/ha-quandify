"""Quandify API client."""

import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_BASE_URL, AUTH_BASE_URL
from .const import (
    CONF_ACCOUNT_ID,
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_ORGANIZATION_ID,
)

_LOGGER = logging.getLogger(__name__)


class QuandifyAPIError(Exception):
    """Generic Quandify API exception."""


class QuandifyAPI:
    """A class for interacting with the Quandify API."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]) -> None:
        """Initialize the API client."""
        self.session = session
        self._config = config

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in to the Quandify API, performing the full authentication flow."""

        try:
            if not self._config.get(CONF_ID_TOKEN):
                auth_data = await self.auth_with_email(email, password)
                self._config[CONF_REFRESH_TOKEN] = auth_data.get("refresh_token")
                self._config[CONF_ID_TOKEN] = auth_data.get("id_token")
                self._config[CONF_ORGANIZATION_ID] = auth_data.get("organization_id")

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to authenticate to Quandify API: %s", err)
            raise QuandifyAPIError("Failed to authenticate to Quandify API") from err

        return self._config

    async def _refresh_token(self) -> bool:
        """Refresh the authentication token."""

        url = f"{AUTH_BASE_URL}/login/refresh"
        payload = {"refresh_token": self._config.get(CONF_REFRESH_TOKEN)}

        try:
            _LOGGER.debug("Attempting to refresh token")
            response = await self.session.post(url, json=payload)
            response.raise_for_status()
            data: dict[str, Any] = await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to refresh token: %s", err)
            raise ConfigEntryAuthFailed("Failed to refresh token") from err

        else:
            self._config[CONF_ID_TOKEN] = data.get("id_token")
            self._config[CONF_REFRESH_TOKEN] = data.get("refresh_token")

        return True

    async def _request(
        self, method: str, url: str, retry: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an authenticated request to the Quandify API, refreshing the token if needed."""

        headers = {"Authorization": f"Bearer {self._config.get(CONF_ID_TOKEN)}"}
        response = {}

        try:
            response = await self.session.request(
                method, url, headers=headers, **kwargs
            )
            response.raise_for_status()
            if response.content_type == "application/json":
                return await response.json()
            else:
                return await response.text()

        except aiohttp.ClientResponseError as err:
            # Check if the error is 401 Unauthorized and we are allowed to retry once.
            if err.status == 401 and retry:
                _LOGGER.info("Token expired or invalid, attempting refresh")
                if await self._refresh_token():
                    _LOGGER.info("Token refreshed, retrying the request")
                    return await self._request(method, url, retry=False, **kwargs)

            raise

    async def auth_with_email(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate to the Quandify API."""
        url = f"{AUTH_BASE_URL}/login/email"
        payload = {"email": email, "password": password}
        _LOGGER.debug("Attempting to authenticate to %s", url)
        response = await self.session.post(url, json=payload)
        response.raise_for_status()
        return await response.json()

    async def get_organization_id(self) -> str:
        """Fetch account details to get the organizationId."""
        account_id = self._config.get(CONF_ACCOUNT_ID)
        url = f"{AUTH_BASE_URL}/accounts/{account_id}"
        response = await self._request("get", url)
        organization_id = response.get("organizationId")

        if not organization_id:
            raise ValueError("Failed to retrieve organizationId from account info.")

        return organization_id

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch the list of devices."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/"
        response = await self._request("get", url)
        return response.get("data", [])

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get all info for a single device."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/{device_id}"
        return await self._request("get", url)

    async def acknowledge_leak(self, device_id: str) -> None:
        """Acknowledge a leak."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = (
            f"{API_BASE_URL}/organization/{organization_id}/devices/"
            f"{device_id}/commands/acknowledge-alarm"
        )
        await self._request("post", url)

    async def open_valve(self, device_id: str) -> None:
        """Open the valve on a device."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = (
            f"{API_BASE_URL}/organization/{organization_id}/devices/"
            f"{device_id}/commands/open-valve"
        )
        await self._request("post", url)

    async def close_valve(self, device_id: str) -> None:
        """Close the valve on a device."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = (
            f"{API_BASE_URL}/organization/{organization_id}/devices/"
            f"{device_id}/commands/close-valve"
        )
        await self._request("post", url)
