# zeughaus-mcp

MCP Server - Agentic Workbench backed by Nixery.

Execute commands in ephemeral containers with any combination of Nix packages.

## Installation

### Docker (recommended)

Docker is the recommended installation method because it provides **workspace isolation** - the MCP server itself runs in a container with access only to your specified workspace directory.

```bash
docker run --rm -i \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /path/to/workspace:/workspace \
  -e NIXERY_REGISTRY_URL=nixery.zeughaus.dev \
  -e HOST_WORKSPACE_ROOT=/path/to/workspace \
  ghcr.io/gtarkin/zeughaus_mcp:latest
```

### uvx (alternative)

> **Note:** When running via uvx, the MCP server has full access to the host system. Use Docker for better isolation.

```bash
uvx zeughaus-mcp
```

## Configuration

Environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NIXERY_REGISTRY_URL` | Yes | - | Nixery registry URL (see below) |
| `HOST_WORKSPACE_ROOT` | Yes | - | Workspace path to mount into containers |
| `DOCKER_NETWORK_MODE` | No | `host` | Docker network mode |
| `CONTAINER_TIMEOUT_SECONDS` | No | `300` | Container execution timeout |

## Nixery Registries

[Nixery](https://nixery.dev) is a Docker-compatible registry that builds container images on-the-fly from Nix packages.

### Available Registries

| Registry | Channel | Description |
|----------|---------|-------------|
| `nixery.zeughaus.dev` | nixos-25.11 | Self-hosted instance for zeughaus-mcp (recommended) |
| `nixery.dev` | nixos-unstable | Public Nixery instance by Google |

### nixery.zeughaus.dev (Recommended)

The default registry for zeughaus-mcp. This is a self-hosted Nixery instance with:
- **Nix Channel:** `nixos-25.11` (stable packages)
- **Source:** [github.com/NixOS/nixpkgs](https://github.com/NixOS/nixpkgs)
- **Build timeout:** 600 seconds

### nixery.dev (Alternative)

The public Nixery instance maintained by Google. Use this if you prefer:
- **Nix Channel:** `nixos-unstable` (latest packages)
- No dependency on third-party infrastructure

To use the public registry, set:
```
NIXERY_REGISTRY_URL=nixery.dev
```

## MCP Client Configuration

### Claude Desktop (Docker - recommended)

```json
{
  "mcpServers": {
    "zeughaus": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/path/to/workspace:/workspace",
        "-e", "NIXERY_REGISTRY_URL=nixery.zeughaus.dev",
        "-e", "HOST_WORKSPACE_ROOT=/path/to/workspace",
        "ghcr.io/gtarkin/zeughaus_mcp:latest"
      ]
    }
  }
}
```

### Claude Desktop (uvx)

```json
{
  "mcpServers": {
    "zeughaus": {
      "command": "uvx",
      "args": ["zeughaus-mcp"],
      "env": {
        "NIXERY_REGISTRY_URL": "nixery.zeughaus.dev",
        "HOST_WORKSPACE_ROOT": "/path/to/workspace"
      }
    }
  }
}
```

## License

MIT
