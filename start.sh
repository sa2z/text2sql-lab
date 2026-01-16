#!/bin/bash

# Text2SQL Lab - Quick Start Script
# This script helps you get started with the text2sql-lab environment

set -e

echo "=========================================="
echo "Text2SQL Lab - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi
echo ""

# Start services
echo "Starting services..."
echo "This may take a few minutes on first run..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "Checking service status..."

# Check PostgreSQL with pg_isready
echo -n "PostgreSQL: "
if docker exec text2sql-postgres pg_isready -U text2sql > /dev/null 2>&1; then
    echo "✓ Ready"
else
    echo "⚠ Not ready yet (still initializing)"
fi

# Check Ollama with API call
echo -n "Ollama: "
if docker exec text2sql-ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ready"
else
    echo "⚠ Not ready yet"
fi

# Check Jupyter with HTTP request
echo -n "JupyterLab: "
if curl -s -o /dev/null http://localhost:8888 2>&1; then
    echo "✓ Ready"
else
    echo "⚠ Not ready yet"
fi

# Check Open-WebUI
echo -n "Open-WebUI: "
if curl -s -o /dev/null http://localhost:3000 2>&1; then
    echo "✓ Ready"
else
    echo "⚠ Not ready yet"
fi

# Check Langfuse
echo -n "Langfuse: "
if curl -s -o /dev/null http://localhost:3001 2>&1; then
    echo "✓ Ready"
else
    echo "⚠ Not ready yet"
fi

echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Install an LLM model (required):"
echo "   docker exec -it text2sql-ollama ollama pull llama2"
echo ""
echo "2. Access services:"
echo "   - JupyterLab: http://localhost:8888"
echo "   - Open-WebUI: http://localhost:3000"
echo "   - Langfuse:   http://localhost:3001"
echo ""
echo "3. Start with the notebooks in order:"
echo "   - 01_setup_and_connection.ipynb"
echo "   - 02_embedding_and_rag.ipynb"
echo "   - 03_text2sql_basic.ipynb"
echo "   - 04_agent_workflow.ipynb"
echo "   - 05_visualization.ipynb"
echo "   - 06_end_to_end.ipynb"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f"
echo ""
echo "5. Stop services:"
echo "   docker-compose down"
echo ""
echo "For more information, see docs/SETUP.md"
echo "=========================================="
