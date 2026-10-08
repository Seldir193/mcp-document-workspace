"""Advanced MCP features through a real client session, in both protocol eras.

``legacy`` forces the initialize handshake (server-to-client requests);
``auto`` negotiates 2026-07-28 in-process (``InputRequiredResult`` round trips).
"""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp import Client, MCPError
from mcp.types import CreateMessageRequestParams

from document_workspace import DocumentStore
from document_workspace.advanced import (
    SUMMARY_MAX_TOKENS,
    SUMMARY_SYSTEM_PROMPT,
    create_advanced_server,
)
from document_workspace.host import NotificationRecorder, advanced_client

pytestmark = pytest.mark.anyio

ADVANCED_TOOLS = [
    "analyze_document",
    "edit_document",
    "list_root_documents",
    "read_root_document",
    "summarize_document",
]


@pytest.fixture(params=["legacy", "auto"])
def mode(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def root(tmp_path: Path) -> Path:
    approved = tmp_path / "approved"
    approved.mkdir()
    (approved / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (approved / "data.json").write_text("{}", encoding="utf-8")
    (tmp_path / "secret.md").write_text("secret\n", encoding="utf-8")
    return approved.resolve()


@pytest.fixture
def recorder() -> NotificationRecorder:
    return NotificationRecorder()


@pytest.fixture
async def advanced(
    store: DocumentStore, root: Path, recorder: NotificationRecorder, mode: str
) -> AsyncIterator[Client]:
    server = create_advanced_server(store)
    async with advanced_client(server, roots=[root], recorder=recorder, mode=mode) as connected:
        yield connected


def text_of(result) -> str:
    return result.content[0].text


async def test_advanced_tools_are_listed_without_resolver_parameters(advanced: Client) -> None:
    result = await advanced.list_tools()

    tools = {tool.name: tool for tool in result.tools}
    assert sorted(tools) == ADVANCED_TOOLS
    assert set(tools["summarize_document"].input_schema["properties"]) == {"doc_id"}
    assert set(tools["read_root_document"].input_schema["properties"]) == {"path"}
    assert tools["list_root_documents"].input_schema.get("properties", {}) == {}


async def test_summarize_document_samples_the_client_model(
    store: DocumentStore, mode: str
) -> None:
    seen: list[CreateMessageRequestParams] = []

    async def model(params: CreateMessageRequestParams) -> str:
        seen.append(params)
        return "A summary from the client's model."

    async with advanced_client(create_advanced_server(store), model=model, mode=mode) as client:
        result = await client.call_tool("summarize_document", {"doc_id": "meeting-notes"})

    assert not result.is_error
    assert text_of(result) == "A summary from the client's model."
    assert len(seen) == 1
    assert seen[0].max_tokens == SUMMARY_MAX_TOKENS
    assert seen[0].system_prompt == SUMMARY_SYSTEM_PROMPT
    assert store.get("meeting-notes").content in seen[0].messages[0].content.text


async def test_summarize_document_with_default_extractive_model(advanced: Client) -> None:
    result = await advanced.call_tool("summarize_document", {"doc_id": "release-notes"})

    assert not result.is_error
    assert text_of(result).startswith("Offline mode for the mobile app.")


async def test_summarize_unknown_document_is_a_tool_error(advanced: Client) -> None:
    result = await advanced.call_tool("summarize_document", {"doc_id": "missing"})

    assert result.is_error
    assert "not found" in text_of(result)


async def test_summarize_requires_a_sampling_capable_client(
    store: DocumentStore, mode: str
) -> None:
    async with Client(create_advanced_server(store), mode=mode) as client:
        with pytest.raises(MCPError, match="did not declare the sampling capability"):
            await client.call_tool("summarize_document", {"doc_id": "release-notes"})


async def test_prompt_is_still_retrieval_only(advanced: Client) -> None:
    result = await advanced.get_prompt("summarize", {"doc_id": "release-notes"})

    assert result.messages[0].role == "user"
    assert "Summarize the document" in result.messages[0].content.text


async def test_lists_documents_in_approved_root(advanced: Client, root: Path) -> None:
    result = await advanced.call_tool("list_root_documents", {})

    assert not result.is_error
    assert [block.text for block in result.content] == [str(root / "notes.md")]


@pytest.mark.parametrize("relative", [True, False])
async def test_reads_document_inside_approved_root(
    advanced: Client, root: Path, relative: bool
) -> None:
    path = "notes.md" if relative else str(root / "notes.md")

    result = await advanced.call_tool("read_root_document", {"path": path})

    assert not result.is_error
    assert text_of(result) == "# Notes\n"


async def test_traversal_out_of_root_is_denied(advanced: Client) -> None:
    result = await advanced.call_tool("read_root_document", {"path": "../secret.md"})

    assert result.is_error
    assert "outside the approved roots" in text_of(result)
    assert "secret\n" not in text_of(result)


async def test_absolute_path_outside_root_is_denied(advanced: Client, root: Path) -> None:
    outside = str(root.parent / "secret.md")

    result = await advanced.call_tool("read_root_document", {"path": outside})

    assert result.is_error
    assert "outside the approved roots" in text_of(result)


async def test_non_text_file_inside_root_is_denied(advanced: Client) -> None:
    result = await advanced.call_tool("read_root_document", {"path": "data.json"})

    assert result.is_error
    assert "not a Markdown or text document" in text_of(result)


async def test_client_approving_no_roots_is_denied(
    store: DocumentStore, root: Path, mode: str
) -> None:
    async with advanced_client(create_advanced_server(store), roots=[], mode=mode) as client:
        result = await client.call_tool("read_root_document", {"path": str(root / "notes.md")})

    assert result.is_error
    assert "not approved any roots" in text_of(result)


async def test_roots_tools_require_a_roots_capable_client(
    store: DocumentStore, root: Path, mode: str
) -> None:
    async with Client(create_advanced_server(store), mode=mode) as client:
        with pytest.raises(MCPError, match="did not declare the roots capability"):
            await client.call_tool("read_root_document", {"path": str(root / "notes.md")})


async def test_analyze_document_reports_logs_and_progress(
    advanced: Client, recorder: NotificationRecorder
) -> None:
    result = await advanced.call_tool(
        "analyze_document", {"doc_id": "release-notes"}, progress_callback=recorder.on_progress
    )

    assert not result.is_error
    assert result.structured_content == {
        "doc_id": "release-notes",
        "lines": 9,
        "words": 31,
        "headings": ["Release Notes 1.4", "Highlights", "Fixes"],
        "list_items": 4,
    }
    assert recorder.progress == [
        (1, 3, "Counting lines and words"),
        (2, 3, "Extracting headings"),
        (3, 3, "Counting list items"),
    ]
    assert recorder.logs == [
        ("info", "Analyzing 'release-notes'"),
        ("info", "Finished 'release-notes'"),
    ]


async def test_analyze_unknown_document_is_a_tool_error(advanced: Client) -> None:
    result = await advanced.call_tool("analyze_document", {"doc_id": "missing"})

    assert result.is_error
    assert "not found" in text_of(result)
