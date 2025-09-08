"""Base entity for the Quandify integration."""
from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .models import QuandifyDevice


class QuandifyEntity(CoordinatorEntity[QuandifyDataUpdateCoordinator]):
    """Base class for all Quandify entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.device = device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.device.id)},
            "name": self.device.name,
            "manufacturer": "Quandify",
            "model": self.device.model,
            "serial_number": self.device.serial,
            "sw_version": self.device.firmware_version,
        }

    @property
    def device_data(self) -> dict[str, Any] | None:
        """Return the latest data for this entity's device."""
        return self.coordinator.data.get(self.device.id)
