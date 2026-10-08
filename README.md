# MCP Document Workspace

A compact portfolio application that demonstrates Model Context Protocol primitives through a real Angular-to-MCP workflow.

The Python backend exposes documents as MCP Resources, a safe edit Tool, and reusable Prompts. A FastAPI bridge owns an MCP Client, and the Angular frontend consumes that bridge over HTTP.

**Status: core UI flow complete; Advanced MCP backend tools implemented and covered by backend tests.**

![MCP Document Workspace](docs/assets/workspace.png)

For a guided explanation of how each MCP concept maps to the code, see [docs/learning-map.md](docs/learning-map.md).

## End-to-end flow

```text
Angular UI
   ↓ HTTP
FastAPI bridge
   ↓ MCP Client
MCPServer 2.x
   ↓
Resources / Tools / Prompts
   ↓
DocumentStore
```

## MCP surface

| Primitive | Identifier | Purpose |
| --- | --- | --- |
| Resource | `docs://documents` | JSON index of documents |
| Resource template | `docs://documents/{doc_id}` | Read one document |
| Tool | `edit_document` | Replace one exact passage |
| Prompt | `summarize` | Render a summary instruction |
| Prompt | `format` | Render a Markdown-formatting instruction |

## Advanced MCP surface

The advanced tools are opt-in (`create_advanced_server()`, or `--advanced` on the CLI) so the core server above keeps its exact surface.

| Feature | Identifier | What it shows |
| --- | --- | --- |
| Sampling | tool `summarize_document` | The server asks the *client's* model for a summary. The server holds no model API key. |
| Roots + authorization | tools `list_root_documents`, `read_root_document` | The client approves directories; the server resolves every path and rejects anything outside them. |
| Logging + progress | tool `analyze_document` | Log messages and progress notifications during a multi-step call. |
| STDIO transport | `python -m document_workspace.serve` | Local subprocess transport. |
| Streamable HTTP transport | `python -m document_workspace.serve --transport streamable-http` | Stateful by default; `--stateless` and `--json-response` are the simplified modes. |

Prompt vs. Sampling: the `summarize` **prompt** only returns prompt text for the host to use. The `summarize_document` **tool** has the client run its model and returns the finished summary.

### Run the advanced server and demo host

From `backend/` with the virtual environment active:

```powershell
# STDIO: the demo host launches the server as a subprocess
python -m document_workspace.demo_client --root ..\docs

# Streamable HTTP, stateful (terminal 1), then the demo host (terminal 2)
python -m document_workspace.serve --transport streamable-http --advanced --port 8001
python -m document_workspace.demo_client --url http://127.0.0.1:8001/mcp --root ..\docs

# Simplified HTTP modes
python -m document_workspace.serve --transport streamable-http --advanced --port 8001 --stateless
python -m document_workspace.serve --transport streamable-http --advanced --port 8001 --json-response
```

Add `--mode legacy` to the demo host to force the 2025-era initialize handshake instead of protocol 2026-07-28.

The demo host uses a deterministic extractive stand-in for a model (`host.extractive_model`), so nothing here needs a paid API. Any `async (CreateMessageRequestParams) -> str` callable can be passed as `model=` to plug in a real one; no Anthropic integration ships in this repo.

### Streamable HTTP modes (measured with mcp 2.3.0)

| Server mode | 2026-07-28 client | 2025-era (handshake) client |
| --- | --- | --- |
| default (stateful, SSE) | sampling, roots, logs, progress | sampling, roots, logs, progress |
| `--stateless` | sampling, roots, logs, progress | sampling and roots fail (no back-channel) |
| `--json-response` | sampling and roots; **no** logs or progress | **no** logs or progress |

Why: a 2026-07-28 request is a self-contained POST with no `Mcp-Session-Id`; the server gets sampling/roots answers by returning an `InputRequiredResult` that the client answers and retries, so it never needs a session. A 2025-era client needs the session's SSE stream for server-to-client requests. A JSON response body can only carry the final result, so notifications are dropped.

Production-demo vs. educational: the Angular UI + FastAPI bridge + core server is the production-style demo path. The advanced tools, `serve.py`, and `demo_client.py` are educational demos; the HTTP server has no authentication and binds to `127.0.0.1` by default.

## Repository layout

```text
backend/
  src/document_workspace/
    server.py     MCP server (core surface)
    advanced.py   sampling, roots, logging/progress tools
    roots.py      server-side roots authorization
    host.py       client callbacks: sampling, roots, notifications
    serve.py      stdio / Streamable HTTP entry point
    demo_client.py  demo host for the advanced tools
    bridge.py     MCP client adapter
    api.py        FastAPI HTTP bridge
    store.py      document domain/store
frontend/
  src/app/
    workspace-api.service.ts
    app.ts / app.html / app.scss
docs/
  architecture.md
.github/workflows/
  ci.yml
```

## Run locally

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
document-workspace-api
```

Frontend:

```powershell
cd frontend
npm install
npm start
```

Open `http://localhost:4200`.

## Run with Docker

```powershell
docker compose up --build
```

Then open `http://localhost:4200`. The backend is exposed on `http://localhost:8000`.

## Verify

Backend:

```powershell
pytest
ruff check .
```

Frontend:

```powershell
npm run build
npm test -- --watch=false --browsers=ChromeHeadless
```

The standalone MCP server can also be explored directly:

```powershell
document-workspace
npx @modelcontextprotocol/inspector document-workspace
```

GitHub Actions runs the backend tests/lint and frontend build/tests on pushes to `main` and on pull requests.

## Current behavior

The document list and document content are loaded through MCP Resources. Editing calls the MCP `edit_document` Tool. Summarize and Format retrieve server-defined MCP Prompts and display the rendered prompt in the UI.

No model API key is required. Prompt retrieval and model execution are intentionally separate so the MCP concepts stay visible and independently testable. The Angular UI does not use the advanced tools yet.

## Optional extensions

- execute rendered prompts with the Claude API
- persistent document storage
- authentication
- demo GIF
