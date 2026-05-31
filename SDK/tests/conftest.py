import pytest
import respx
from execra_sdk import ExecraClient

@pytest.fixture(scope="function")
async def client():
    client = ExecraClient()
    client.connect("http://localhost:8000", api_key="test-key")
    yield client
    await client.close()

@pytest.fixture
def mock_router():
    with respx.mock(base_url="http://localhost:8000") as respx_mock:
        yield respx_mock
