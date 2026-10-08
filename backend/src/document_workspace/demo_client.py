"""Demo host for the advanced MCP features, over stdio or Streamable HTTP.

Without ``--url`` it launches ``python -m document_workspace.serve --advanced`` as a
stdio subprocess. With ``--url`` it connects to a running Streamable HTTP server.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import anyio
from mcp import Client

from document_workspace.host import NotificationRecorder, advanced_client, stdio_server_parameters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-workspace-demo", description="Exercise the advanced MCP tools."
    )
    parser.add_argument("--url", help="Streamable HTTP endpoint, e.g. http://127.0.0.1:8000/mcp")
    parser.add_argument("--doc-id", default="release-notes")
    parser.add_argument(
        "--root",
        type=Path,
        action="append",
        default=[],
        help="directory to approve as an MCP root (repeatable)",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "legacy"],
        default="auto",
        help="auto negotiates 2026-07-28; legacy forces the initialize handshake",
    )
    return parser


async def run_demo(args: argparse.Namespace) -> None:
    recorder = NotificationRecorder(on_event=lambda line: print(f"  [notification] {line}"))
    stdio = stdio_server_parameters(sys.executable, "--advanced", "--step-delay", "0.2")
    server = args.url or stdio
    client = advanced_client(server, roots=args.root, recorder=recorder, mode=args.mode)
    async with client:
        print(f"Connected ({'http' if args.url else 'stdio'}), protocol {client.protocol_version}")
        await _show(client, "summarize_document", {"doc_id": args.doc_id})
        await _show(client, "list_root_documents", {})
        await _show(client, "analyze_document", {"doc_id": args.doc_id}, recorder)


async def _show(
    client: Client,
    tool: str,
    arguments: dict[str, str],
    recorder: NotificationRecorder | None = None,
) -> None:
    print(f"\n{tool}({arguments})")
    result = await client.call_tool(
        tool,
        arguments,
        progress_callback=recorder.on_progress if recorder is not None else None,
    )
    status = "error" if result.is_error else "ok"
    text = "\n".join(block.text for block in result.content if hasattr(block, "text"))
    print(f"  [{status}] {text}")


def main(argv: Sequence[str] | None = None) -> None:
    anyio.run(run_demo, build_parser().parse_args(argv))


if __name__ == "__main__":
    main()
