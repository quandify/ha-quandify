"""Sensor platform for Quandify integration."""

from datetime import datetime, timedelta
from typing import Any

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
from homeassistant.util import dt as dt_util

from .const import DOMAIN, EXTENDED_CONSUMPTION_BUCKET_DELAY_MINUTES
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

# Sensor descriptions
TOTAL_VOLUME = SensorEntityDescription(
    key="status.total_volume",
    name="Total volume",
    native_unit_of_measurement=UnitOfVolume.LITERS,
    state_class=SensorStateClass.TOTAL_INCREASING,
    device_class=SensorDeviceClass.WATER,
)

WATER_TEMP = SensorEntityDescription(
    key="status.avg_water_temp",
    name="Water temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.TEMPERATURE,
)

AMBIENT_TEMP = SensorEntityDescription(
    key="status.ambient_temp",
    name="Ambient temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
    device_class=SensorDeviceClass.TEMPERATURE,
)

WIFI_SIGNAL = SensorEntityDescription(
    key="status.wifi_signal_strength",
    name="Signal strength",
    native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    state_class=SensorStateClass.MEASUREMENT,
)

RSSI_SIGNAL = SensorEntityDescription(
    key="status.rssi",
    name="Signal strength",
    native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
    state_class=SensorStateClass.MEASUREMENT,
)

WATER_TYPE = SensorEntityDescription(
    key="sub_type",
    name="Water type",
    icon="mdi:water-thermometer",
)

LEAK_STATE = SensorEntityDescription(
    key="quandify_extended.leak_status.leak_state",
    name="Leak state",
    icon="mdi:pipe-leak",
)

LEAK_MEAN_FLOW = SensorEntityDescription(
    key="quandify_extended.leak_status.mean_flow_lph",
    name="Leak mean flow rate",
    native_unit_of_measurement="L/h",
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:waves-arrow-right",
)

LEAK_UPDATED_AT = SensorEntityDescription(
    key="quandify_extended.leak_status.updated_at",
    name="Leak status updated",
    device_class=SensorDeviceClass.TIMESTAMP,
    icon="mdi:clock-alert-outline",
)

CURRENT_FIRMWARE = SensorEntityDescription(
    key="quandify_extended.firmware_version.currentVersion",
    name="Current firmware",
    icon="mdi:chip",
)

LATEST_FIRMWARE = SensorEntityDescription(
    key="quandify_extended.firmware_version.latestVersion",
    name="Latest firmware",
    icon="mdi:update",
)

HOURLY_CONSUMPTION = SensorEntityDescription(
    key="quandify_extended.detailed_consumption_hourly",
    name="Latest hourly consumption",
    native_unit_of_measurement=UnitOfVolume.LITERS,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:chart-bar",
)

