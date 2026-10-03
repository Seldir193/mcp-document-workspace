# MCP Learning Map

This file maps the MCP concepts demonstrated by the project to the code that implements them.

## 1. Direct Resource

A Direct Resource has a fixed URI and needs no URI parameter.

Project implementation:

```python
@mcp.resource("docs://documents", mime_type="application/json")
def list_documents() -> str:
    ...
```

File: `backend/src/document_workspace/server.py`

Purpose: return the document index used by the client for discovery.

## 2. Resource Template

A Resource Template contains a parameter in the URI.

```python
@mcp.resource("docs://documents/{doc_id}", mime_type="text/markdown")
def read_document(doc_id: str) -> str:
    ...
```

The MCP SDK extracts `doc_id` from the URI and passes it to the function.

## 3. Tool

Tools represent actions. This project exposes one write operation:

```text
edit_document(doc_id, old_text, new_text)
```

It uses exact text replacement so an edit is rejected when the target text is missing or ambiguous.

## 4. Prompts

The server publishes two reusable Prompt templates:

- `summarize`
- `format`

The client requests a Prompt by name and passes `doc_id` as an argument. The server returns a ready-to-use model message.

Important distinction: retrieving an MCP Prompt is not the same as calling an AI model. This project deliberately displays the rendered Prompt so that the MCP layer remains visible.

## 5. MCP Client

The HTTP bridge does not read `DocumentStore` directly.

`bridge.py` uses the MCP Client API:

```python
client.read_resource(...)
client.get_prompt(...)
client.call_tool(...)
```

That means the browser-facing application consumes the same MCP contract that another MCP host could consume.

## 6. Why the HTTP bridge exists

A browser Angular application does not directly own the Python MCP Client in this architecture.

The flow is:

```text
Angular
  → HTTP request
  → FastAPI
  → MCP Client
  → MCP Server
```

FastAPI is therefore an application adapter, not a replacement for MCP.

## 7. What happens when you click in the UI

Selecting a document:

```text
Angular click
→ GET /api/documents/{id}
→ MCPBridge.get_document()
→ Client.read_resource()
→ docs://documents/{id}
→ MCP Resource
```

Editing a document:

```text
Save via MCP Tool
→ POST /api/documents/{id}/edit
→ Client.call_tool("edit_document")
→ MCP Tool
→ DocumentStore.replace_text()
```

Clicking Summarize:

```text
Summarize
→ POST /api/prompts/summarize
→ Client.get_prompt("summarize")
→ MCP Prompt
→ rendered prompt shown in Angular
```

## 8. Where to study the project

Read these files in this order:

1. `backend/src/document_workspace/store.py`
2. `backend/src/document_workspace/server.py`
3. `backend/tests/test_server.py`
4. `backend/src/document_workspace/bridge.py`
5. `backend/src/document_workspace/api.py`
6. `frontend/src/app/workspace-api.service.ts`
7. `frontend/src/app/app.ts`
8. `frontend/src/app/app.html`

That sequence follows the data from the domain layer outward to the browser.
