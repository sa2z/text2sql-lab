# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

#### Port Configuration Updates
To prevent conflicts with other containers running on the same server, all service ports have been updated to use non-standard ports:

- **PostgreSQL**: Changed from `5432` to `5433` (host port)
  - Internal container port remains `5432`
  - Update connection strings to use `localhost:5433`
  
- **Ollama**: Changed from `11434` to `11435` (host port)
  - Internal container port remains `11434`
  - API endpoint now available at `http://localhost:11435`
  
- **Open-WebUI**: Changed from `3000` to `3002` (host port)
  - Internal container port remains `8080`
  - Web interface now available at `http://localhost:3002`
  
- **Langfuse**: Changed from `3001` to `3003` (host port)
  - Internal container port remains `3000`
  - Web interface now available at `http://localhost:3003`
  
- **JupyterLab**: Changed from `8888` to `8889` (host port)
  - Internal container port remains `8888`
  - Web interface now available at `http://localhost:8889`

#### Dependency Version Updates
Updated Python package versions to resolve compatibility issues:

- **langchain**: Changed from `==0.1.0` to `>=0.3.0`
  - Updated to ensure compatibility with `langchain-community==0.3.27`
  - Uses minimum version constraint to allow for future compatible updates
  
- **langgraph**: Changed from `==0.0.20` to `>=0.2.0`
  - Updated to ensure compatibility with `langchain>=0.3.0`
  - Uses minimum version constraint to allow for future compatible updates

### Migration Guide

If you are upgrading from a previous version, please note the following changes:

1. **Update your `.env` file** (or create from `.env.example`):
   ```env
   POSTGRES_PORT=5433
   OLLAMA_HOST=http://localhost:11435
   LANGFUSE_HOST=http://localhost:3003
   ```

2. **Update any hardcoded URLs** in your notebooks or scripts:
   - JupyterLab: `http://localhost:8889`
   - Open-WebUI: `http://localhost:3002`
   - Langfuse: `http://localhost:3003`
   - PostgreSQL: `localhost:5433`
   - Ollama: `http://localhost:11435`

3. **Rebuild containers** after updating:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Reinstall Python dependencies** in the Jupyter container:
   ```bash
   make update-deps
   ```

### Files Modified

- `docker-compose.yml`: Updated all port mappings
- `.env.example`: Updated default port configurations
- `Makefile`: Updated port references in commands
- `README.md`: Updated documentation with new port information
- `requirements.txt`: Updated langchain and langgraph version constraints
- `CHANGELOG.md`: Created to document changes (this file)

### Why These Changes?

**Port Conflicts**: Using standard ports (like 5432 for PostgreSQL, 3000 for web services) can cause conflicts when multiple projects or containers are running on the same server. The new port assignments reduce the likelihood of such conflicts.

**Version Compatibility**: The previous configuration had `langchain==0.1.0` with `langchain-community==0.3.27`, which caused compatibility issues due to the significant version gap. The updated minimum version constraints ensure compatibility while allowing for future updates.
