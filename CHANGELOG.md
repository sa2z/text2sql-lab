# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

#### Port Configuration Updates
To prevent conflicts with other containers running on the same server, all service ports have been updated using a "5" prefix with +1 offset pattern:

- **PostgreSQL**: Changed from `5432` to `55433` (host port)
  - Pattern: 5 + 5432 + 1 = 55433
  - Internal container port remains `5432`
  - Update connection strings to use `localhost:55433`
  
- **Ollama**: Changed from `11434` to `51435` (host port)
  - Pattern: 5 + (11434 + 1 without first digit) = 51435
  - Internal container port remains `11434`
  - API endpoint now available at `http://localhost:51435`
  
- **Open-WebUI**: Changed from `3000` to `53001` (host port)
  - Pattern: 5 + 3000 + 1 = 53001
  - Internal container port remains `8080`
  - Web interface now available at `http://localhost:53001`
  
- **Langfuse**: Changed from `3001` to `53002` (host port)
  - Pattern: 5 + 3001 + 1 = 53002
  - Internal container port remains `3000`
  - Web interface now available at `http://localhost:53002`
  
- **JupyterLab**: Changed from `8888` to `58889` (host port)
  - Pattern: 5 + 8888 + 1 = 58889
  - Internal container port remains `8888`
  - Web interface now available at `http://localhost:58889`

**Note**: All ports now use a "5" prefix with +1 offset from standard ports, making them easy to identify while avoiding conflicts.

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
   POSTGRES_PORT=55433
   OLLAMA_HOST=http://localhost:51435
   LANGFUSE_HOST=http://localhost:53002
   ```

2. **Update any hardcoded URLs** in your notebooks or scripts:
   - JupyterLab: `http://localhost:58889`
   - Open-WebUI: `http://localhost:53001`
   - Langfuse: `http://localhost:53002`
   - PostgreSQL: `localhost:55433`
   - Ollama: `http://localhost:51435`

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

**Port Conflicts**: Using standard ports (like 5432 for PostgreSQL, 3000 for web services) can cause conflicts when multiple projects or containers are running on the same server. The new port assignments use a "5" prefix with +1 offset pattern (e.g., 5432 → 55433) which:
- Reduces the likelihood of conflicts with other services
- Makes it easy to identify modified ports (all have "5" prefix)
- Maintains recognizability of the original port numbers

**Version Compatibility**: The previous configuration had `langchain==0.1.0` with `langchain-community==0.3.27`, which caused compatibility issues due to the significant version gap. The updated minimum version constraints ensure compatibility while allowing for future updates.
