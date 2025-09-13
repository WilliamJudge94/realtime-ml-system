# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the trades service into `/app/services/trades`
WORKDIR /app/services/trades

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# First copy the workspace files needed for dependency resolution
COPY uv.lock pyproject.toml /app/

# Copy only the trades service files
COPY services/trades /app/services/trades

# Install only the trades service dependencies using workspace lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package trades

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["uv", "run", "/app/services/trades/src/trades/main.py"]

# If you want to debug the file system, uncomment the line below
# This will keep the container running and allow you to exec into it
# CMD ["/bin/bash", "-c", "sleep 999999"]