"""In-memory document store.

The store is the only place that knows how documents are held. The MCP server
talks to it through a handful of methods, so swapping in file or database
storage later does not touch the protocol layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

MAX_CONTENT_CHARS = 20_000


class DocumentNotFoundError(LookupError):
    """Raised when a document id is not in the store."""

    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document '{doc_id}' not found")
        self.doc_id = doc_id


class EditError(ValueError):
    """Raised when an edit is rejected; the document is left unchanged."""


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    title: str
    content: str


SAMPLE_DOCUMENTS: tuple[Document, ...] = (
    Document(
        id="release-notes",
        title="Release Notes 1.4",
        content=(
            "# Release Notes 1.4\n\n"
            "## Highlights\n"
            "- Offline mode for the mobile app\n"
            "- Search results now load 40% faster\n\n"
            "## Fixes\n"
            "- Resolved a crash when exporting empty reports\n"
            "- Corrected time zone handling in weekly digests\n"
        ),
    ),
    Document(
        id="onboarding-guide",
        title="Engineering Onboarding Guide",
        content=(
            "# Engineering Onboarding Guide\n\n"
            "Welcome to the team. Your first week focuses on access, tooling, "
            "and shipping one small change.\n\n"
            "1. Request repository and staging access.\n"
            "2. Set up the local environment using the project README.\n"
            "3. Pair with your onboarding buddy on a starter ticket.\n"
        ),
    ),
    Document(
        id="meeting-notes",
        title="Product Sync Notes",
        content=(
            "product sync - notes\n"
            "attendees: dana, li, marco\n"
            "decided to move the beta to the 14th. marco owns the migration plan, "
            "li follows up with support about the faq. open question: do we need "
            "a second load test before launch?\n"
        ),
    ),
)


class DocumentStore:
    """Holds documents in memory, keyed by id."""

    def __init__(self, documents: Iterable[Document] = SAMPLE_DOCUMENTS) -> None:
        self._documents = {doc.id: doc for doc in documents}

    def list(self) -> list[Document]:
        return list(self._documents.values())

    def get(self, doc_id: str) -> Document:
        try:
            return self._documents[doc_id]
        except KeyError:
            raise DocumentNotFoundError(doc_id) from None

    def replace_text(self, doc_id: str, old_text: str, new_text: str) -> Document:
        """Replace one exact occurrence of ``old_text`` with ``new_text``.

        The edit is rejected unless ``old_text`` occurs exactly once, so a
        caller can never change more of the document than it has quoted.
        """
        document = self.get(doc_id)
        if not old_text:
            raise EditError("old_text must not be empty")

        occurrences = document.content.count(old_text)
        if occurrences == 0:
            raise EditError(f"old_text was not found in document '{doc_id}'")
        if occurrences > 1:
            raise EditError(
                f"old_text occurs {occurrences} times in document '{doc_id}'; "
                "include more surrounding text so it matches exactly once"
            )

        content = document.content.replace(old_text, new_text, 1)
        if len(content) > MAX_CONTENT_CHARS:
            raise EditError(f"Edit would exceed the {MAX_CONTENT_CHARS} character limit")

        updated = replace(document, content=content)
        self._documents[doc_id] = updated
        return updated
