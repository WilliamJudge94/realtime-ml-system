# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install ta-lib
ENV TALIB_DIR=/usr/local
RUN wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
    tar -xzf ta-lib-0.6.4-src.tar.gz && \
    cd ta-lib-0.6.4/ && \
    ./configure --prefix=$TALIB_DIR && \
    make -j$(nproc) && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.6.4-src.tar.gz ta-lib-0.6.4/

# Ensure TA-Lib is linked correctly
RUN ldconfig

# Install the technical_indicators service into `/app/services/technical_indicators`
WORKDIR /app/services/technical_indicators

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# First copy the workspace files needed for dependency resolution
COPY uv.lock pyproject.toml /app/

# Copy only the technical_indicators service files
COPY services/technical_indicators /app/services/technical_indicators

# Install only the technical_indicators service dependencies using workspace lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package technical_indicators

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

CMD ["uv", "run", "/app/services/technical_indicators/src/technical_indicators/main.py"]

# If you want to debug the file system, uncomment the line below
# This will keep the container running and allow you to exec into it
# CMD ["/bin/bash", "-c", "sleep 999999"]