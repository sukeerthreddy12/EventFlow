FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv


COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/

WORKDIR /app/backend

RUN uv sync --frozen --no-dev --directory ..

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

RUN chmod +x /app/backend/entrypoint.sh

ENTRYPOINT ["/app/backend/entrypoint.sh"]
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]