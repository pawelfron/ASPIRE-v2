# ASPIRE-v2

Reimplementation of ASPIRE: Assistive System for Performance Evaluation in IR,
https://github.com/GiorgosPeikos/ASPIRE.

## Requirements

- Docker and Docker Compose v2
- A `.env` file (copy from `.env.example`)

```bash
cp .env.example .env
# Edit secrets, DOMAIN, CERTBOT_EMAIL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
```

## Development

Hot-reload for Django, Celery, and frontend (Tailwind/TypeScript):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

- App via nginx: http://localhost:8080
- Django directly: http://localhost:8000
- Flower: http://localhost:8080/flower/ (or :5555)
- RabbitMQ management: http://localhost:8080/rabbitmq/ (nginx basic auth + RabbitMQ login)
- MinIO console: http://localhost:8080/minio/ (nginx basic auth + MinIO login)

Nginx basic auth for admin UIs uses `NGINX_ADMIN_USER` / `NGINX_ADMIN_PASS`.

## Production

```bash
docker compose up -d --build
```

- HTTP :80 redirects to HTTPS :443
- TLS certificates live in the `certbot_certs` volume
- On first start nginx bootstraps a short-lived self-signed cert so the stack can boot

### Issue a Let's Encrypt certificate

Set `DOMAIN` and `CERTBOT_EMAIL` in `.env`, ensure DNS points at the host, then:

```bash
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$CERTBOT_EMAIL" \
  --agree-tos --no-eff-email

docker compose exec nginx nginx -s reload
```

The `certbot` service renews certificates roughly every 12 hours.

### Admin UIs (behind nginx)

| Path | Service | Auth |
|------|---------|------|
| `/flower/` | Celery Flower | Flower basic auth (`FLOWER_USER` / `FLOWER_PASS`) |
| `/rabbitmq/` | RabbitMQ management | Nginx basic auth + RabbitMQ credentials |
| `/minio/` | MinIO console | Nginx basic auth + MinIO credentials |
| `/minio-api/` | MinIO S3 API | Nginx basic auth + MinIO credentials |

### Process model

- **server**: Gunicorn with `uvicorn.workers.UvicornWorker` (ASGI / Channels WebSockets)
- **worker**: Celery (late ack, prefetch 1, concurrency via `CELERY_WORKER_CONCURRENCY`)
- **nginx**: TLS termination, static files, reverse proxy, WebSocket upgrade

## Environment

See [`.env.example`](.env.example) for the full list. Important keys:

- `DJANGO_SECRET_KEY`, `MODE` (`PROD` or `DEBUG`)
- `DB_USER`, `DB_PASS`
- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` (comma-separated; include your HTTPS origin in prod)
- `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`
- `RABBITMQ_USER`, `RABBITMQ_PASS`
- `FLOWER_USER`, `FLOWER_PASS`
- `NGINX_ADMIN_USER`, `NGINX_ADMIN_PASS`
- `DOMAIN`, `CERTBOT_EMAIL`
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`

If a secret value contains `$`, escape it as `$$` in `.env` so Docker Compose does not treat it as interpolation.
