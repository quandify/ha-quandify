import pytest
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from custom_components.quandify.binary_sensor import QuandifyBinarySensor
from custom_components.quandify.models import QuandifyDevice


class DummyCoordinator:
    def __init__(self, data):
        self.data = data


@pytest.mark.asyncio
async def test_binary_sensor_updates_boolean_state(monkeypatch):
    device = QuandifyDevice(
        id="dev1",
        name="Name",
        model="Water Grip",
        serial=None,
        firmware_version=None,
        hardware_version=5,
    )
    desc = BinarySensorEntityDescription(key="state.valve_open", name="Valve Open")
    coord = DummyCoordinator(data={"dev1": {"state": {"valve_open": True}}})

    entity = QuandifyBinarySensor(coord, device, desc)
    # simulate coordinator update call
    entity._handle_coordinator_update()
    assert entity.is_on is True

    coord.data["dev1"]["state"]["valve_open"] = False
    entity._handle_coordinator_update()
    assert entity.is_on is False
