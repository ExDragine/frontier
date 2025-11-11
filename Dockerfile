FROM python:3.13-slim-bookworm
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/
RUN sudo apt-get update && sudo apt-get install -y\
    git\
    nodejs

ARG version=22

ADD . /app

WORKDIR /app
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"

RUN uv run playwright install
RUN uv run playwright install-deps

ENTRYPOINT [ "uv","run","nb","run" ]