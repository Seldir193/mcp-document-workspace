# Backend — Document Workspace MCP server

Python package exposing a small document store over the Model Context Protocol.

| Kind              | Name / URI                  | Purpose                                   |
| ----------------- | --------------------------- | ----------------------------------------- |
| Resource          | `docs://documents`          | JSON index of documents                   |
| Resource template | `docs://documents/{doc_id}` | Content of one document                   |
| Tool              | `edit_document`             | Replace one exact passage of a document   |
| Prompt            | `summarize`                 | Summarize a document                      |
| Prompt            | `format`                    | Reformat a document as clean Markdown     |

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
document-workspace          # or: python -m document_workspace
```

The server speaks MCP over stdio. To explore it interactively:

```bash
npx @modelcontextprotocol/inspector document-workspace
```

## Test and lint

```bash
pytest
ruff check .
```
