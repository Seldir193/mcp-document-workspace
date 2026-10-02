# MCP Document Workspace

A small application that demonstrates practical use of the
[Model Context Protocol](https://modelcontextprotocol.io): a Python MCP server
exposes documents as resources, an edit tool, and prompts, with an Angular
frontend on top.

**Status: phase 1 (foundation).** The MCP server is working and tested. The
frontend is a static shell; connecting it to the server is phase 2.

## What the server exposes

| Primitive         | Identifier                  | Purpose                                 |
| ----------------- | --------------------------- | --------------------------------------- |
| Resource          | `docs://documents`          | JSON index of documents                 |
| Resource template | `docs://documents/{doc_id}` | Content of one document                 |
| Tool              | `edit_document`             | Replace one exact passage of a document |
| Prompt            | `summarize`                 | Summarize a document                    |
| Prompt            | `format`                    | Reformat a document as clean Markdown   |

See [docs/architecture.md](docs/architecture.md) for the design and diagram.

## Repository layout

```
backend/    Python package: MCP server, document store, tests
frontend/   Angular standalone app (SCSS, routing)
docs/       Architecture notes
```

## Prerequisites

- Python 3.11+
- Node.js 20.19+, 22.12+ or 24+

## Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"

pytest                 # run the tests
document-workspace     # start the MCP server on stdio
```

To explore the server interactively with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector document-workspace
```

## Frontend

```bash
cd frontend
npm install
npm start              # http://localhost:4200
npm run build
npm test -- --watch=false --browsers=ChromeHeadless
```

## Roadmap

Phase 2: an HTTP API with an MCP client in the backend, the frontend wired to
it (document list, viewer, prompts, edit, activity log), and Docker setup.
