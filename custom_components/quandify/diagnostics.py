"""Diagnostics support for Quandify integration."""
from __future__ import annotations
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ID_TOKEN, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Redact sensitive information
    redacted_data = dict(entry.data)
    if CONF_ID_TOKEN in redacted_data:
        redacted_data[CONF_ID_TOKEN] = "**REDACTED**"
    if CONF_REFRESH_TOKEN in redacted_data:
        redacted_data[CONF_REFRESH_TOKEN] = "**REDACTED**"

    return {
        "entry": {
            "title": entry.title,
            "data": redacted_data,
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "data": coordinator.data,
        },
    }
