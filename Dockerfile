# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.14
ARG PLAYWRIGHT_VERSION=1.61.0
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

COPY --from=docker.io/astral/uv:0.11.28 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PATH="/app/.venv/bin:${PATH}" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HF_HOME=/app/cache/huggingface \
    TORCH_HOME=/app/cache/torch \
    HF_ENDPOINT=https://hf-mirror.com \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system frontier \
    && useradd --system --gid frontier --home-dir /app --shell /usr/sbin/nologin frontier

WORKDIR /app

FROM base AS dependencies

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

FROM base AS runtime-system

ARG PLAYWRIGHT_VERSION
RUN uvx --from "playwright==${PLAYWRIGHT_VERSION}" playwright install --with-deps --only-shell chromium \
    && rm -rf /root/.cache/uv \
    && mkdir -p /app/cache /ms-playwright \
    && chown -R frontier:frontier /app /ms-playwright

COPY --chown=frontier:frontier . /app

USER frontier

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/dashboard/', timeout=5).close()"]

ENTRYPOINT ["nb", "run"]

FROM runtime-system AS runtime

COPY --from=dependencies --chown=frontier:frontier /app/.venv /app/.venv

FROM dependencies AS content-check-dependencies

RUN uv sync --locked --no-dev --no-install-project --extra content-check

FROM runtime-system AS runtime-content-check

COPY --from=content-check-dependencies --chown=frontier:frontier /app/.venv /app/.venv

# Keep the lightweight image as the default target for `docker build .`.
FROM runtime AS default
