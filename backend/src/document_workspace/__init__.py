"""MCP document workspace: a small MCP server over a local document store."""

from document_workspace.advanced import create_advanced_server
from document_workspace.server import create_server
from document_workspace.store import Document, DocumentStore

__all__ = ["Document", "DocumentStore", "create_advanced_server", "create_server"]
