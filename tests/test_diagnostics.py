import types
import pytest

from custom_components.quandify.diagnostics import async_get_config_entry_diagnostics
from custom_components.quandify.const import DOMAIN, CONF_ID_TOKEN, CONF_REFRESH_TOKEN


class DummyEntry:
    def __init__(self, title, data, options=None, entry_id="entry123"):
        self.title = title
        self.data = data
        self.options = options or {}
        self.entry_id = entry_id


class DummyHass(dict):
    pass


class DummyCoordinator:
    def __init__(self):
        self.last_update_success = True
        self.data = {"dev1": {"ok": True}}


@pytest.mark.asyncio
async def test_diagnostics_redacts_tokens():
    hass = DummyHass()
    entry = DummyEntry(
        title="Quandify",
        data={
            CONF_ID_TOKEN: "abc123",
            CONF_REFRESH_TOKEN: "zzz999",
            "email": "u@example.com",
        },
    )
    hass[DOMAIN] = {entry.entry_id: DummyCoordinator()}
    result = await async_get_config_entry_diagnostics(hass, entry)

    # tokens should be redacted
    redacted = result["entry"]["data"]
    assert redacted[CONF_ID_TOKEN] == "**REDACTED**"
    assert redacted[CONF_REFRESH_TOKEN] == "**REDACTED**"
    # structure should include coordinator state
    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["data"] == {"dev1": {"ok": True}}
