import pytest
from fastapi.testclient import TestClient

from document_workspace.api import app


@pytest.fixture
def api_client():
    with TestClient(app) as client:
        yield client


def test_health_reports_real_bridge(api_client: TestClient) -> None:
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["transport"] == "mcp-client"


def test_lists_documents_through_mcp(api_client: TestClient) -> None:
    response = api_client.get("/api/documents")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "release-notes"


def test_reads_document_through_mcp(api_client: TestClient) -> None:
    response = api_client.get("/api/documents/onboarding-guide")

    assert response.status_code == 200
    assert response.json()["title"] == "Engineering Onboarding Guide"
    assert "first week" in response.json()["content"]


def test_renders_prompt_through_mcp(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/prompts/summarize",
        json={"doc_id": "meeting-notes"},
    )

    assert response.status_code == 200
    assert "Product Sync Notes" in response.json()["text"]


def test_edits_document_through_mcp_tool(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/documents/release-notes/edit",
        json={"old_text": "40% faster", "new_text": "twice as fast"},
    )

    assert response.status_code == 200
    assert "twice as fast" in response.json()["document"]["content"]
    assert "Updated 'release-notes'" in response.json()["message"]


def test_missing_document_returns_404(api_client: TestClient) -> None:
    response = api_client.get("/api/documents/missing")

    assert response.status_code == 404
