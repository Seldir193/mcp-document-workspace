# MCP Document Workspace

A compact portfolio project that demonstrates Model Context Protocol primitives in a real document workflow.

## What it demonstrates
- Direct MCP resources
- Templated MCP resources
- MCP tools
- Reusable MCP prompts
- Angular document workspace UI
- Automated backend and frontend tests

## Stack
- Angular 20 + TypeScript + SCSS
- Python 3.14
- MCP Python SDK 2.x
- Pytest

## Current MCP contract
- Resource: docs://documents
- Resource template: docs://documents/{doc_id}
- Tool: edit_document
- Prompt: summarize
- Prompt: format

## Backend
From backend:

    .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    .\.venv\Scripts\python.exe -m pytest -q
    .\.venv\Scripts\python.exe -m mcp_workspace.server

## Frontend
From frontend:

    npm install
    npm run build
    npm test -- --watch=false --browsers=ChromeHeadless

## Status
Phase 1 foundation is implemented. The Angular shell currently uses local sample data while the MCP client-to-UI bridge is the next integration step.

## Next milestones
1. Add an MCP client module.
2. Expose a thin local HTTP bridge for the Angular UI.
3. Connect resource listing and document reading.
4. Connect summarize, format and edit actions.
5. Add activity logging and an MCP Inspector demo.
6. Add CI and final portfolio screenshots.
