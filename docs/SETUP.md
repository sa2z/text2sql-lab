# Setup Guide

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB+ free space
- **OS**: Linux, macOS, or Windows with WSL2

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- (Optional) NVIDIA GPU with drivers for GPU acceleration

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/sa2z/text2sql-lab.git
cd text2sql-lab
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (optional)
nano .env
```

Key environment variables:
```env
# Database
POSTGRES_USER=text2sql
POSTGRES_PASSWORD=text2sql123
POSTGRES_DB=text2sql_db

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Expected output:
```
NAME                       STATUS          PORTS
text2sql-postgres          Up              0.0.0.0:5432->5432/tcp
text2sql-ollama           Up              0.0.0.0:11434->11434/tcp
text2sql-open-webui       Up              0.0.0.0:3000->8080/tcp
text2sql-langfuse         Up              0.0.0.0:3001->3000/tcp
text2sql-jupyter          Up              0.0.0.0:8888->8888/tcp
```

### 4. Wait for Services to Initialize

```bash
# Wait for PostgreSQL
docker-compose logs postgres | grep "database system is ready"

# Wait for Ollama
curl http://localhost:11434/api/tags

# Check Jupyter
curl http://localhost:8888
```

### 5. Install LLM Model

```bash
# Install Llama 2 (recommended for starting)
docker exec -it text2sql-ollama ollama pull llama2

# Or install Mistral (faster, less accurate)
docker exec -it text2sql-ollama ollama pull mistral

# Or install CodeLlama (for SQL tasks)
docker exec -it text2sql-ollama ollama pull codellama

# Verify installation
docker exec -it text2sql-ollama ollama list
```

### 6. Verify Database

```bash
# Connect to database
docker exec -it text2sql-postgres psql -U text2sql -d text2sql_db

# Check tables
\dt

# Check sample data
SELECT COUNT(*) FROM employees;
SELECT COUNT(*) FROM departments;

# Exit
\q
```

### 7. Access Services

Open your browser and navigate to:

- **JupyterLab**: http://localhost:8888
- **Open-WebUI**: http://localhost:3000
- **Langfuse**: http://localhost:3001

## GPU Support (Optional)

### NVIDIA GPU Setup

1. Install NVIDIA Docker runtime:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

3. Services will automatically use GPU if available

## Troubleshooting

### Port Conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
services:
  jupyter:
    ports:
      - "9999:8888"  # Change 8888 to 9999
```

### Memory Issues

Increase Docker memory limit:
- Docker Desktop: Settings → Resources → Memory → 8GB+

### Database Connection Issues

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### Ollama Not Responding

```bash
# Restart Ollama
docker-compose restart ollama

# Check logs
docker-compose logs ollama

# Test connection
curl http://localhost:11434/api/tags
```

### Jupyter Kernel Issues

```bash
# Restart Jupyter
docker-compose restart jupyter

# Rebuild image
docker-compose build jupyter
docker-compose up -d jupyter
```

## Development Setup

### Local Python Environment

If you want to develop outside Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=text2sql
export POSTGRES_PASSWORD=text2sql123
export POSTGRES_DB=text2sql_db
export OLLAMA_HOST=http://localhost:11434
```

### Running Tests

```bash
# In Jupyter container
docker exec -it text2sql-jupyter bash

cd /workspace
python -m pytest tests/  # If tests exist
```

## Updating

### Update Docker Images

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose down
docker-compose up -d
```

### Update Python Dependencies

```bash
# Edit requirements.txt
nano requirements.txt

# Rebuild Jupyter image
docker-compose build jupyter
docker-compose up -d jupyter
```

### Update Database Schema

```bash
# Backup database
docker exec text2sql-postgres pg_dump -U text2sql text2sql_db > backup.sql

# Edit init_db.sql
nano scripts/init_db.sql

# Recreate database
docker-compose down -v
docker-compose up -d
```

## Production Considerations

### Security

1. Change default passwords in `.env`
2. Enable SSL for PostgreSQL
3. Use secrets management (Docker secrets, Vault)
4. Implement authentication for Jupyter
5. Set up firewall rules

### Backup

```bash
# Backup database
docker exec text2sql-postgres pg_dump -U text2sql text2sql_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup volumes
docker run --rm -v text2sql-lab_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_data_backup.tar.gz /data
```

### Monitoring

1. Set up Langfuse for LLM monitoring
2. Configure PostgreSQL logging
3. Use Docker health checks
4. Set up alerts for failures

### Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  jupyter:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Next Steps

1. Open JupyterLab: http://localhost:8888
2. Start with `01_setup_and_connection.ipynb`
3. Follow notebooks in order
4. Experiment with your own queries
5. Build custom applications using the utilities

## Getting Help

- Check logs: `docker-compose logs <service>`
- Issues: https://github.com/sa2z/text2sql-lab/issues
- Documentation: See `docs/` folder
