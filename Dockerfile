FROM python:3.13-slim-bookworm
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r frontier && useradd -r -g frontier -d /app frontier

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* .python-version* /app/

WORKDIR /app
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH"
ENV HF_ENDPOINT="https://hf-mirror.com"

RUN uv run playwright install chromium
RUN uv run playwright install-deps chromium

# Copy application code
COPY . /app

# Ensure cache directories exist and are writable by the app user
RUN mkdir -p /app/cache /app/cache/sandbox /app/cache/chroma \
    && chown -R frontier:frontier /app

USER frontier

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/api/dashboard/status').raise_for_status()" || exit 1

ENTRYPOINT [ "uv","run","nb","run" ]
