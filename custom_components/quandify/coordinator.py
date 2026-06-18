"""DataUpdateCoordinator for the Quandify integration."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QuandifyAPI
from .const import (
    DOMAIN,
    EXTENDED_CONSUMPTION_LOOKBACK_HOURS,
    UPDATE_INTERVAL_MINUTES,
)
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

                # Request the latest hourly buckets on the normal coordinator
                # polling interval. Home Assistant's configured time zone is
                # passed to the API so bucket timestamps match the local UI.
                now_ts = int(datetime.now().timestamp())
                from_ts = now_ts - EXTENDED_CONSUMPTION_LOOKBACK_HOURS * 60 * 60
                timezone = self.hass.config.time_zone

                for device in self.devices:
                    device_info = await self.api.get_device_info(device.id)

                    # Keep optional endpoint failures isolated from the main
                    # coordinator update. A temporary failure in historical
                    # consumption or diagnostics should not make the device
                    # unavailable in Home Assistant.
                    extended_data: dict[str, Any] = {}

                    try:
                        extended_data["detailed_consumption_hourly"] = (
                            await self.api.get_device_detailed_consumption(
                                device.id,
                                from_ts=from_ts,
                                to_ts=now_ts,
                                truncate="hour",
                                timezone=timezone,
                            )
                        )
                    except Exception as exception:  # noqa: BLE001
                        _LOGGER.debug(
                            "Failed to fetch detailed consumption for %s: %s",
                            device.id,
                            exception,
                        )

                    try:
                        extended_data["leak_status"] = (
                            await self.api.get_device_leak_status(device.id)
                        )
                    except Exception as exception:  # noqa: BLE001
                        _LOGGER.debug(
                            "Failed to fetch leak status for %s: %s",
                            device.id,
                            exception,
                        )

                    try:
                        extended_data["firmware_version"] = (
                            await self.api.get_device_firmware_version(device.id)
                        )
                    except Exception as exception:  # noqa: BLE001
                        _LOGGER.debug(
                            "Failed to fetch firmware version for %s: %s",
                            device.id,
                            exception,
                        )

                    if extended_data:
                        device_info["quandify_extended"] = extended_data

                    data[device.id] = device_info
                return data
        except Exception as exception:
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
