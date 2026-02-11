.PHONY: help build up down restart logs ps health test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the Docker image
	docker-compose build

up: ## Start the service
	docker-compose up -d
	@echo "✅ Service started!"
	@echo "🔗 SSE endpoint: http://localhost:8000/sse"
	@echo "❤️  Health check: http://localhost:8000/health"

down: ## Stop the service
	docker-compose down

restart: ## Restart the service
	docker-compose restart
	@echo "♻️  Service restarted!"

logs: ## Show logs
	docker-compose logs -f

ps: ## Show running containers
	docker-compose ps

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "❌ Service not responding"

test: ## Run tests
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/health
	@echo "\n\nTesting SSE endpoint..."
	@curl -N http://localhost:8000/sse &
	@sleep 2
	@killall curl 2>/dev/null || true

stats: ## Show container stats
	docker stats eve-wiki-mcp --no-stream

clean: ## Remove containers and images
	docker-compose down -v
	docker rmi eve-wiki-mcp 2>/dev/null || true
	@echo "🧹 Cleaned up!"

rebuild: down build up ## Rebuild and restart

update: ## Pull changes and rebuild
	git pull
	$(MAKE) rebuild

install: ## Initial setup
	@echo "📦 Installing EVE Wiki MCP Server..."
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	$(MAKE) build
	$(MAKE) up
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Test with: make health"
	@echo "2. Add to Claude Desktop config:"
	@echo "   {"
	@echo "     \"mcpServers\": {"
	@echo "       \"eve-university-wiki\": {"
	@echo "         \"url\": \"http://YOUR_IP:8000/sse\""
	@echo "       }"
	@echo "     }"
	@echo "   }"

backup: ## Backup configuration
	@mkdir -p backup
	@cp docker-compose.yml backup/docker-compose.yml.bak
	@cp .env backup/.env.bak 2>/dev/null || true
	@echo "💾 Configuration backed up to backup/"

rpi-build: ## Build for Raspberry Pi (ARM64)
	docker buildx build --platform linux/arm64 -t eve-wiki-mcp:arm64 .

multi-arch: ## Build for multiple architectures
	docker buildx create --name multiarch --use 2>/dev/null || true
	docker buildx build --platform linux/amd64,linux/arm64 -t eve-wiki-mcp:latest .

pull-ghcr: ## Pull pre-built image from GitHub Container Registry
	@echo "📥 Pulling pre-built image from GHCR..."
	docker pull ghcr.io/YOUR_USERNAME/eve-wiki-mcp:latest
	@echo "✅ Image pulled successfully!"

deploy-ghcr: pull-ghcr ## Deploy using pre-built GHCR image
	@echo "🚀 Starting service with GHCR image..."
	docker-compose -f docker-compose.ghcr.yml up -d
	@echo "✅ Service started!"
	@echo "🔗 SSE endpoint: http://localhost:8000/sse"
	@echo "❤️  Health check: http://localhost:8000/health"

update-from-git: ## Update from git and rebuild
	@echo "📥 Pulling latest changes from git..."
	git pull origin main
	@echo "🏗️  Rebuilding..."
	$(MAKE) rebuild
	@echo "✅ Update complete!"
