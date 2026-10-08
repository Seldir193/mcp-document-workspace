"""Transport tests against real processes: a stdio subprocess and a uvicorn server."""

import socket
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from mcp import Client, MCPError

from document_workspace.advanced import create_advanced_server
from document_workspace.host import NotificationRecorder, advanced_client, stdio_server_parameters
from document_workspace.serve import build_parser, build_server

pytestmark = pytest.mark.anyio

MODERN = "2026-07-28"
LEGACY = "2025-11-25"
PROGRESS_STEPS = [1, 2, 3]


@pytest.fixture
def root(tmp_path: Path) -> Path:
    (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")
    return tmp_path.resolve()


@pytest.fixture
def http_url(request: pytest.FixtureRequest) -> Iterator[str]:
    """Serve the advanced server with uvicorn; the param is the HTTP flag set."""
    flags: dict[str, bool] = getattr(request, "param", {})
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    app = create_advanced_server().streamable_http_app(**flags)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        assert time.monotonic() < deadline, "uvicorn did not start"
        time.sleep(0.02)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join(timeout=10)


async def analyze(client: Client, recorder: NotificationRecorder) -> None:
    result = await client.call_tool(
        "analyze_document", {"doc_id": "release-notes"}, progress_callback=recorder.on_progress
    )
    assert not result.is_error


async def test_cli_defaults_keep_the_basic_stdio_server() -> None:
    args = build_parser().parse_args([])

    assert (args.transport, args.advanced, args.stateless, args.json_response) == (
        "stdio",
        False,
        False,
        False,
    )
    async with Client(build_server(args)) as client:
        tools = await client.list_tools()
    assert [tool.name for tool in tools.tools] == ["edit_document"]


async def test_stdio_subprocess_default_server_is_unchanged() -> None:
    async with Client(stdio_server_parameters(sys.executable)) as client:
        tools = await client.list_tools()

    assert [tool.name for tool in tools.tools] == ["edit_document"]


@pytest.mark.parametrize(("mode", "version"), [("auto", MODERN), ("legacy", LEGACY)])
async def test_stdio_subprocess_serves_advanced_features(
    root: Path, mode: str, version: str
) -> None:
    recorder = NotificationRecorder()
    parameters = stdio_server_parameters(sys.executable, "--advanced")

    async with advanced_client(parameters, roots=[root], recorder=recorder, mode=mode) as client:
        assert client.protocol_version == version
        summary = await client.call_tool("summarize_document", {"doc_id": "release-notes"})
        listing = await client.call_tool("list_root_documents", {})
        await analyze(client, recorder)

    assert summary.content[0].text.startswith("Offline mode")
    assert [block.text for block in listing.content] == [str(root / "notes.md")]
    assert [step for step, _, _ in recorder.progress] == PROGRESS_STEPS
    assert len(recorder.logs) == 2


@pytest.mark.parametrize(("mode", "version"), [("auto", MODERN), ("legacy", LEGACY)])
async def test_stateful_http_serves_advanced_features(
    http_url: str, root: Path, mode: str, version: str
) -> None:
    recorder = NotificationRecorder()

    async with advanced_client(http_url, roots=[root], recorder=recorder, mode=mode) as client:
        assert client.protocol_version == version
        summary = await client.call_tool("summarize_document", {"doc_id": "release-notes"})
        denied = await client.call_tool("read_root_document", {"path": "../outside.md"})
        allowed = await client.call_tool("read_root_document", {"path": "notes.md"})
        await analyze(client, recorder)

    assert summary.content[0].text.startswith("Offline mode")
    assert denied.is_error
    assert allowed.content[0].text == "# Notes\n"
    assert [step for step, _, _ in recorder.progress] == PROGRESS_STEPS
    assert len(recorder.logs) == 2


@pytest.mark.parametrize("http_url", [{"stateless_http": True}], indirect=True)
async def test_stateless_http_modern_client_keeps_sampling_and_notifications(
    http_url: str, root: Path
) -> None:
    recorder = NotificationRecorder()

    async with advanced_client(http_url, roots=[root], recorder=recorder) as client:
        summary = await client.call_tool("summarize_document", {"doc_id": "release-notes"})
        await analyze(client, recorder)

    assert not summary.is_error
    assert [step for step, _, _ in recorder.progress] == PROGRESS_STEPS
    assert len(recorder.logs) == 2


@pytest.mark.parametrize("http_url", [{"stateless_http": True}], indirect=True)
async def test_stateless_http_legacy_client_has_no_back_channel(http_url: str, root: Path) -> None:
    async with advanced_client(http_url, roots=[root], mode="legacy") as client:
        with pytest.raises(MCPError):
            await client.call_tool("summarize_document", {"doc_id": "release-notes"})
        with pytest.raises(MCPError):
            await client.call_tool("list_root_documents", {})


@pytest.mark.parametrize("http_url", [{"json_response": True}], indirect=True)
@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_json_response_http_drops_notifications(http_url: str, root: Path, mode: str) -> None:
    recorder = NotificationRecorder()

    async with advanced_client(http_url, roots=[root], recorder=recorder, mode=mode) as client:
        await analyze(client, recorder)

    assert recorder.progress == []
    assert recorder.logs == []


@pytest.mark.parametrize("http_url", [{"json_response": True}], indirect=True)
async def test_json_response_http_modern_client_keeps_sampling_and_roots(
    http_url: str, root: Path
) -> None:
    async with advanced_client(http_url, roots=[root]) as client:
        summary = await client.call_tool("summarize_document", {"doc_id": "release-notes"})
        listing = await client.call_tool("list_root_documents", {})

    assert not summary.is_error
    assert [block.text for block in listing.content] == [str(root / "notes.md")]
