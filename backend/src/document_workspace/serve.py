"""Run the document workspace MCP server over stdio or Streamable HTTP.

``python -m document_workspace.serve --help`` lists the options.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from mcp.server.mcpserver import MCPServer

from document_workspace.advanced import create_advanced_server
from document_workspace.server import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-workspace", description="Document workspace MCP server."
    )
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="also expose the sampling, roots, and logging/progress tools",
    )
    parser.add_argument(
        "--step-delay",
        type=float,
        default=0.0,
        help="seconds to pause between analyze_document steps (advanced only)",
    )
    http = parser.add_argument_group("streamable-http options")
    http.add_argument("--host", default="127.0.0.1")
    http.add_argument("--port", type=int, default=8000)
    http.add_argument(
        "--stateless",
        action="store_true",
        help="no Mcp-Session-Id: every 2025-era request gets a fresh transport",
    )
    http.add_argument(
        "--json-response",
        action="store_true",
        help="answer each POST with one JSON body instead of an SSE stream",
    )
    return parser


def build_server(args: argparse.Namespace) -> MCPServer:
    if args.advanced:
        return create_advanced_server(step_delay=args.step_delay)
    return create_server()


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    server = build_server(args)
    if args.transport == "stdio":
        server.run(transport="stdio")
        return
    server.run(
        transport="streamable-http",
        host=args.host,
        port=args.port,
        stateless_http=args.stateless,
        json_response=args.json_response,
    )


if __name__ == "__main__":
    main()
