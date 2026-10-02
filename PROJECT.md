# MCP Document Workspace

## Goal
Build a small portfolio-grade application that demonstrates practical Model Context Protocol usage.

## Scope
- Angular frontend with SCSS
- Python backend using the MCP Python SDK
- MCP server exposing Resources, Resource Templates, Tools, and Prompts
- MCP client that lists and reads resources, lists and executes prompts, and calls tools
- Local document storage for the MVP
- Clean README, tests, Docker setup, and architecture diagram

## Core user flows
1. View available documents.
2. Open a document through an MCP Resource.
3. Use /summarize and /format prompts.
4. Edit document content through an MCP Tool.
5. See a small activity log of MCP operations.

## Quality bar
- Portfolio-ready, not a tutorial clone
- Responsive from 325px upward
- Clear separation of frontend, API/client, and MCP server
- Automated tests for core MCP behavior
- No secrets committed
- Reproducible local setup
