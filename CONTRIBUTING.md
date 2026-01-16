# Contributing to Text2SQL Lab

Thank you for your interest in contributing to Text2SQL Lab! This document provides guidelines and instructions for contributing.

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features
- 📚 Add examples and tutorials

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/text2sql-lab.git
cd text2sql-lab
```

### 2. Set Up Development Environment

```bash
# Copy environment file
cp .env.example .env

# Start services
make start

# Install model
make install-model

# Run tests
make test
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused

Example:
```python
def execute_text2sql(db_connection, natural_query: str, 
                     log_execution: bool = True) -> Dict[str, Any]:
    """
    Complete text2sql pipeline: generate SQL and execute it
    
    Args:
        db_connection: Database connection object
        natural_query: Natural language query
        log_execution: Whether to log the execution
    
    Returns:
        Dictionary with results and metadata
    """
    # Implementation
    pass
```

### Testing

- Test your changes thoroughly
- Add tests for new features
- Ensure existing tests pass
- Test with different LLM models

### Documentation

- Update README.md if adding features
- Add docstrings to new functions
- Update relevant notebooks
- Add examples for new functionality

### Commit Messages

Use clear and descriptive commit messages:

```bash
# Good
git commit -m "Add support for multi-table joins in text2sql"
git commit -m "Fix embedding dimension mismatch in RAG"
git commit -m "Update setup documentation with GPU requirements"

# Not so good
git commit -m "Fix bug"
git commit -m "Update stuff"
git commit -m "WIP"
```

## Adding New Features

### 1. New Utility Function

```python
# Add to appropriate file in src/utils/
def your_new_function(param1: type, param2: type) -> return_type:
    """
    Clear description of what the function does
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Description of return value
    """
    # Implementation
    pass
```

### 2. New Notebook

Create notebooks in the `notebooks/` directory:
- Follow the naming convention: `##_descriptive_name.ipynb`
- Include clear explanations
- Add code comments
- Show expected outputs

### 3. New Service

If adding a new service to docker-compose:
- Update `docker-compose.yml`
- Update documentation
- Add to `Makefile` if needed
- Test integration with existing services

## Submitting Changes

### 1. Push Your Changes

```bash
git add .
git commit -m "Your descriptive commit message"
git push origin feature/your-feature-name
```

### 2. Create Pull Request

- Go to GitHub and create a Pull Request
- Fill in the PR template
- Link any related issues
- Describe your changes clearly

### 3. PR Review Process

- Maintainers will review your PR
- Address any feedback
- Make requested changes
- Once approved, your PR will be merged

## Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tested locally
- [ ] Added/updated tests
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Commit messages are clear

## Screenshots (if applicable)
Add screenshots for UI changes
```

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, etc.)
- Error messages and logs

Example:
```markdown
**Describe the bug**
Text2SQL fails when query contains special characters

**To Reproduce**
1. Open notebook 03_text2sql_basic.ipynb
2. Run query: "Show employees with name containing 'O'Brien'"
3. See error

**Expected behavior**
Should handle special characters in queries

**Environment**
- OS: Ubuntu 22.04
- Docker: 24.0.5
- Python: 3.11

**Error message**
```
SyntaxError: unterminated string literal
```
```

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Example of how it would work
- Any relevant references

## Code Review Checklist

When reviewing code:
- [ ] Code is readable and well-documented
- [ ] Tests are included and pass
- [ ] No security vulnerabilities
- [ ] Performance is acceptable
- [ ] Documentation is updated
- [ ] Follows project conventions

## Development Tips

### Running Specific Services

```bash
# Only start database and Ollama
docker-compose up -d postgres ollama

# View logs for specific service
docker-compose logs -f jupyter
```

### Debugging

```bash
# Enter Jupyter container
make shell-jupyter

# Run Python interactively
python
>>> from src.utils.db_utils import DatabaseConnection
>>> db = DatabaseConnection()
>>> db.get_all_tables()

# Check database directly
make shell-db
\dt
SELECT * FROM employees LIMIT 5;
```

### Testing Changes

```bash
# Rebuild after code changes
docker-compose build jupyter
docker-compose up -d jupyter

# Test in notebook
# Open JupyterLab and run test notebook
```

## Adding Examples

Good examples should:
1. Be self-contained
2. Include clear explanations
3. Show expected output
4. Handle errors gracefully
5. Follow best practices

```python
# Good example
from src.utils.text2sql_utils import execute_text2sql
from src.utils.db_utils import DatabaseConnection

# Initialize database connection
db = DatabaseConnection()

# Execute a natural language query
result = execute_text2sql(
    db, 
    "Show me employees with salary greater than 6000000"
)

# Check if successful and display results
if result['success']:
    print(f"Found {result['row_count']} employees")
    print(result['results'])
else:
    print(f"Error: {result['error']}")
```

## Community

- Be respectful and inclusive
- Help others learn
- Share knowledge
- Give constructive feedback
- Celebrate contributions

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to Text2SQL Lab! 🎉
