from collections.abc import AsyncIterator

import pytest
from mcp import Client

from document_workspace import DocumentStore, create_server


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def store() -> DocumentStore:
    return DocumentStore()


@pytest.fixture
async def client(store: DocumentStore) -> AsyncIterator[Client]:
    """An MCP client connected in-process to a server over a fresh store."""
    async with Client(create_server(store)) as connected:
        yield connected
