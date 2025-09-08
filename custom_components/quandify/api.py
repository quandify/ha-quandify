"""Quandify API client."""
import json
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_BASE_URL, AUTH_BASE_URL
from .const import FIREBASE_API_KEY, FIREBASE_AUTH_BASE_URL
from .const import CONF_ACCOUNT_ID, CONF_ID_TOKEN, CONF_REFRESH_TOKEN, CONF_ORGANIZATION_ID

_LOGGER = logging.getLogger(__name__)
class QuandifyAPIError(Exception):
    """Generic Quandify API exception."""

class QuandifyAPI:
    """A class for interacting with the Quandify API."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]):
        """Initialize the API client."""
        self.session = session
        self._config = config

    async def _firebase_auth(self, email: str, password: str) -> dict[str, Any]:
        """Perform the full Firebase authentication flow to get all necessary IDs."""
        try:
            signin_url = (
                f"{FIREBASE_AUTH_BASE_URL}"
                f"/accounts:signInWithPassword"
                f"?key={FIREBASE_API_KEY}"
            )

            signin_payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True,
            }

            response = await self.session.post(signin_url, json=signin_payload)
            response.raise_for_status()
            signin_data = await response.json()
            firebase_id_token = signin_data["idToken"]

            lookup_url = f"{FIREBASE_AUTH_BASE_URL}/accounts:lookup?key={FIREBASE_API_KEY}"
            lookup_payload = {"idToken": firebase_id_token}
            response = await self.session.post(lookup_url, json=lookup_payload)
            response.raise_for_status()
            lookup_data = await response.json()

            user_info = lookup_data.get("users", [{}])[0]
            custom_attributes_str = user_info.get("customAttributes", "{}")
            custom_attributes = json.loads(custom_attributes_str)
            account_id = custom_attributes.get("accountId")

            if not account_id:
                raise ConfigEntryAuthFailed("Could not find Quandify accountId in user profile")

            return {
                "account_id": account_id,
                "id_token": firebase_id_token,
                "refresh_token": signin_data["refreshToken"],
            }

        except aiohttp.ClientError as err:
            _LOGGER.error("A connection error occurred during authentication: %s", err)
            raise QuandifyAPIError(f"Connection error: {err}") from err

        except (KeyError, json.JSONDecodeError) as err:
            _LOGGER.error("Received an unexpected response from the authentication API: %s", err)
            raise QuandifyAPIError("Unexpected API response during login.") from err

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in to the Quandify API, performing the full authentication flow."""

        try:
            if not self._config.get(CONF_ACCOUNT_ID):
                f_base = await self._firebase_auth(email, password)
                self._config[CONF_ACCOUNT_ID] = f_base["account_id"]

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to authenticate via Firebase: %s", err)
            raise QuandifyAPIError("Failed to authenticate via Firebase") from err

        try:
            if not self._config.get(CONF_ID_TOKEN):
                auth_data = await self.auth(self._config.get(CONF_ACCOUNT_ID), password)
                self._config[CONF_REFRESH_TOKEN] = auth_data["refresh_token"]
                self._config[CONF_ID_TOKEN] = auth_data["id_token"]

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to authenticate to Quandify API: %s", err)
            raise QuandifyAPIError("Failed to authenticate to Quandify API") from err

        try:
            if not self._config.get(CONF_ORGANIZATION_ID):
                organization_id = await self.get_organization_id()
                self._config[CONF_ORGANIZATION_ID] = organization_id
        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get account info after login: %s", err)
            raise QuandifyAPIError("Failed to get account info after login") from err

        return self._config

    async def _refresh_token(self) -> bool:
        """Refresh the authentication token."""

        url = f"{AUTH_BASE_URL}/refresh"
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
            self._config[CONF_ID_TOKEN] = data["id_token"]
            self._config[CONF_REFRESH_TOKEN] = data["refresh_token"]

        return True

    async def _request(
        self,
        method: str,
        url: str,
        retry: bool = True,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Make an authenticated request to the Quandify API, refreshing the token if needed."""

        headers = {"Authorization": f"Bearer {self._config.get(CONF_ID_TOKEN)}"}
        response = {}

        try:
            response = await self.session.request(method, url, headers=headers, **kwargs)
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

    async def auth(self, account_id: str, password: str) -> dict[str, Any]:
        """Authenticate to the Quandify API."""
        url = f"{AUTH_BASE_URL}/"
        payload = {"account_id": account_id, "password": password}
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
        url = (
            f"{API_BASE_URL}/organization/{organization_id}/devices/"
        )
        response = await self._request("get", url)
        return response.get("data", [])

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get all info for a single device."""
        organization_id = self._config.get(CONF_ORGANIZATION_ID)
        url = (
            f"{API_BASE_URL}/organization/{organization_id}/devices/"
            f"{device_id}"
        )
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
