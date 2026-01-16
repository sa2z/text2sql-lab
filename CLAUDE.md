# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Text2SQL Lab is an on-premises learning environment for practicing Text2SQL (natural language to SQL conversion), RAG (Retrieval-Augmented Generation), and AI Agents using LangChain/LangGraph. It runs entirely locally using Docker with no external API dependencies (Ollama provides local LLM execution).

## Common Commands

```bash
# Service management
make start              # Start all Docker services
make stop               # Stop all services
make restart            # Restart all services
make logs               # Stream logs from all services
make status             # Check service status
make test               # Test service connectivity

# LLM model management
make install-model      # Install Llama2 in Ollama
make install-mistral    # Install Mistral model
make list-models        # List installed models

# Development
make shell-db           # Open PostgreSQL shell
make shell-jupyter      # Open Jupyter container bash
make build              # Rebuild Docker images
make dev                # Run in foreground (with logs)

# Database
make backup-db          # Backup PostgreSQL database
make reset-db           # Reset database (deletes all data)
```

## Service Access Points

- **JupyterLab**: http://localhost:58889 (no token required)
- **PostgreSQL**: localhost:55433 (user: text2sql, db: text2sql_db)
- **Ollama API**: http://localhost:51435
- **Open-WebUI**: http://localhost:53001
- **Langfuse**: http://localhost:53002

## Architecture

```
JupyterLab (notebooks + Python utils)
    ├── Ollama (local LLM - Llama2/Mistral/CodeLlama)
    ├── PostgreSQL + pgvector (data + vector search)
    ├── Open-WebUI (LLM model management)
    └── Langfuse (LLM observability)
```

**Core data flow:**
```
User Query → LangChain Agent → Text2SQL Generator → PostgreSQL → Results → Visualization
                                      ↓
                              Ollama LLM (local)
```

**Key Python utilities** (`src/utils/`):
- `db_utils.py` - Database connections, schema inspection, safe query execution
- `text2sql_utils.py` - Natural language to SQL conversion with LLM
- `embedding_utils.py` - Text embeddings (Sentence Transformers) + pgvector search
- `viz_utils.py` - Automatic chart generation (Plotly/Matplotlib/Seaborn)

**6 Progressive notebooks** (`notebooks/`):
1. `01_setup_and_connection.ipynb` - Service verification, schema exploration
2. `02_embedding_and_rag.ipynb` - Embeddings, vector storage, semantic search
3. `03_text2sql_basic.ipynb` - Natural language to SQL conversion
4. `04_agent_workflow.ipynb` - LangChain agents, LangGraph workflows
5. `05_visualization.ipynb` - Chart generation from query results
6. `06_end_to_end.ipynb` - Complete pipeline demonstration

## Database Schema

Business tables: `employees`, `departments`, `projects`, `project_assignments`, `sales`, `customers`

RAG/ML tables: `documents` (with embeddings), `lexicon` (terminology with embeddings), `query_history` (logging)

## Code Style

- Follow PEP 8 for Python code
- Add docstrings to functions with Args/Returns sections
- Use type hints for function parameters and returns

## Development Workflow

After modifying Python code in `src/utils/`:
```bash
docker-compose build jupyter
docker-compose up -d jupyter
```

For debugging:
```bash
make shell-jupyter      # Access Jupyter container
make shell-db           # Direct database access (psql)
```
