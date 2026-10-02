"""Protocol-level tests: every assertion goes through a real MCP client session."""

import json

import pytest
from mcp import Client, MCPError

from document_workspace import DocumentStore

pytestmark = pytest.mark.anyio


async def test_direct_resource_is_listed(client: Client) -> None:
    result = await client.list_resources()

    assert [str(resource.uri) for resource in result.resources] == ["docs://documents"]


async def test_document_template_is_listed(client: Client) -> None:
    result = await client.list_resource_templates()

    assert [template.uri_template for template in result.resource_templates] == [
        "docs://documents/{doc_id}"
    ]


async def test_read_document_index(client: Client) -> None:
    result = await client.read_resource("docs://documents")

    content = result.contents[0]
    assert content.mime_type == "application/json"
    assert {"id": "release-notes", "title": "Release Notes 1.4"}.items() <= (
        json.loads(content.text)[0].items()
    )
    assert len(json.loads(content.text)) == 3


async def test_read_single_document(client: Client, store: DocumentStore) -> None:
    result = await client.read_resource("docs://documents/onboarding-guide")

    content = result.contents[0]
    assert content.mime_type == "text/markdown"
    assert content.text == store.get("onboarding-guide").content


async def test_read_unknown_document_fails(client: Client) -> None:
    with pytest.raises(MCPError, match="missing"):
        await client.read_resource("docs://documents/missing")


async def test_edit_document_tool_is_listed(client: Client) -> None:
    result = await client.list_tools()

    assert [tool.name for tool in result.tools] == ["edit_document"]
    assert set(result.tools[0].input_schema["required"]) == {"doc_id", "old_text", "new_text"}


async def test_edit_document_changes_content(client: Client) -> None:
    result = await client.call_tool(
        "edit_document",
        {"doc_id": "release-notes", "old_text": "40% faster", "new_text": "twice as fast"},
    )

    assert not result.is_error
    assert "Updated 'release-notes'" in result.content[0].text

    reread = await client.read_resource("docs://documents/release-notes")
    assert "twice as fast" in reread.contents[0].text


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"doc_id": "missing", "old_text": "a", "new_text": "b"}, "not found"),
        ({"doc_id": "release-notes", "old_text": "absent", "new_text": "b"}, "was not found"),
        ({"doc_id": "release-notes", "old_text": "- ", "new_text": "* "}, "occurs 4 times"),
    ],
)
async def test_edit_document_rejects_unsafe_edits(
    client: Client, store: DocumentStore, arguments: dict[str, str], message: str
) -> None:
    before = store.get("release-notes")

    result = await client.call_tool("edit_document", arguments)

    assert result.is_error
    assert message in result.content[0].text
    assert store.get("release-notes") == before


async def test_prompts_are_listed(client: Client) -> None:
    result = await client.list_prompts()

    assert sorted(prompt.name for prompt in result.prompts) == ["format", "summarize"]
    for prompt in result.prompts:
        assert [(arg.name, arg.required) for arg in prompt.arguments] == [("doc_id", True)]


@pytest.mark.parametrize(
    ("name", "instruction"),
    [("summarize", "Summarize the document"), ("format", "Reformat the document")],
)
async def test_prompt_embeds_document(
    client: Client, store: DocumentStore, name: str, instruction: str
) -> None:
    result = await client.get_prompt(name, {"doc_id": "meeting-notes"})

    message = result.messages[0]
    assert message.role == "user"
    assert instruction in message.content.text
    assert store.get("meeting-notes").content in message.content.text


async def test_prompt_for_unknown_document_fails(client: Client) -> None:
    with pytest.raises(MCPError):
        await client.get_prompt("summarize", {"doc_id": "missing"})
