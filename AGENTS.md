# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zeughaus MCP is an MCP (Model Context Protocol) server that provides ephemeral container execution using Nix packages from a Nixery registry. It allows agents to run commands in containers with any combination of Nix packages.

## Development Commands

```bash
# Install dependencies (using uv)
uv pip install -e .

# Run the server (stdio mode, default for MCP clients)
zeughaus-mcp

# Run the server (SSE mode for HTTP transport)
zeughaus-mcp --sse --port 8000

# Build the package
python -m build

# Build Docker image locally
docker build -t zeughaus-mcp .
```

## Required Environment Variables

- `NIXERY_REGISTRY_URL` - Nixery registry URL (e.g., `nixery.zeughaus.dev` or `nixery.dev`)
- `HOST_WORKSPACE_ROOT` - Absolute path to workspace directory that gets mounted into containers

## Architecture

The entire server is implemented in a single file: `src/zeughaus_mcp/__init__.py`

Key components:
- **Settings** (pydantic-settings): Loads configuration from environment variables, optionally from `.env` file
- **FastMCP server**: Provides the MCP protocol implementation via the `fastmcp` library
- **invoke_tool**: The single MCP tool that executes commands in Nixery containers

Container execution flow:
1. Tool receives package list and command
2. Constructs Nixery image URL: `{registry}/shell/{pkg1}/{pkg2}/...`
3. Docker pulls/builds image on-demand from Nixery
4. Runs container with workspace mounted at `/workspace`
5. Returns stdout/stderr output

## Release Process

- Push a tag like `v0.1.0` to trigger both PyPI publish and Docker image build
- Docker images are published to `ghcr.io/gtarkin/zeughaus_mcp`
- PyPI package is published as `zeughaus-mcp`
- Version is defined in `pyproject.toml` and `src/zeughaus_mcp/__init__.py`
