"""Client-side (host) handlers for the advanced MCP features.

The server asks; the host answers. This module holds the answers: a sampling
callback backed by a pluggable model, a roots callback that advertises the
approved directories, and a recorder for log and progress notifications.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from mcp import Client, StdioServerParameters
from mcp.client.session import ClientRequestContext
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    ListRootsResult,
    LoggingMessageNotificationParams,
    Root,
    TextContent,
)

TextModel = Callable[[CreateMessageRequestParams], Awaitable[str]]
"""Runs one sampling request and returns the generated text.

Swap in a real model client here; the MCP server never sees its credentials.
"""

EXTRACTIVE_MODEL_NAME = "extractive-demo"
_DOCUMENT_BLOCK = re.compile(r"<document[^>]*>\n(.*)\n</document>", re.DOTALL)
_BULLET_PREFIX = re.compile(r"^(?:[-*]|\d+\.)\s+")


async def extractive_model(params: CreateMessageRequestParams) -> str:
    """Deterministic stand-in for an LLM: the first three content lines of the document."""
    prompt = "\n".join(_message_texts(params))
    match = _DOCUMENT_BLOCK.search(prompt)
    body = match.group(1) if match else prompt
    lines = [line.strip() for line in body.splitlines()]
    content = [_BULLET_PREFIX.sub("", line) for line in lines if line and not line.startswith("#")]
    return " ".join(_as_sentence(line) for line in content[:3])


def sampling_callback(model: TextModel = extractive_model, model_name: str = EXTRACTIVE_MODEL_NAME):
    """Build the callback that answers the server's ``sampling/createMessage``."""

    async def handle(
        context: ClientRequestContext, params: CreateMessageRequestParams
    ) -> CreateMessageResult:
        text = await model(params)
        return CreateMessageResult(
            role="assistant",
            content=TextContent(text=text),
            model=model_name,
            stop_reason="endTurn",
        )

    return handle


def roots_callback(directories: Sequence[Path]):
    """Build the callback that answers ``roots/list`` with the approved directories."""
    roots = [Root(uri=path.resolve().as_uri(), name=path.name) for path in directories]

    async def handle(context: ClientRequestContext) -> ListRootsResult:
        return ListRootsResult(roots=roots)

    return handle


@dataclass
class NotificationRecorder:
    """Collects server notifications so a host can display or assert on them."""

    logs: list[tuple[str, str]] = field(default_factory=list)
    progress: list[tuple[float, float | None, str | None]] = field(default_factory=list)
    on_event: Callable[[str], None] | None = None

    async def on_log(self, params: LoggingMessageNotificationParams) -> None:
        self.logs.append((params.level, str(params.data)))
        self._emit(f"log[{params.level}] {params.data}")

    async def on_progress(self, progress: float, total: float | None, message: str | None) -> None:
        self.progress.append((progress, total, message))
        of_total = f"/{total:g}" if total is not None else ""
        self._emit(f"progress {progress:g}{of_total} {message or ''}".rstrip())

    def _emit(self, line: str) -> None:
        if self.on_event is not None:
            self.on_event(line)


def advanced_client(
    server: object,
    *,
    roots: Sequence[Path] = (),
    recorder: NotificationRecorder | None = None,
    model: TextModel = extractive_model,
    mode: str = "auto",
) -> Client:
    """A client that answers sampling and roots requests and receives log messages.

    ``server`` is anything ``mcp.Client`` accepts: a URL, ``StdioServerParameters``,
    or an in-process server. ``log_level`` is the per-request opt-in that 2026-07-28
    servers require before they send any log message.
    """
    return Client(
        server,
        sampling_callback=sampling_callback(model),
        list_roots_callback=roots_callback(roots),
        logging_callback=recorder.on_log if recorder is not None else None,
        log_level="info",
        mode=mode,
    )


def stdio_server_parameters(python: str, *server_args: str) -> StdioServerParameters:
    """Launch parameters for ``python -m document_workspace.serve`` as a stdio subprocess.

    The SDK passes only a minimal environment to the child, so the package
    location is handed over explicitly; this also works for a source checkout.
    """
    source_root = str(Path(__file__).resolve().parent.parent)
    return StdioServerParameters(
        command=python,
        args=["-m", "document_workspace.serve", *server_args],
        env={"PYTHONPATH": source_root},
    )


def _message_texts(params: CreateMessageRequestParams) -> list[str]:
    texts = []
    for message in params.messages:
        blocks = message.content if isinstance(message.content, list) else [message.content]
        texts.extend(block.text for block in blocks if isinstance(block, TextContent))
    return texts


def _as_sentence(line: str) -> str:
    return line if line.endswith((".", "!", "?")) else f"{line}."
