# The official mcr.microsoft.com/playwright/python images ship Python 3.12,
# which is below this project's requires-python, so build from python:3.14.
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    OUTPUT_DIR=/data/output

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Dependencies first so edits to the source don't invalidate the layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Chromium plus the system libraries it needs.
RUN playwright install --with-deps chromium

COPY magazine_scraper ./magazine_scraper

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "magazine_scraper.server:app", "--host", "0.0.0.0", "--port", "8000"]
