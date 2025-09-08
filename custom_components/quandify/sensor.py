"""Sensor platform for Quandify integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

# Sensor descriptions
TOTAL_VOLUME = SensorEntityDescription(
    key="status.total_volume",
    name="Total volume",
    native_unit_of_measurement=UnitOfVolume.LITERS,
    state_class=SensorStateClass.TOTAL_INCREASING,
    device_class=SensorDeviceClass.WATER)

WATER_TEMP = SensorEntityDescription(
    key="status.avg_water_temp",
    name="Water temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.TEMPERATURE)

AMBIENT_TEMP = SensorEntityDescription(
    key="status.ambient_temp",
    name="Ambient temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.TEMPERATURE)

WIFI_SIGNAL = SensorEntityDescription(
    key="status.wifi_signal_strength",
    name="Signal strength",
    native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    state_class=SensorStateClass.MEASUREMENT)

RSSI_SIGNAL = SensorEntityDescription(
    key="status.rssi",
    name="Signal strength",
    native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    state_class=SensorStateClass.MEASUREMENT)

WATER_TYPE = SensorEntityDescription(
    key="sub_type",
    name="Water type",
    icon="mdi:water-thermometer")

# Sensor profiles
DEVICE_SENSORS = {
    "Water Grip": [TOTAL_VOLUME, WATER_TEMP, WIFI_SIGNAL, WATER_TYPE],
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the sensor entities."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[QuandifySensor] = []
    for device in coordinator.devices:
        if descriptions := DEVICE_SENSORS.get(device.model):
            entities.extend(
                QuandifySensor(coordinator, device, description) for description in descriptions
            )
    async_add_entities(entities)

class QuandifySensor(QuandifyEntity, SensorEntity):
    """Implementation of a Quandify sensor."""

    def __init__(self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice, description: SensorEntityDescription):
        """Initialize the sensor."""
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
        """Update the state and attributes of the entity."""
        value = self.device_data
        if value is None:
            self._attr_native_value = None
            return

        if self.entity_description.key == "sub_type":
            sub_type = value.get("sub_type")
            self._attr_native_value = sub_type.capitalize() if sub_type else None
        else:
            try:
                for key_part in self.entity_description.key.split("."):
                    if value is None:
                        break
                    value = value.get(key_part)
            except AttributeError:
                value = None
            self._attr_native_value = value
