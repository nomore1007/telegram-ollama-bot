# Makefile for Docker operations

.PHONY: help build up down restart logs clean dev test

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Build the bot container
build: ## Build the Docker containers
	docker-compose build

# Start all services
up: ## Start all services (bot + Ollama)
	docker-compose up -d

# Start in development mode
dev: ## Start in development mode with source mounting
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
down: ## Stop all services
	docker-compose down

# Restart services
restart: ## Restart all services
	docker-compose restart

# View logs
logs: ## Show logs from all services
	docker-compose logs -f

# Show bot logs only
logs-bot: ## Show only bot logs
	docker-compose logs -f telegram-bot

# Show Ollama logs only
logs-ollama: ## Show only Ollama logs
	docker-compose logs -f ollama

# Clean up
clean: ## Remove containers, networks, and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

# Rebuild and restart
rebuild: ## Rebuild and restart all services
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
health: ## Check health of all containers
	docker-compose ps
	@echo
	docker-compose exec telegram-bot python -c "import sys; print('Bot container: OK')" || echo "Bot container: FAILED"
	docker-compose exec ollama ollama list || echo "Ollama container: FAILED"

# Pull latest Ollama image
pull: ## Pull latest Ollama image
	docker-compose pull ollama

# Setup environment file
setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please edit with your configuration."; \
	else \
		echo ".env file already exists."; \
	fi