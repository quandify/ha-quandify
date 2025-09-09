import asyncio
import pytest
import aiohttp

@pytest.fixture
async def aiohttp_session():
    async with aiohttp.ClientSession() as session:
        yield session

class DummyCoordinator:
    def __init__(self):
        self.api = None
        self.data = {}
        self.last_update_success = True

    async def async_request_refresh(self):
        # mimic HA coordinator refresh call
        return None
