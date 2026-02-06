# Makefile for Docker operations

# Default Docker Compose file to use.
# Users can override this by running `make COMPOSE_FILE=docker-compose.bot-only.yml <target>`
COMPOSE_FILE ?= docker-compose.yml

.PHONY: help build up down restart logs clean dev test rebuild health pull setup

# Default target
help: ## Show this help message
	@echo "Available commands (defaulting to $(COMPOSE_FILE) unless COMPOSE_FILE is overridden):"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'
	@echo
	@echo "To use a different compose file (e.g., for bot-only deployment):"
	@echo "  make COMPOSE_FILE=docker-compose.bot-only.yml up"

# Build the bot container
build: ## Build the Docker containers
	docker-compose -f $(COMPOSE_FILE) build

# Start all services
up: ## Start all services (bot + Ollama by default, or bot-only if COMPOSE_FILE is overridden)
	docker-compose -f $(COMPOSE_FILE) up -d

# Start in development mode (assumes base is docker-compose.yml)
dev: ## Start in development mode with source mounting
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
down: ## Stop all services
	docker-compose -f $(COMPOSE_FILE) down

# Restart services
restart: ## Restart all services
	docker-compose -f $(COMPOSE_FILE) restart

# View logs
logs: ## Show logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

# Show bot logs only
logs-bot: ## Show only bot logs
	docker-compose -f $(COMPOSE_FILE) logs -f telegram-bot

# Show Ollama logs only (only applicable for full stack deployment)
logs-ollama: ## Show only Ollama logs
	docker-compose -f $(COMPOSE_FILE) logs -f ollama

# Clean up
clean: ## Remove containers, networks, and volumes
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

# Rebuild and restart
rebuild: ## Rebuild and restart all services
	docker-compose -f $(COMPOSE_FILE) down
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	docker-compose -f $(COMPOSE_FILE) up -d

# Run tests in container
test: ## Run tests in the bot container
	docker-compose -f $(COMPOSE_FILE) exec telegram-bot pytest

# Shell access to bot container
shell: ## Open shell in bot container
	docker-compose -f $(COMPOSE_FILE) exec telegram-bot bash

# Check container health
health: ## Check health of all containers
	docker-compose -f $(COMPOSE_FILE) ps
	@echo
	docker-compose -f $(COMPOSE_FILE) exec telegram-bot python -c "import sys; print('Bot container: OK')" || echo "Bot container: FAILED"
	@if [ "$(COMPOSE_FILE)" = "docker-compose.yml" ]; then \
		docker-compose -f $(COMPOSE_FILE) exec ollama ollama list || echo "Ollama container: FAILED"; \
	else \
		echo "Ollama container check skipped for bot-only deployment."; \
	fi

# Pull latest Ollama image (only applicable for full stack deployment)
pull: ## Pull latest Ollama image
	@if [ "$(COMPOSE_FILE)" = "docker-compose.yml" ]; then \
		docker-compose -f $(COMPOSE_FILE) pull ollama; \
	else \
		echo "Ollama pull skipped for bot-only deployment."; \
	fi

# Setup environment file
setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please edit with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi
