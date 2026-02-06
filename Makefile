# Makefile for Docker operations

.PHONY: help build up down restart logs clean dev test rebuild health pull setup

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Build the bot container
build: ## Build the Docker containers
	docker-compose build

# Start the bot service
up: ## Start the bot service
	docker-compose up -d

# Start in development mode
dev: ## Start in development mode with source mounting
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop the bot service
down: ## Stop the bot service
	docker-compose down

# Restart the bot service
restart: ## Restart the bot service
	docker-compose restart

# View logs from the bot service
logs: ## Show logs from the bot service
	docker-compose logs -f

# Show bot logs only
logs-bot: ## Show only bot logs
	docker-compose logs -f telegram-bot

# Clean up
clean: ## Remove containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

# Rebuild and restart
rebuild: ## Rebuild and restart the bot service
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Run tests in container
test: ## Run tests in the bot container
	docker-compose exec telegram-bot pytest

# Shell access to bot container
shell: ## Open shell in bot container
	docker-compose exec telegram-bot bash

# Check container health
health: ## Check health of the bot container
	docker-compose ps
	@echo
	docker-compose exec telegram-bot python -c "import sys; print('Bot container: OK')" || echo "Bot container: FAILED"

# Pull latest Ollama image (Not applicable for this bot-only setup)
pull: ## Pull latest Ollama image (Not applicable for this bot-only setup)
	@echo "Ollama pull is not applicable for this bot-only deployment."

# Setup environment file
setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please edit with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi