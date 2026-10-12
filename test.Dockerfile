FROM ghcr.io/astral-sh/uv:0.11.2 AS uv

FROM python:3.12-slim

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY coding_assistant.py ./
COPY tests ./tests

ENTRYPOINT ["uv", "run", "--frozen", "--no-dev", "python", "-m", "pytest"]
