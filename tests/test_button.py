import pytest
from types import SimpleNamespace

from custom_components.quandify.button import (
    QuandifyAcknowledgeLeakButton,
    QuandifyOpenValveButton,
    QuandifyCloseValveButton,
)
from custom_components.quandify.models import QuandifyDevice


class DummyCoordinator:
    def __init__(self):
        self.api = SimpleNamespace(
            acknowledge_leak=pytest.AsyncMock(),
            open_valve=pytest.AsyncMock(),
            close_valve=pytest.AsyncMock(),
        )
        self.async_request_refresh = pytest.AsyncMock()


@pytest.mark.asyncio
async def test_acknowledge_button_calls_api_and_refresh(monkeypatch):
    coord = DummyCoordinator()
    device = QuandifyDevice(
        id="dev1",
        name="Name",
        model="Water Grip",
        serial=None,
        firmware_version=None,
        hardware_version=5,
    )
    btn = QuandifyAcknowledgeLeakButton(coord, device)
    await btn.async_press()
    coord.api.acknowledge_leak.assert_awaited_once_with("dev1")
    coord.async_request_refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_open_close_buttons_call_api_and_refresh():
    coord = DummyCoordinator()
    device = QuandifyDevice(
        id="dev1",
        name="Name",
        model="Water Grip",
        serial=None,
        firmware_version=None,
        hardware_version=5,
    )

    open_btn = QuandifyOpenValveButton(coord, device)
    await open_btn.async_press()
    coord.api.open_valve.assert_awaited_once_with("dev1")

    close_btn = QuandifyCloseValveButton(coord, device)
    await close_btn.async_press()
    coord.api.close_valve.assert_awaited_once_with("dev1")
    assert coord.async_request_refresh.await_count == 2
