from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp import Client
from mcp.shared.exceptions import MCPError

from document_workspace.bridge import MCPBridge
from document_workspace.schemas import EditRequest, EditResponse, PromptRequest, PromptResponse
from document_workspace.server import create_server
from document_workspace.store import DocumentStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = DocumentStore()
    async with Client(create_server(store)) as client:
        app.state.bridge = MCPBridge(client)
        yield


app = FastAPI(title="MCP Document Workspace API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def bridge(request: Request) -> MCPBridge:
    return request.app.state.bridge


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ready", "server": "document-workspace", "transport": "mcp-client"}


@app.get("/api/documents")
async def list_documents(request: Request):
    return await bridge(request).list_documents()


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, request: Request):
    try:
        return await bridge(request).get_document(doc_id)
    except (MCPError, ValueError) as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/prompts/{name}", response_model=PromptResponse)
async def render_prompt(name: str, payload: PromptRequest, request: Request):
    if name not in {"summarize", "format"}:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    try:
        return await bridge(request).render_prompt(name, payload.doc_id)
    except (MCPError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/documents/{doc_id}/edit", response_model=EditResponse)
async def edit_document(doc_id: str, payload: EditRequest, request: Request):
    try:
        return await bridge(request).edit_document(doc_id, payload.old_text, payload.new_text)
    except (MCPError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
