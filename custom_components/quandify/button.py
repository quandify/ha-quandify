"""Button platform for Quandify integration."""

import logging
from typing import Any, Coroutine

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, HomeAssistantError

from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VALVE_UPDATE_DELAY
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

_LOGGER = logging.getLogger(__name__)

DEVICE_BUTTONS = {
    "Water Grip": ["acknowledge"],
    "CubicSecure": ["acknowledge", "open_valve", "close_valve"],
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the button entities based on device class."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []

    for device in coordinator.devices:
        if button_types := DEVICE_BUTTONS.get(device.model):
            if "acknowledge" in button_types:
                entities.append(QuandifyAcknowledgeLeakButton(coordinator, device))
            if "open_valve" in button_types:
                entities.append(QuandifyOpenValveButton(coordinator, device))
            if "close_valve" in button_types:
                entities.append(QuandifyCloseValveButton(coordinator, device))

    async_add_entities(entities)


class QuandifyButton(QuandifyEntity, ButtonEntity):
    """Base button entity for all Quandify devices."""

    _attr_entity_category = EntityCategory.CONFIG

    def press(self) -> None:
        pass


class QuandifyAcknowledgeLeakButton(QuandifyButton):
    """Represents the acknowledge leak button."""

    _attr_name = "Acknowledge leak"
    _attr_icon = "mdi:bell-cancel"

    def __init__(
        self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice
    ):
        """Initialize the button."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{self.device.id}_acknowledge_leak"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Acknowledging leak for device %s", self.device.id)
        try:
            await self.coordinator.api.acknowledge_leak(self.device.id)
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to acknowledge leak: %s", err)


class QuandifyOpenValveButton(QuandifyButton):
    """Represents the open valve button."""

    _attr_name = "Open valve"
    _attr_icon = "mdi:valve-open"

    def __init__(
        self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice
    ):
        """Initialize the button."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{self.device.id}_open_valve"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Opening valve for device %s", self.device.id)
        try:
            await self.coordinator.api.open_valve(self.device.id)
            # Schedule a refresh for later instead of an immediate one.
            async_call_later(
                self.hass, VALVE_UPDATE_DELAY, self.async_schedule_update_ha_state
            )
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to open valve: %s", err)
            raise HomeAssistantError("Failed to send open valve command") from err


class QuandifyCloseValveButton(QuandifyButton):
    """Represents the close valve button."""

    _attr_name = "Close valve"
    _attr_icon = "mdi:valve-closed"

    def __init__(
        self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice
    ):
        """Initialize the button."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{self.device.id}_close_valve"

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Closing valve for device %s", self.device.id)
        try:
            await self.coordinator.api.close_valve(self.device.id)
            # Schedule a refresh for later instead of an immediate one.
            async_call_later(
                self.hass, VALVE_UPDATE_DELAY, self.async_schedule_update_ha_state
            )
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to close valve: %s", err)
            raise HomeAssistantError("Failed to send close valve command") from err
