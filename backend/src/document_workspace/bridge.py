import json

from mcp import Client

from document_workspace.schemas import DocumentDetail, DocumentSummary, EditResponse, PromptResponse


class MCPBridge:
    def __init__(self, client: Client) -> None:
        self.client = client

    async def list_documents(self) -> list[DocumentSummary]:
        result = await self.client.read_resource("docs://documents")
        payload = json.loads(result.contents[0].text)
        return [DocumentSummary(**item) for item in payload]

    async def get_document(self, doc_id: str) -> DocumentDetail:
        documents = await self.list_documents()
        summary = next((item for item in documents if item.id == doc_id), None)
        if summary is None:
            raise ValueError(f"Document '{doc_id}' not found")
        result = await self.client.read_resource(summary.uri)
        return DocumentDetail(**summary.model_dump(), content=result.contents[0].text)

    async def render_prompt(self, name: str, doc_id: str) -> PromptResponse:
        result = await self.client.get_prompt(name, {"doc_id": doc_id})
        text = result.messages[0].content.text
        return PromptResponse(name=name, doc_id=doc_id, text=text)

    async def edit_document(self, doc_id: str, old_text: str, new_text: str) -> EditResponse:
        result = await self.client.call_tool(
            "edit_document",
            {"doc_id": doc_id, "old_text": old_text, "new_text": new_text},
        )
        message = result.content[0].text
        if result.is_error:
            raise ValueError(message)
        document = await self.get_document(doc_id)
        return EditResponse(message=message, document=document)
