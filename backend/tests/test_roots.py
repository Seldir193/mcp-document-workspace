"""Roots authorization: paths must resolve inside a client-approved root."""

from pathlib import Path

import pytest

from document_workspace.roots import (
    RootAccessError,
    list_text_documents,
    read_text_document,
    resolve_in_roots,
    root_uri_to_path,
    roots_from_uris,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    approved = tmp_path / "approved"
    (approved / "nested").mkdir(parents=True)
    (approved / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (approved / "nested" / "todo.txt").write_text("ship it\n", encoding="utf-8")
    (approved / "data.json").write_text("{}", encoding="utf-8")
    (tmp_path / "secret.md").write_text("secret\n", encoding="utf-8")
    return approved.resolve()


def test_file_uri_round_trips_to_path(root: Path) -> None:
    assert root_uri_to_path(root.as_uri()) == root
    assert roots_from_uris([root.as_uri()]) == [root]


@pytest.mark.parametrize("uri", ["https://example.com/docs", "file://fileserver/share/docs"])
def test_non_local_root_uri_is_rejected(uri: str) -> None:
    with pytest.raises(RootAccessError):
        root_uri_to_path(uri)


def test_reads_relative_path_inside_root(root: Path) -> None:
    assert read_text_document("notes.md", [root]) == "# Notes\n"
    assert read_text_document("nested/todo.txt", [root]) == "ship it\n"


def test_reads_absolute_path_inside_root(root: Path) -> None:
    assert read_text_document(str(root / "notes.md"), [root]) == "# Notes\n"


def test_relative_path_is_found_in_a_later_root(root: Path, tmp_path: Path) -> None:
    second = tmp_path / "second"
    second.mkdir()
    (second / "only-here.md").write_text("second root\n", encoding="utf-8")

    assert read_text_document("only-here.md", [root, second.resolve()]) == "second root\n"


def test_lists_only_text_documents(root: Path) -> None:
    assert list_text_documents([root]) == [root / "nested" / "todo.txt", root / "notes.md"]


@pytest.mark.parametrize("requested", ["../secret.md", "nested/../../secret.md"])
def test_traversal_out_of_root_is_denied(root: Path, requested: str) -> None:
    with pytest.raises(RootAccessError, match="outside the approved roots"):
        read_text_document(requested, [root])


def test_absolute_path_outside_root_is_denied(root: Path) -> None:
    with pytest.raises(RootAccessError, match="outside the approved roots"):
        read_text_document(str(root.parent / "secret.md"), [root])


def test_sibling_directory_sharing_a_prefix_is_denied(root: Path) -> None:
    sibling = root.parent / "approved-other"
    sibling.mkdir()
    (sibling / "notes.md").write_text("other\n", encoding="utf-8")

    with pytest.raises(RootAccessError):
        resolve_in_roots(str(sibling / "notes.md"), [root])


def test_symlink_escaping_root_is_denied(root: Path) -> None:
    link = root / "link.md"
    try:
        link.symlink_to(root.parent / "secret.md")
    except OSError:
        pytest.skip("symlinks are not available on this platform")

    with pytest.raises(RootAccessError):
        read_text_document("link.md", [root])
    assert link.resolve() not in list_text_documents([root])


def test_non_text_document_is_denied(root: Path) -> None:
    with pytest.raises(RootAccessError, match="not a Markdown or text document"):
        read_text_document("data.json", [root])


def test_missing_file_is_denied(root: Path) -> None:
    with pytest.raises(RootAccessError, match="not a file"):
        read_text_document("absent.md", [root])


def test_no_roots_denies_everything(root: Path) -> None:
    with pytest.raises(RootAccessError, match="not approved any roots"):
        read_text_document(str(root / "notes.md"), [])


def test_non_utf8_file_is_denied(root: Path) -> None:
    (root / "binary.txt").write_bytes(b"\xff\xfe\x00bad")

    with pytest.raises(RootAccessError, match="not UTF-8 text"):
        read_text_document("binary.txt", [root])
