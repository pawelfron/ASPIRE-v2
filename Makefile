.PHONY: help deploy dev

help:
	@echo "ASPIRE-v2 Make targets:"
	@echo "  make deploy  - Start production stack (docker compose up -d --build)"
	@echo "  make dev     - Start development stack with hot-reload"
	@echo "  make help    - Show this message"

deploy:
	docker compose up -d --build

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
