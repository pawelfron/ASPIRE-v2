.PHONY: help deploy dev

help:
	@echo "ASPIRE-v2 Make targets:"
	@echo "  make setup   - Install project dependencies"
	@echo "  make deploy  - Start production stack (docker compose up -d --build)"
	@echo "  make dev     - Start development stack with hot-reload"
	@echo "  make test    - Run tests"
	@echo "  make help    - Show this message"

setup:
	uv sync --dev
 
deploy:
	docker compose up -d --build

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

test:
	uv run pytest
