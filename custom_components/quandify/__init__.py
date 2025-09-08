"""The Quandify integration."""
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuandifyAPI, QuandifyAPIError
from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .models import QuandifyDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quandify devices from a config entry."""
    session = async_get_clientsession(hass)
    api = QuandifyAPI(session, dict(entry.data))

    try:
        raw_devices = await api.get_devices()
        devices = []
        for device_data in raw_devices:
            device = QuandifyDevice.from_api(device_data)
            if device is not None:
                devices.append(device)

    except (aiohttp.ClientError, ValueError, QuandifyAPIError) as err:
        _LOGGER.error("Failed to set up Quandify integration during device fetch: %s", err)
        raise ConfigEntryNotReady(f"Failed to get devices: {err}") from err

    coordinator = QuandifyDataUpdateCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
