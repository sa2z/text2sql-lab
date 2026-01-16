.PHONY: help start stop restart logs clean build pull install-model status shell-db shell-jupyter test

# Default target
help:
	@echo "Text2SQL Lab - Available Commands:"
	@echo ""
	@echo "  make start          - Start all services"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make status         - Check status of all services"
	@echo "  make clean          - Stop and remove all containers and volumes"
	@echo "  make build          - Build Docker images"
	@echo "  make pull           - Pull latest Docker images"
	@echo "  make install-model  - Install Llama2 model in Ollama"
	@echo "  make shell-db       - Open PostgreSQL shell"
	@echo "  make shell-jupyter  - Open Jupyter container shell"
	@echo "  make backup-db      - Backup database"
	@echo "  make test           - Run basic connectivity tests"
	@echo ""

# Start services
start:
	@echo "Starting Text2SQL Lab services..."
	docker-compose up -d
	@echo ""
	@echo "Services started!"
	@echo "Access points:"
	@echo "  - JupyterLab: http://localhost:15436"
	@echo "  - Open-WebUI: http://localhost:15434"
	@echo "  - Langfuse:   http://localhost:15435"
	@echo ""
	@echo "Don't forget to install an LLM model:"
	@echo "  make install-model"

# Stop services
stop:
	@echo "Stopping Text2SQL Lab services..."
	docker-compose down
	@echo "Services stopped!"

# Restart services
restart:
	@echo "Restarting Text2SQL Lab services..."
	docker-compose restart
	@echo "Services restarted!"

# View logs
logs:
	docker-compose logs -f

# Check status
status:
	@echo "Service Status:"
	@docker-compose ps

# Clean everything
clean:
	@echo "WARNING: This will remove all containers, volumes, and data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Cleaned!"; \
	else \
		echo "Cancelled."; \
	fi

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "Build complete!"

# Pull images
pull:
	@echo "Pulling latest Docker images..."
	docker-compose pull
	@echo "Pull complete!"

# Install LLM model
install-model:
	@echo "Installing Llama2 model in Ollama..."
	@echo "This may take a while depending on your internet connection..."
	docker exec -it text2sql-ollama ollama pull llama2
	@echo ""
	@echo "Model installed! You can now use text2sql features."

# Install alternative model
install-mistral:
	@echo "Installing Mistral model in Ollama..."
	docker exec -it text2sql-ollama ollama pull mistral

install-codellama:
	@echo "Installing CodeLlama model in Ollama..."
	docker exec -it text2sql-ollama ollama pull codellama

# List installed models
list-models:
	@echo "Installed models:"
	docker exec -it text2sql-ollama ollama list

# Open database shell
shell-db:
	docker exec -it text2sql-postgres psql -U text2sql -d text2sql_db

# Open Jupyter shell
shell-jupyter:
	docker exec -it text2sql-jupyter bash

# Backup database
backup-db:
	@echo "Backing up database..."
	@mkdir -p backups
	docker exec text2sql-postgres pg_dump -U text2sql text2sql_db | gzip > backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz
	@echo "Backup created in backups/"

# Restore database
restore-db:
	@echo "Available backups:"
	@ls -1 backups/
	@read -p "Enter backup filename: " backup; \
	gunzip -c backups/$$backup | docker exec -i text2sql-postgres psql -U text2sql text2sql_db

# Run tests
test:
	@echo "Running connectivity tests..."
	@echo ""
	@echo "Testing PostgreSQL..."
	@docker exec text2sql-postgres pg_isready -U text2sql && echo "✓ PostgreSQL is ready" || echo "✗ PostgreSQL is not ready"
	@echo ""
	@echo "Testing Ollama..."
	@curl -s http://localhost:15433/api/tags > /dev/null && echo "✓ Ollama is ready" || echo "✗ Ollama is not ready"
	@echo ""
	@echo "Testing JupyterLab..."
	@curl -s http://localhost:15436 > /dev/null && echo "✓ JupyterLab is ready" || echo "✗ JupyterLab is not ready"
	@echo ""
	@echo "Testing Open-WebUI..."
	@curl -s http://localhost:15434 > /dev/null && echo "✓ Open-WebUI is ready" || echo "✗ Open-WebUI is not ready"
	@echo ""

# View resource usage
stats:
	@echo "Resource Usage:"
	docker stats --no-stream

# Reset database (development only)
reset-db:
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose stop postgres; \
		docker volume rm text2sql-lab_postgres_data; \
		docker-compose up -d postgres; \
		echo "Database reset!"; \
	else \
		echo "Cancelled."; \
	fi

# Update dependencies
update-deps:
	@echo "Updating Python dependencies..."
	docker-compose build jupyter --no-cache
	docker-compose up -d jupyter
	@echo "Dependencies updated!"

# Development mode (with auto-reload)
dev:
	docker-compose up

# Production mode (detached)
prod:
	docker-compose up -d
	@echo "Running in production mode"
	@make status
