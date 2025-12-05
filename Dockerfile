FROM python:3.13-slim-bookworm

WORKDIR /app

RUN apt update && \
    apt install -y npm postgresql-client && \
    apt clean

COPY pyproject.toml /app/
RUN pip install --no-cache-dir .

COPY src/ /app/src/
RUN cd src/aspire_v2/frontend && \
    npm install && \
    npm run build

COPY docker-entrypoint.sh /app/
