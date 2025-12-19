"""DataUpdateCoordinator for the Quandify integration."""

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QuandifyAPI
from .const import DOMAIN, UPDATE_INTERVAL_MINUTES
from .models import QuandifyDevice

_LOGGER = logging.getLogger(__name__)


class QuandifyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self, hass: HomeAssistant, api: QuandifyAPI, devices: list[QuandifyDevice]
    ):
        """Initialize."""
        self.api = api
        self.devices = devices
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library by polling."""
        try:
            async with asyncio.timeout(30):
                data = {}
                for device in self.devices:
                    device_info = await self.api.get_device_info(device.id)
                    data[device.id] = device_info
                return data
        except Exception as exception:
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
