"""Authorization for filesystem access inside client-approved MCP roots.

An MCP client advertises roots as ``file://`` URIs. Nothing in the protocol
stops a server from reading elsewhere, so every path is checked here: it is
resolved (following ``..`` and symlinks) and must still sit inside a root.

This module has no MCP SDK dependency; the protocol layer passes in root URIs.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

ALLOWED_SUFFIXES = frozenset({".md", ".markdown", ".txt"})
MAX_FILE_BYTES = 200_000
MAX_LISTED_FILES = 200


class RootAccessError(PermissionError):
    """Raised when a path is outside the approved roots or not a readable document."""


def root_uri_to_path(uri: str) -> Path:
    """Convert a ``file://`` root URI to a resolved local path."""
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise RootAccessError(f"Root '{uri}' is not a file:// URI")
    if parsed.netloc not in ("", "localhost"):
        raise RootAccessError(f"Root '{uri}' points at a remote host")
    return _resolve(Path(url2pathname(parsed.path)))


def roots_from_uris(uris: Iterable[str]) -> list[Path]:
    return [root_uri_to_path(uri) for uri in uris]


def resolve_in_roots(requested: str, roots: Sequence[Path]) -> Path:
    """Return the resolved path for ``requested`` if it lies inside a root.

    Absolute paths are checked as given. Relative paths are tried against each
    root in order and the first existing match wins; if none exists, the first
    in-root candidate is returned so the caller can report it as missing.
    """
    if not roots:
        raise RootAccessError("The client has not approved any roots")
    resolved_roots = [_resolve(root) for root in roots]
    path = Path(requested)
    candidates = [path] if path.is_absolute() else [root / path for root in resolved_roots]
    resolved = [_resolve(candidate) for candidate in candidates]
    inside = [candidate for candidate in resolved if _is_inside(candidate, resolved_roots)]
    if not inside:
        raise RootAccessError(f"Path '{requested}' is outside the approved roots")
    return next((candidate for candidate in inside if candidate.exists()), inside[0])


def read_text_document(requested: str, roots: Sequence[Path]) -> str:
    """Read one Markdown/text file that lies inside the approved roots."""
    path = resolve_in_roots(requested, roots)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise RootAccessError(f"Path '{requested}' is not a Markdown or text document")
    if not path.is_file():
        raise RootAccessError(f"Path '{requested}' is not a file")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise RootAccessError(f"Path '{requested}' exceeds the {MAX_FILE_BYTES} byte limit")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise RootAccessError(f"Path '{requested}' is not UTF-8 text") from error


def list_text_documents(roots: Sequence[Path]) -> list[Path]:
    """List Markdown/text files under the approved roots, sorted, capped in number."""
    resolved_roots = [_resolve(root) for root in roots]
    found: set[Path] = set()
    for root in resolved_roots:
        found.update(_documents_under(root, resolved_roots))
    return sorted(found)[:MAX_LISTED_FILES]


def _documents_under(root: Path, roots: Sequence[Path]) -> Iterable[Path]:
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if path.suffix.lower() not in ALLOWED_SUFFIXES or not path.is_file():
            continue
        resolved = _resolve(path)
        if _is_inside(resolved, roots):
            yield resolved


def _resolve(path: Path) -> Path:
    try:
        return path.resolve()
    except (OSError, ValueError) as error:
        raise RootAccessError(f"Path '{path}' cannot be resolved") from error


def _is_inside(path: Path, roots: Sequence[Path]) -> bool:
    return any(path.is_relative_to(root) for root in roots)
