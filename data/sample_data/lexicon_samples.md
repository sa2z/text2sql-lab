# Sample Lexicon Data

This file contains sample terminology and definitions that can be added to the lexicon table.

## AI/ML Terms

### Text2SQL
**Definition**: A technology that converts natural language queries into SQL statements using artificial intelligence.
**Category**: AI/ML
**Examples**: 
- User: "Show me all employees" → System: "SELECT * FROM employees"
- User: "What is the average salary?" → System: "SELECT AVG(salary) FROM employees"

### RAG (Retrieval-Augmented Generation)
**Definition**: A technique that combines information retrieval with text generation, allowing AI models to access external knowledge.
**Category**: AI/ML
**Examples**:
- System retrieves relevant documents before generating a response
- Enhances LLM responses with up-to-date or domain-specific information

### Embedding
**Definition**: A dense vector representation of text that captures semantic meaning, used for similarity search and machine learning.
**Category**: AI/ML
**Examples**:
- Converting "hello world" into [0.23, -0.45, 0.67, ...]
- Similar texts have similar embeddings

### Fine-tuning
**Definition**: The process of adapting a pre-trained model to a specific task or domain by training it on task-specific data.
**Category**: AI/ML
**Examples**:
- Adapting GPT for medical question answering
- Training a model on company-specific documentation

## Database Terms

### pgvector
**Definition**: PostgreSQL extension for efficient storage and similarity search of vector embeddings.
**Category**: Database
**Examples**:
- Store embeddings as vector(384) type
- Use cosine similarity for semantic search

### Indexing
**Definition**: Database optimization technique that creates data structures to speed up data retrieval operations.
**Category**: Database
**Examples**:
- CREATE INDEX idx_salary ON employees(salary)
- IVFFlat index for vector similarity search

### ACID
**Definition**: Atomicity, Consistency, Isolation, Durability - properties that guarantee database transaction reliability.
**Category**: Database
**Examples**:
- Bank transfer either completes fully or not at all
- Concurrent transactions don't interfere with each other

## Framework Terms

### LangChain
**Definition**: Framework for developing applications powered by language models, providing tools and abstractions for LLM integration.
**Category**: Framework
**Examples**:
- Building chatbots with memory
- Creating RAG systems
- Developing autonomous agents

### LangGraph
**Definition**: Library for building stateful, multi-actor applications with LLMs using graph-based workflows.
**Category**: Framework
**Examples**:
- Creating agent workflows with cycles
- Implementing conditional logic in agent behavior
- State management across multiple agent interactions

### ReAct
**Definition**: Reasoning and Acting - a prompting pattern where the model alternates between reasoning about what to do and taking actions.
**Category**: Framework
**Examples**:
- Thought: "I need to find sales data" → Action: Query database
- Thought: "Now I need to calculate average" → Action: Perform calculation

## Infrastructure Terms

### Ollama
**Definition**: Tool for running open-source large language models locally with easy installation and management.
**Category**: Infrastructure
**Examples**:
- Running Llama 2, Mistral, or CodeLlama on-premise
- Model management through CLI or API
- No external API calls required

### Docker Compose
**Definition**: Tool for defining and running multi-container Docker applications using YAML configuration.
**Category**: Infrastructure
**Examples**:
- Orchestrating database, LLM, and application containers
- Defining service dependencies and networking
- One-command deployment of entire stack

### Langfuse
**Definition**: Open-source LLM engineering platform for monitoring, debugging, and improving LLM applications.
**Category**: Observability
**Examples**:
- Tracking token usage and costs
- Monitoring response latency
- Analyzing prompt performance

## SQL Terms

### JOIN
**Definition**: SQL operation that combines rows from two or more tables based on a related column.
**Category**: SQL
**Examples**:
- INNER JOIN: Returns matching rows from both tables
- LEFT JOIN: Returns all rows from left table and matching rows from right

### Aggregate Function
**Definition**: SQL function that performs calculation on a set of values and returns a single value.
**Category**: SQL
**Examples**:
- SUM(), AVG(), COUNT(), MIN(), MAX()
- Used with GROUP BY for summarization

### Subquery
**Definition**: A query nested inside another query, used to perform operations in multiple steps.
**Category**: SQL
**Examples**:
- SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)
- Finding employees with above-average salaries

## Usage Instructions

To add these terms to your database:

```python
from src.utils.db_utils import DatabaseConnection
from src.utils.embedding_utils import EmbeddingGenerator

db = DatabaseConnection()
embedder = EmbeddingGenerator()

# Example: Add a term
term = "Vector Database"
definition = "A database optimized for storing and querying vector embeddings"
category = "Database"
examples = "pgvector, Pinecone, Weaviate, Milvus"

# Generate embedding
text = f"{term}: {definition}"
embedding = embedder.generate_embedding(text)

# Insert into database
query = """
INSERT INTO lexicon (term, definition, category, examples, embedding)
VALUES (%s, %s, %s, %s, %s)
"""
conn = db.get_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute(query, (term, definition, category, examples, embedding))
    conn.commit()
finally:
    conn.close()
```
