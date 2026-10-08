"""Advanced MCP tools: sampling, roots-scoped file access, logging and progress.

Sampling and roots are client features, so the server has to ask the client
for them. Both are requested through ``Resolve(...)`` resolvers instead of
calling ``ctx.session.create_message()`` / ``list_roots()`` directly: the SDK
then picks the mechanism the negotiated protocol allows. On 2025-era
(handshake) connections it sends a server-to-client request mid-call; on
2026-07-28 connections, where servers may not send requests, it returns an
``InputRequiredResult`` and the client retries the call with the answers.
"""

from typing import Annotated

import anyio
from mcp.server.mcpserver import Context, ListRoots, MCPServer, Resolve, Sample
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import (
    CreateMessageResult,
    ListRootsResult,
    SamplingMessage,
    TextContent,
    ToolAnnotations,
)
from pydantic import BaseModel

from document_workspace.roots import (
    RootAccessError,
    list_text_documents,
    read_text_document,
    roots_from_uris,
)
from document_workspace.server import create_server
from document_workspace.store import Document, DocumentNotFoundError, DocumentStore

SUMMARY_MAX_TOKENS = 300
SUMMARY_SYSTEM_PROMPT = "You summarize documents faithfully and concisely."
ANALYSIS_LOGGER = "document-workspace.analysis"

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=False,
)


class DocumentAnalysis(BaseModel):
    doc_id: str
    lines: int
    words: int
    headings: list[str]
    list_items: int


def create_advanced_server(
    store: DocumentStore | None = None, *, step_delay: float = 0.0
) -> MCPServer:
    """Build the base server plus the advanced tools.

    ``step_delay`` pauses between analysis steps so progress is visible in a demo.
    """
    store = store if store is not None else DocumentStore()
    mcp = create_server(store)
    _register_sampling_tool(mcp, store)
    _register_roots_tools(mcp)
    _register_analysis_tool(mcp, store, step_delay)
    return mcp


def _get_document(store: DocumentStore, doc_id: str) -> Document:
    try:
        return store.get(doc_id)
    except DocumentNotFoundError as error:
        raise ToolError(str(error)) from error


def _register_sampling_tool(mcp: MCPServer, store: DocumentStore) -> None:
    def request_summary(doc_id: str) -> Sample:
        """Ask the client's model for a summary; the server holds no model key."""
        document = _get_document(store, doc_id)
        prompt = (
            f"Summarize the document '{document.title}' in three sentences or fewer.\n\n"
            f'<document id="{document.id}">\n{document.content}\n</document>'
        )
        return Sample(
            [SamplingMessage(role="user", content=TextContent(text=prompt))],
            max_tokens=SUMMARY_MAX_TOKENS,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
        )

    @mcp.tool(title="Summarize document (sampling)", annotations=READ_ONLY)
    def summarize_document(
        doc_id: str,
        sampled: Annotated[CreateMessageResult, Resolve(request_summary)],
    ) -> str:
        """Summarize a document using the connected client's model via MCP sampling.

        Unlike the ``summarize`` prompt, which only returns prompt text for the
        host to run, this tool gets the finished summary back from the client.
        """
        if not isinstance(sampled.content, TextContent):
            raise ToolError("The client returned a non-text sampling result")
        return sampled.content.text


def _register_roots_tools(mcp: MCPServer) -> None:
    def client_roots() -> ListRoots:
        """Ask the client which filesystem roots it approves, on every call."""
        return ListRoots()

    @mcp.tool(title="List documents in approved roots", annotations=READ_ONLY)
    def list_root_documents(
        approved: Annotated[ListRootsResult, Resolve(client_roots)],
    ) -> list[str]:
        """List Markdown/text files inside the roots the client approved."""
        try:
            roots = roots_from_uris(str(root.uri) for root in approved.roots)
            return [str(path) for path in list_text_documents(roots)]
        except RootAccessError as error:
            raise ToolError(str(error)) from error

    @mcp.tool(title="Read a document from an approved root", annotations=READ_ONLY)
    def read_root_document(
        path: str,
        approved: Annotated[ListRootsResult, Resolve(client_roots)],
    ) -> str:
        """Read one Markdown/text file; the path must resolve inside an approved root."""
        try:
            roots = roots_from_uris(str(root.uri) for root in approved.roots)
            return read_text_document(path, roots)
        except RootAccessError as error:
            raise ToolError(str(error)) from error


def _register_analysis_tool(mcp: MCPServer, store: DocumentStore, step_delay: float) -> None:
    @mcp.tool(title="Analyze document (logging + progress)", annotations=READ_ONLY)
    async def analyze_document(doc_id: str, ctx: Context) -> DocumentAnalysis:
        """Analyze a document step by step, emitting log messages and progress."""
        document = _get_document(store, doc_id)
        lines = document.content.splitlines()
        steps = [
            ("Counting lines and words", lambda: _count_words(document.content)),
            (
                "Extracting headings",
                lambda: [line.lstrip("# ").strip() for line in lines if line.startswith("#")],
            ),
            (
                "Counting list items",
                lambda: sum(1 for line in lines if _is_list_item(line)),
            ),
        ]
        results = []
        await ctx.info(f"Analyzing '{document.id}'", logger_name=ANALYSIS_LOGGER)
        for index, (label, compute) in enumerate(steps, start=1):
            await anyio.sleep(step_delay)
            results.append(compute())
            await ctx.report_progress(index, len(steps), label)
        words, headings, list_items = results
        await ctx.info(f"Finished '{document.id}'", logger_name=ANALYSIS_LOGGER)
        return DocumentAnalysis(
            doc_id=document.id,
            lines=len(lines),
            words=words,
            headings=headings,
            list_items=list_items,
        )


def _count_words(text: str) -> int:
    return sum(1 for token in text.split() if any(char.isalnum() for char in token))


def _is_list_item(line: str) -> bool:
    stripped = line.lstrip()
    marker, _, rest = stripped.partition(" ")
    return bool(rest) and (marker in {"-", "*"} or marker.rstrip(".").isdigit())
