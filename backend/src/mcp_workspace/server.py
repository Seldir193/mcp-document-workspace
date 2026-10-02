import json

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .store import DOCUMENTS

mcp = MCPServer("MCP Document Workspace")


@mcp.resource("docs://documents", mime_type="application/json")
def list_documents() -> list[dict[str, str]]:
    return [
        {"id": doc.id, "title": doc.title}
        for doc in DOCUMENTS.values()
    ]


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_document(doc_id: str) -> str:
    document = DOCUMENTS.get(doc_id)
    if document is None:
        raise ValueError(f"Document '{doc_id}' not found")
    return document.content


@mcp.tool()
def edit_document(doc_id: str, content: str) -> str:
    document = DOCUMENTS.get(doc_id)
    if document is None:
        raise ValueError(f"Document '{doc_id}' not found")
    document.content = content
    return f"Updated {doc_id}"


@mcp.prompt(name="summarize", description="Summarize a document clearly.")
def summarize_document(
    doc_id: str = Field(description="Document id to summarize"),
) -> str:
    return (
        "Summarize the document identified by "
        f"docs://documents/{doc_id}. "
        "Preserve facts, decisions, and action items."
    )


@mcp.prompt(name="format", description="Rewrite a document in clean Markdown.")
def format_document(
    doc_id: str = Field(description="Document id to format"),
) -> str:
    return (
        "Read the document identified by "
        f"docs://documents/{doc_id}. "
        "Rewrite it as clear Markdown with useful structure. "
        "Use edit_document only after preserving the original meaning."
    )


if __name__ == "__main__":
    mcp.run()
