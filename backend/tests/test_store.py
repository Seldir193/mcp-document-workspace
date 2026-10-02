import pytest

from document_workspace.store import (
    MAX_CONTENT_CHARS,
    Document,
    DocumentNotFoundError,
    DocumentStore,
    EditError,
)


def test_sample_documents_are_listed(store: DocumentStore) -> None:
    ids = [doc.id for doc in store.list()]

    assert ids == ["release-notes", "onboarding-guide", "meeting-notes"]


def test_get_unknown_document_raises(store: DocumentStore) -> None:
    with pytest.raises(DocumentNotFoundError, match="'missing' not found"):
        store.get("missing")


def test_replace_text_updates_single_occurrence(store: DocumentStore) -> None:
    updated = store.replace_text("release-notes", "40% faster", "twice as fast")

    assert "twice as fast" in updated.content
    assert "40% faster" not in updated.content
    assert store.get("release-notes") == updated


@pytest.mark.parametrize(
    ("old_text", "message"),
    [
        ("", "must not be empty"),
        ("not in the document", "was not found"),
        ("- ", "occurs 4 times"),
    ],
)
def test_replace_text_rejects_unsafe_edits(
    store: DocumentStore, old_text: str, message: str
) -> None:
    before = store.get("release-notes")

    with pytest.raises(EditError, match=message):
        store.replace_text("release-notes", old_text, "replacement")

    assert store.get("release-notes") == before


def test_replace_text_enforces_size_limit() -> None:
    store = DocumentStore([Document(id="note", title="Note", content="short")])

    with pytest.raises(EditError, match="character limit"):
        store.replace_text("note", "short", "x" * (MAX_CONTENT_CHARS + 1))

    assert store.get("note").content == "short"


def test_stores_do_not_share_state() -> None:
    first, second = DocumentStore(), DocumentStore()

    first.replace_text("release-notes", "40% faster", "faster")

    assert "40% faster" in second.get("release-notes").content