# Sensor profiles
DEVICE_SENSORS = {
    "Water Grip": [
        TOTAL_VOLUME,
        WATER_TEMP,
        WIFI_SIGNAL,
        WATER_TYPE,
        LEAK_STATE,
        LEAK_MEAN_FLOW,
        LEAK_UPDATED_AT,
        CURRENT_FIRMWARE,
        LATEST_FIRMWARE,
        HOURLY_CONSUMPTION,
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
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

    def __init__(
        self,
        coordinator: QuandifyDataUpdateCoordinator,
        device: QuandifyDevice,
        description: SensorEntityDescription,
    ) -> None:
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
        elif self.entity_description.key == "quandify_extended.leak_status.updated_at":
            timestamp = self._get_nested_value(value, self.entity_description.key)
            self._attr_native_value = self._timestamp_to_datetime(timestamp)
        elif self.entity_description.key == "quandify_extended.detailed_consumption_hourly":
            detailed_consumption = self._get_nested_value(
                value, self.entity_description.key
            )
            self._update_hourly_consumption(detailed_consumption)
        else:
            self._attr_native_value = self._get_nested_value(
                value, self.entity_description.key
            )

    @staticmethod
    def _get_nested_value(data: dict[str, Any], key: str) -> Any:
        """Get a nested value from a dictionary using a dot separated key."""
        value: Any = data
        try:
            for key_part in key.split("."):
                if value is None:
                    break
                value = value.get(key_part)
        except AttributeError:
            value = None
        return value

    @staticmethod
    def _timestamp_to_datetime(timestamp: Any) -> datetime | None:
        """Convert a Unix timestamp to a timezone-aware datetime."""
        if timestamp in (None, "unknown", "unavailable", ""):
            return None
        try:
            return dt_util.as_local(dt_util.utc_from_timestamp(float(timestamp)))
        except (TypeError, ValueError):
            return None

    def _update_hourly_consumption(self, detailed_consumption: Any) -> None:
        """Update hourly consumption sensor value and attributes.

        The Quandify detailed consumption endpoint can return separate rows for
        hot, cold and unknown water at the same timestamp. Group the latest 24
        hourly buckets into a compact `hourly_total` attribute that is easier to
        use for Home Assistant charts and small enough for the recorder.

        The `datetime` field is kept as provided by the Quandify API. For easier
        use in dashboards, the integration also exposes `bucket_start` and
        `bucket_end` based on the observed hourly bucket start timestamp. The
        most recent bucket is ignored for a short delay after its end time so
        partially updated API data does not temporarily replace the latest value
        with zero.
        """
        if not isinstance(detailed_consumption, dict):
            self._attr_native_value = None
            self._attr_extra_state_attributes = {}
            return

        data = detailed_consumption.get("data") or []
        period = detailed_consumption.get("period") or {}

        if not isinstance(data, list):
            data = []

        grouped_by_timestamp: dict[Any, dict[str, Any]] = {}
        bucket_cutoff_datetime = dt_util.now() - timedelta(
            minutes=EXTENDED_CONSUMPTION_BUCKET_DELAY_MINUTES
        )

        for item in data:
            if not isinstance(item, dict):
                continue

            timestamp = item.get("ts")
            value = item.get("value")
            water_type = item.get("type") or "unknown"
            timestamp_datetime = self._timestamp_to_datetime(timestamp)
            bucket_start_datetime = timestamp_datetime
            bucket_end_datetime = (
                bucket_start_datetime + timedelta(hours=1)
                if bucket_start_datetime
                else None
            )

            if bucket_end_datetime and bucket_end_datetime > bucket_cutoff_datetime:
                continue

            try:
                value_liters = float(value)
            except (TypeError, ValueError):
                continue

            grouped = grouped_by_timestamp.setdefault(
                timestamp,
                {
                    "ts": timestamp,
                    "datetime": timestamp_datetime.isoformat()
                    if timestamp_datetime
                    else None,
                    "bucket_start": bucket_start_datetime.isoformat()
                    if bucket_start_datetime
                    else None,
                    "bucket_end": bucket_end_datetime.isoformat()
                    if bucket_end_datetime
                    else None,
                    "hot_liter": 0.0,
                    "cold_liter": 0.0,
                    "unknown_liter": 0.0,
                    "total_liter": 0.0,
                },
            )

            if water_type == "hot":
                grouped["hot_liter"] += value_liters
            elif water_type == "cold":
                grouped["cold_liter"] += value_liters
            else:
                grouped["unknown_liter"] += value_liters

            grouped["total_liter"] += value_liters

        hourly_total = [
            {
                **item,
                "hot_liter": round(item["hot_liter"], 3),
                "cold_liter": round(item["cold_liter"], 3),
                "unknown_liter": round(item["unknown_liter"], 3),
                "total_liter": round(item["total_liter"], 3),
            }
            for item in sorted(
                grouped_by_timestamp.values(), key=lambda item: item["ts"] or 0
            )
        ]

        hourly_total = hourly_total[-24:]
        latest_total = hourly_total[-1]["total_liter"] if hourly_total else None
        self._attr_native_value = latest_total
        self._attr_extra_state_attributes = {
            "hourly_total": hourly_total,
            "period": period,
            "raw_row_count": len(data),
            "hourly_total_count": len(hourly_total),
            "bucket_delay_minutes": EXTENDED_CONSUMPTION_BUCKET_DELAY_MINUTES,
        }
