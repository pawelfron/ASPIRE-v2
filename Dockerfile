FROM python:3.13-slim-bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src/ /app/src/
RUN cd src/aspire_v2/frontend && \
    npm ci || npm install && \
    npm run build

FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        curl \
        procps \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libatspi2.0-0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libpango-1.0-0 \
        libcairo2 && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system --gid 1000 aspire && \
    useradd --system --uid 1000 --gid aspire --create-home --home-dir /home/aspire aspire

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/src /app/src

RUN mkdir -p /ms-playwright && \
    playwright install --with-deps chromium && \
    plotly_get_chrome -y && \
    mkdir -p /app/src/aspire_v2/staticfiles && \
    chown -R aspire:aspire /app /home/aspire /ms-playwright

COPY docker-entrypoint.sh docker-entrypoint.dev.sh /app/
RUN chmod +x /app/docker-entrypoint.sh /app/docker-entrypoint.dev.sh

WORKDIR /app/src/aspire_v2

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
