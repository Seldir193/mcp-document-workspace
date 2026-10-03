# MCP Document Workspace

A compact portfolio application that demonstrates Model Context Protocol primitives through a real Angular-to-MCP workflow.

The Python backend exposes documents as MCP resources, a safe edit tool, and reusable prompts. A FastAPI bridge owns an MCP client, and the Angular frontend consumes that bridge over HTTP.

**Status: phase 2 complete.** The frontend now reads and edits real MCP-backed data.

![MCP Document Workspace](docs/assets/workspace.png)

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

## Repository layout

```text
backend/
  src/document_workspace/
    server.py     MCP server
    bridge.py     MCP client adapter
    api.py        FastAPI HTTP bridge
    store.py      document domain/store
frontend/
  src/app/
    workspace-api.service.ts
    app.ts / app.html / app.scss
docs/
  architecture.md
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

The HTTP bridge runs on `http://127.0.0.1:8000`.

Frontend:

```powershell
cd frontend
npm install
npm start
```

Open `http://localhost:4200`.

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

The standalone MCP server can still be explored directly:

```powershell
document-workspace
npx @modelcontextprotocol/inspector document-workspace
```

## Current behavior

The document list and document content are loaded through MCP Resources. Editing calls the MCP `edit_document` Tool. Summarize and Format retrieve the server-defined MCP Prompts and display the rendered prompt in the UI.

No model API key is required in this project. Executing those prompts with Claude is intentionally a later extension, so the MCP concepts remain visible and independently testable.

## Next phase

- Docker setup
- optional Claude API execution for rendered prompts
- demo GIF
- final portfolio polish
