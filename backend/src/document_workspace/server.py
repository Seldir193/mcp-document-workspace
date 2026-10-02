"""MCP server definition: resources, the edit tool, and prompts."""

from __future__ import annotations

import json

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import ToolAnnotations

from document_workspace.store import DocumentNotFoundError, DocumentStore, EditError

SERVER_NAME = "document-workspace"

INSTRUCTIONS = (
    "Read docs://documents to discover documents, then docs://documents/{doc_id} "
    "to read one. Use edit_document for targeted changes."
)


def create_server(store: DocumentStore | None = None) -> MCPServer:
    """Build an MCP server bound to ``store`` (a fresh sample store by default)."""
    store = store if store is not None else DocumentStore()
    mcp = MCPServer(SERVER_NAME, instructions=INSTRUCTIONS)

    @mcp.resource(
        "docs://documents",
        name="documents",
        title="Documents",
        description="Index of all documents with their ids and titles.",
        mime_type="application/json",
    )
    def list_documents() -> str:
        index = [
            {"id": doc.id, "title": doc.title, "uri": f"docs://documents/{doc.id}"}
            for doc in store.list()
        ]
        return json.dumps(index, indent=2)

    @mcp.resource(
        "docs://documents/{doc_id}",
        name="document",
        title="Document",
        description="Full text content of a single document.",
        mime_type="text/markdown",
    )
    def read_document(doc_id: str) -> str:
        try:
            return store.get(doc_id).content
        except DocumentNotFoundError as error:
            raise ResourceNotFoundError(str(error)) from error

    @mcp.tool(
        title="Edit document",
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=False,
            open_world_hint=False,
        ),
    )
    def edit_document(doc_id: str, old_text: str, new_text: str) -> str:
        """Replace one exact passage of a document.

        old_text must match exactly once in the document, including whitespace;
        otherwise the edit is rejected and nothing changes.
        """
        try:
            document = store.replace_text(doc_id, old_text, new_text)
        except (DocumentNotFoundError, EditError) as error:
            raise ToolError(str(error)) from error
        return f"Updated '{document.id}' ({len(document.content)} characters)."

    @mcp.prompt(title="Summarize document")
    def summarize(doc_id: str) -> str:
        """Summarize a document in a few sentences."""
        document = store.get(doc_id)
        return (
            f"Summarize the document '{document.title}' in three sentences or fewer. "
            "Cover the main points only and do not add information that is not in the text.\n\n"
            f"<document id=\"{document.id}\">\n{document.content}\n</document>"
        )

    @mcp.prompt(name="format", title="Format document")
    def format_document(doc_id: str) -> str:
        """Rewrite a document as clean, consistent Markdown."""
        document = store.get(doc_id)
        return (
            f"Reformat the document '{document.title}' as clean Markdown. Use headings, "
            "lists, and emphasis where they aid readability, and keep the wording and "
            "meaning unchanged. Apply the result with the edit_document tool using "
            f"doc_id '{document.id}'.\n\n"
            f"<document id=\"{document.id}\">\n{document.content}\n</document>"
        )

    return mcp
