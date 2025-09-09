import pytest
from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)

from custom_components.quandify.sensor import QuandifySensor
from custom_components.quandify.models import QuandifyDevice


class DummyCoordinator:
    def __init__(self, data):
        self.data = data


@pytest.mark.asyncio
async def test_sensor_value_nested_extraction():
    device = QuandifyDevice(
        id="dev1",
        name="Name",
        model="Water Grip",
        serial=None,
        firmware_version=None,
        hardware_version=5,
    )
    desc = SensorEntityDescription(
        key="diagnostics.signal.rssi", name="RSSI", device_class=None, state_class=None
    )
    coord = DummyCoordinator(data={"dev1": {"diagnostics": {"signal": {"rssi": -60}}}})

    entity = QuandifySensor(coord, device, desc)
    entity._handle_coordinator_update()
    assert entity.native_value == -60


@pytest.mark.asyncio
async def test_sensor_value_for_sub_type_is_capitalized():
    device = QuandifyDevice(
        id="dev1",
        name="Name",
        model="Water Grip",
        serial=None,
        firmware_version=None,
        hardware_version=5,
    )
    desc = SensorEntityDescription(key="sub_type", name="Subtype")
    coord = DummyCoordinator(data={"dev1": {"sub_type": "waterfuse"}})

    entity = QuandifySensor(coord, device, desc)
    entity._handle_coordinator_update()
    assert entity.native_value == "Waterfuse"
