import json
import pytest
from yarl import URL

from custom_components.quandify.api import QuandifyAPI, QuandifyAPIError
from custom_components.quandify.const import (
    API_BASE_URL,
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_ORGANIZATION_ID,
)


@pytest.mark.asyncio
async def test_request_retries_after_refresh_token_on_401(
    aiohttp_session, aresponses, monkeypatch
):
    # Arrange: initial config with id_token and refresh_token
    config = {
        CONF_ID_TOKEN: "expired_token",
        CONF_REFRESH_TOKEN: "refresh_me",
        CONF_ORGANIZATION_ID: "org1",
    }
    api = QuandifyAPI(aiohttp_session, config)

    # Mock refresh to update the id token in-place
    async def fake_refresh():
        config[CONF_ID_TOKEN] = "new_token"
        return True

    monkeypatch.setattr(api, "_refresh_token", fake_refresh)

    # Endpoint we will call (GET a device info)
    path = "/organization/org1/devices/dev123"
    aresponses.add(
        URL(API_BASE_URL).host,
        path,
        "get",
        aresponses.Response(status=401, text="Unauthorized"),
    )
    aresponses.add(
        URL(API_BASE_URL).host,
        path,
        "get",
        aresponses.Response(status=200, text=json.dumps({"id": "dev123", "ok": True})),
    )

    # Act: make request via public helper
    data = await api.get_device_info("dev123")

    # Assert: second attempt succeeded and returned parsed JSON
    assert data == {"id": "dev123", "ok": True}
    assert config[CONF_ID_TOKEN] == "new_token"


@pytest.mark.asyncio
async def test_request_raises_on_non_json_error(aiohttp_session, aresponses):
    config = {CONF_ID_TOKEN: "t", CONF_REFRESH_TOKEN: "r", CONF_ORGANIZATION_ID: "org1"}
    api = QuandifyAPI(aiohttp_session, config)

    path = "/organization/org1/devices/dev123"
    aresponses.add(
        URL(API_BASE_URL).host,
        path,
        "get",
        aresponses.Response(status=500, text="server error"),
    )

    with pytest.raises(QuandifyAPIError):
        await api.get_device_info("dev123")
