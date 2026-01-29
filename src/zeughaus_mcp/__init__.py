"""Zeughaus MCP Server - Agentic Workbench backed by Nixery.

This MCP server provides ephemeral container execution using Nix packages
from a private Nixery instance. Agents can execute commands with any
combination of Nix packages available in the configured registry.
"""

import argparse
import sys
from pathlib import Path

import docker
from docker.errors import APIError, ContainerError, ImageNotFound
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic_settings import BaseSettings

__version__ = "0.1.1"


class Settings(BaseSettings):
    """Server configuration loaded from environment variables."""

    nixery_registry_url: str
    """Base URL of the private Nixery registry (e.g., docker.my-company.com/nixery-cache)."""

    host_workspace_root: str
    """Absolute path on the host OS containing working files. Mounted into containers."""

    docker_network_mode: str = "host"
    """Network mode for spawned containers."""

    container_timeout_seconds: int = 300
    """Maximum execution time for containers in seconds."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def validate_startup(settings: Settings) -> None:
    """Validate configuration at startup. Fails fast with clear messages."""
    # When running in container, /workspace exists (created in Dockerfile).
    # HOST_WORKSPACE_ROOT is only used for spawning child containers.
    container_workspace = Path("/workspace")
    if container_workspace.exists():
        # Running inside container - /workspace is what matters
        pass
    else:
        # Running directly on host - validate HOST_WORKSPACE_ROOT
        workspace_path = Path(settings.host_workspace_root)
        if not workspace_path.exists():
            print(
                f"ERROR: HOST_WORKSPACE_ROOT does not exist: {settings.host_workspace_root}",
                file=sys.stderr,
            )
            sys.exit(1)
        if not workspace_path.is_dir():
            print(
                f"ERROR: HOST_WORKSPACE_ROOT is not a directory: {settings.host_workspace_root}",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        client = docker.from_env()
        client.ping()
    except Exception as e:
        print(f"ERROR: Cannot connect to Docker daemon: {e}", file=sys.stderr)
        sys.exit(1)


# Initialize MCP server (lazy - tools are registered but not validated yet)
mcp = FastMCP(
    "Zeughaus",
    instructions="Agentic Workbench - Execute commands in ephemeral Nix containers",
)

# Module-level variables initialized in main()
_settings: Settings | None = None
_docker_client: docker.DockerClient | None = None


def _get_settings() -> Settings:
    """Get settings, initializing if needed."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _get_docker_client() -> docker.DockerClient:
    """Get Docker client, initializing if needed."""
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


@mcp.tool
def invoke_tool(packages: list[str], command: str) -> str:
    """Execute a command in an ephemeral container with specified Nix packages.

    The container has read/write access to the workspace directory mounted at /workspace.
    All commands execute with /workspace as the working directory.

    Args:
        packages: List of Nix package names to include in the container.
        command: Shell command to execute in the /workspace directory.

    Returns:
        Combined stdout/stderr output from the command execution.
        If the command fails, includes the exit code in the output.
    """
    settings = _get_settings()
    docker_client = _get_docker_client()

    if not packages:
        raise ToolError("At least one package must be specified")

    if not command.strip():
        raise ToolError("Command cannot be empty")

    # Sort packages alphabetically for consistent image naming
    sorted_pkgs = sorted(packages)

    # Construct Nixery image URL: registry/shell/pkg1/pkg2/...
    image = f"{settings.nixery_registry_url}/shell/{'/'.join(sorted_pkgs)}"

    # Configure volume mount
    volumes = {settings.host_workspace_root: {"bind": "/workspace", "mode": "rw"}}

    try:
        output = docker_client.containers.run(
            image=image,
            command=["sh", "-c", command],
            volumes=volumes,
            working_dir="/workspace",
            network_mode=settings.docker_network_mode,
            remove=True,
            stdout=True,
            stderr=True,
        )

        # Output is combined stdout/stderr as bytes
        if output:
            return output.decode("utf-8", errors="replace")
        return "(no output)"

    except ImageNotFound:
        raise ToolError(
            f"Failed to build Nixery image. Verify package names are correct: {sorted_pkgs}. "
            f"Search the web for 'nixpkgs <package-name>' to find valid package names."
        )
    except ContainerError as e:
        # Container exited with non-zero code - return output, don't crash
        output = e.stderr.decode("utf-8", errors="replace") if e.stderr else "(no output)"
        return f"Command failed (exit code {e.exit_status}):\n{output}"
    except APIError as e:
        raise ToolError(f"Docker API error: {e.explanation or str(e)}")
    except Exception as e:
        raise ToolError(f"Container execution error: {str(e)}")


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="Zeughaus MCP Server - Agentic Workbench backed by Nixery"
    )
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Use SSE transport instead of stdio (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    # Initialize and validate settings
    global _settings, _docker_client
    _settings = Settings()
    validate_startup(_settings)
    _docker_client = docker.from_env()

    if args.sse:
        print(f"Starting Zeughaus MCP Server (SSE) on port {args.port}", file=sys.stderr)
        print(f"Workspace: {_settings.host_workspace_root}", file=sys.stderr)
        print(f"Nixery Registry: {_settings.nixery_registry_url}", file=sys.stderr)
        mcp.run(transport="sse", host="0.0.0.0", port=args.port)
    else:
        # stdio transport (default for MCP clients)
        mcp.run()


if __name__ == "__main__":
    main()
