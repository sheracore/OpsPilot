# ---- build stage: resolve and install dependencies ----
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# dependencies first: this layer is cached until pyproject.toml/uv.lock change
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# then the project itself, installed (not editable) into the venv
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# ---- runtime stage: only the venv, no uv, no build files ----
FROM python:3.12-slim
RUN useradd --system --create-home app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health', timeout=2)"
CMD ["uvicorn", "opspilot.api:app", "--host", "0.0.0.0", "--port", "8100"]
