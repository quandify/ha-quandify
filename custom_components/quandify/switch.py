"""Switch platform for Quandify integration."""

from typing import Any
import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

_LOGGER = logging.getLogger(__name__)

VALVE_SUPPORTING_DEVICES = ["CubicSecure"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch entities based on device class."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[QuandifyValveSwitch] = []

    for device in coordinator.devices:
        if device.model in VALVE_SUPPORTING_DEVICES:
            entities.append(QuandifyValveSwitch(coordinator, device))

    async_add_entities(entities)


class QuandifyValveSwitch(QuandifyEntity, SwitchEntity):
    """Represents the main valve switch for a Quandify device."""

    _attr_name = "Valve"
    _attr_icon = "mdi:valve"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: QuandifyDataUpdateCoordinator,
        device: QuandifyDevice,
    ):
        """Initialize the valve switch."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{self.device.id}_valve"
        self._update_attr()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attr()
        super()._handle_coordinator_update()

    def _update_attr(self) -> None:
        """Update the state of the switch based on the coordinator data."""
        device_data = self.device_data
        valve_state = None

        if device_data and "status" in device_data:
            valve_state = device_data["status"].get("valve_state")

        if valve_state is None:
            self._attr_is_on = None
        else:
            self._attr_is_on = valve_state == "open"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on (open the valve)."""
        _LOGGER.info("Opening valve for device %s", self.device.id)
        try:
            await self.coordinator.api.open_valve(self.device.id)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to open valve for device %s: %s", self.device.id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off (close the valve)."""
        _LOGGER.info("Closing valve for device %s", self.device.id)
        try:
            await self.coordinator.api.close_valve(self.device.id)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to close valve for device %s: %s", self.device.id, err
            )
