"""Binary sensor platform for Quandify integration."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

# Binary Sensor descriptions
LEAK_SENSOR = BinarySensorEntityDescription(
    key="leak_status.leak_state",
    name="Leak",
    device_class=BinarySensorDeviceClass.MOISTURE,
)

# Binary Sensor profiles
DEVICE_BINARY_SENSORS = {
    "Water Grip": [LEAK_SENSOR],
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the binary sensor entities."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[QuandifyBinarySensor] = []

    for device in coordinator.devices:
        if descriptions := DEVICE_BINARY_SENSORS.get(device.model):
            entities.extend(
                QuandifyBinarySensor(coordinator, device, description)
                for description in descriptions
            )
    async_add_entities(entities)


class QuandifyBinarySensor(QuandifyEntity, BinarySensorEntity):
    """Implementation of a Quandify binary sensor."""

    def __init__(
        self,
        coordinator: QuandifyDataUpdateCoordinator,
        device: QuandifyDevice,
        description: BinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        self._attr_unique_id = f"{self.device.id}_{self.entity_description.key}"
        self._update_attr()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attr()
        super()._handle_coordinator_update()

    def _update_attr(self) -> None:
        """Update the state of the binary sensor."""
        value = self.device_data
        if value is None:
            self._attr_is_on = None
            return

        try:
            for key_part in self.entity_description.key.split("."):
                if value is None:
                    break
                value = value.get(key_part)
        except AttributeError:
            value = None

        self._attr_is_on = value != "noLeak"
