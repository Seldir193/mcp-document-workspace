# Architecture

## Phase 1

```text
Angular UI
   |
   | phase 2: local HTTP bridge
   v
MCP Client
   |
   | MCP protocol
   v
MCPServer 2.x
   |-- Resources
   |-- Resource Templates
   |-- Tools
   |-- Prompts
   v
Document Store
```

The MCP server is intentionally isolated from the Angular UI. The UI will talk to a thin application bridge, and that bridge will act as the MCP client.

## Design decisions

- MCP SDK 2.x is used rather than pinning the course's older FastMCP API.
- The first store is in-memory to keep the MCP concepts visible.
- Persistence, authentication and cloud deployment are deferred.
- The Angular application starts as a document workspace shell.
- Tests cover both MCP behavior and frontend rendering.

## Phase 2 boundary

Phase 2 introduces the client/session layer and UI integration without changing the MCP resource, tool or prompt contract unless tests require it.
