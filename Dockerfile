FROM python:3.13-slim-bookworm

RUN apt update && \
    apt install -y npm postgresql-client && \
    apt clean

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install --no-cache-dir .
RUN playwright install --with-deps chromium
RUN plotly_get_chrome -y

COPY src/ /app/src/
RUN cd src/aspire_v2/frontend && \
    npm install && \
    npm run build

COPY docker-entrypoint.sh /app/
