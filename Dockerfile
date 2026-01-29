FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install the package
RUN uv pip install --system .

# Create workspace directory (will be overwritten by volume mount at runtime)
RUN mkdir -p /workspace

# Default to stdio transport
ENTRYPOINT ["zeughaus-mcp"]
