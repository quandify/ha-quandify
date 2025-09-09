import pytest

from custom_components.quandify.models import QuandifyDevice


def test_quandify_device_from_api_maps_water_grip_v5():
    data = {
        "id": "dev123",
        "serial": "SN001",
        "firmware_version": "1.2.3",
        "hardware_version": 5,
        "node": {"type": "waterfuse", "name": "Kitchen Valve"},
    }
    device = QuandifyDevice.from_api(data)
    assert device is not None
    assert device.id == "dev123"
    assert device.name == "Kitchen Valve"
    assert device.model == "Water Grip"
    assert device.serial == "SN001"
    assert device.firmware_version == "1.2.3"
    assert device.hardware_version == 5


@pytest.mark.parametrize(
    "hardware_version,node_type,expected",
    [
        (None, "waterfuse", None),
        (4, "waterfuse", None),
        (5, "other_type", None),
    ],
)
def test_quandify_device_from_api_returns_none_for_unsupported(
    hardware_version, node_type, expected
):
    data = {
        "id": "devX",
        "serial": None,
        "firmware_version": None,
        "hardware_version": hardware_version,
        "node": {"type": node_type, "name": "Unknown Device"},
    }
    device = QuandifyDevice.from_api(data)
    assert device is expected
