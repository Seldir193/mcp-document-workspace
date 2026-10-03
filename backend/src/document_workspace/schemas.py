from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    doc_id: str = Field(min_length=1)


class EditRequest(BaseModel):
    old_text: str = Field(min_length=1)
    new_text: str


class DocumentSummary(BaseModel):
    id: str
    title: str
    uri: str


class DocumentDetail(DocumentSummary):
    content: str


class PromptResponse(BaseModel):
    name: str
    doc_id: str
    text: str


class EditResponse(BaseModel):
    message: str
    document: DocumentDetail
