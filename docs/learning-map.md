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

## 8. Sampling

Sampling lets a server borrow the client's model. The server never holds an API key.

```python
def request_summary(doc_id: str) -> Sample:
    return Sample([SamplingMessage(role="user", content=TextContent(text=prompt))], max_tokens=300)

@mcp.tool()
def summarize_document(
    doc_id: str, sampled: Annotated[CreateMessageResult, Resolve(request_summary)]
) -> str:
    return sampled.content.text
```

Server: `advanced.py`. Client: `host.sampling_callback(model)`, passed to `Client(..., sampling_callback=...)`.

Compare with section 4: the `summarize` prompt returns text and stops. `summarize_document` returns the model's answer.

## 9. Roots and authorization

The client advertises approved directories through `list_roots_callback`. The server asks for them with `Resolve(client_roots)`, where `client_roots` returns `ListRoots()`.

Roots are information, not enforcement. `roots.py` resolves each requested path and refuses anything that ends up outside a root, so `../secret.md`, an absolute outside path, or a symlink pointing out are all denied.

Tests: `tests/test_roots.py`, and the denial cases in `tests/test_advanced.py`.

## 10. Logging

```python
await ctx.info("Analyzing 'release-notes'", logger_name="document-workspace.analysis")
```

Client: `Client(..., logging_callback=recorder.on_log, log_level="info")`. On protocol 2026-07-28 the `log_level` opt-in is required. The SDK marks logging as deprecated from that protocol version on.

## 11. Progress notifications

```python
await ctx.report_progress(index, len(steps), label)
```

Client: `client.call_tool("analyze_document", {...}, progress_callback=recorder.on_progress)`. Without a callback the client sends no progress token and the server call does nothing.

## 12. STDIO transport

```powershell
python -m document_workspace.serve --advanced
python -m document_workspace.demo_client --root ..\docs
```

The client starts the server as a subprocess and talks over stdin/stdout, so the server must write nothing but protocol messages to stdout.

## 13. Streamable HTTP transport

```powershell
python -m document_workspace.serve --transport streamable-http --advanced --port 8001
python -m document_workspace.demo_client --url http://127.0.0.1:8001/mcp --root ..\docs
```

One HTTP endpoint (`/mcp`). The client POSTs requests; the server answers with JSON or an SSE stream.

## 14. Stateful, stateless, and JSON-response

| Mode | Flag | Keeps | Loses |
| --- | --- | --- | --- |
| Stateful | (default) | sessions, SSE, every server-to-client feature | 2025-era clients must keep hitting the process that holds their session |
| Stateless | `--stateless` | any worker can serve any request | sampling/roots for 2025-era clients |
| JSON response | `--json-response` | plain request/response HTTP | log and progress notifications |

Clients on protocol 2026-07-28 keep sampling and roots in every mode, because the answers travel inside a retried request instead of over a session.

Tests: `tests/test_transports.py`.

## 15. Where to study the project

Read these files in this order:

1. `backend/src/document_workspace/store.py`
2. `backend/src/document_workspace/server.py`
3. `backend/tests/test_server.py`
4. `backend/src/document_workspace/bridge.py`
5. `backend/src/document_workspace/api.py`
6. `frontend/src/app/workspace-api.service.ts`
7. `frontend/src/app/app.ts`
8. `frontend/src/app/app.html`

For the advanced topics, read `roots.py`, `advanced.py`, `host.py`, `serve.py`, then `tests/test_advanced.py` and `tests/test_transports.py`.

That sequence follows the data from the domain layer outward to the browser.
