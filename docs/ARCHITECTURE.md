# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                         │
│            (JupyterLab / Open-WebUI / Custom Apps)            │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐           ┌─────▼─────┐
    │ LangChain│           │  Ollama   │
    │   Agent  │◄──────────┤    LLM    │
    └────┬────┘           └───────────┘
         │
    ┌────▼──────────────────────────────┐
    │      Text2SQL + RAG Pipeline      │
    │  ┌──────┐  ┌──────┐  ┌─────────┐ │
    │  │Embed │  │Query │  │Generate │ │
    │  │ding  │─►│ RAG  │─►│  SQL    │ │
    │  └──────┘  └──────┘  └─────────┘ │
    └────┬──────────────────────────────┘
         │
    ┌────▼────────────┐
    │   PostgreSQL    │
    │   + pgvector    │
    │  ┌──────────┐   │
    │  │  Vector  │   │
    │  │  Store   │   │
    │  └──────────┘   │
    │  ┌──────────┐   │
    │  │Business  │   │
    │  │  Data    │   │
    │  └──────────┘   │
    └─────────────────┘
         │
    ┌────▼────────┐
    │  Langfuse   │
    │ Monitoring  │
    └─────────────┘
```

## Component Descriptions

### 1. User Interface Layer
- **JupyterLab**: Interactive notebooks for experimentation and learning
- **Open-WebUI**: Web interface for Ollama model management
- **Custom Apps**: Any application using the provided utilities

### 2. LLM Layer
- **Ollama**: Local LLM execution (Llama 2, Mistral, etc.)
- **vLLM** (optional): High-performance LLM inference
- Supports GPU acceleration for faster inference

### 3. Application Layer

#### Text2SQL Pipeline
1. **Input Processing**: Receives natural language query
2. **Schema Retrieval**: Gets relevant database schema
3. **Few-Shot Examples**: Loads example queries
4. **SQL Generation**: Uses LLM to generate SQL
5. **Validation**: Checks SQL safety
6. **Execution**: Runs query against database
7. **Result Formatting**: Prepares results for visualization

#### RAG Pipeline
1. **Document Chunking**: Splits documents into chunks
2. **Embedding Generation**: Creates vector embeddings
3. **Vector Storage**: Stores in pgvector
4. **Similarity Search**: Finds relevant documents
5. **Context Augmentation**: Adds context to prompts

#### Agent Workflow (LangChain/LangGraph)
1. **Tool Definition**: Define available tools
2. **Agent Creation**: Create ReAct or other agent types
3. **State Management**: Maintain conversation state
4. **Execution**: Agent decides which tools to use
5. **Response Generation**: Formulate final answer

### 4. Data Layer

#### PostgreSQL + pgvector
- **Business Tables**: employees, departments, sales, etc.
- **RAG Tables**: documents, lexicon with embeddings
- **Monitoring Tables**: query_history
- **Vector Indexes**: For fast similarity search

### 5. Observability Layer

#### Langfuse
- **Trace**: Complete request lifecycle
- **Generations**: LLM calls and outputs
- **Observations**: Tool usage and results
- **Metrics**: Latency, cost, success rate

## Data Flow

### 1. Simple Text2SQL Flow
```
User Query → LLM (with schema) → SQL → Database → Results → Visualization
```

### 2. RAG-Enhanced Text2SQL Flow
```
User Query → Embedding → Vector Search → Relevant Docs → 
→ LLM (with schema + docs) → SQL → Database → Results → Visualization
```

### 3. Agent-Based Flow
```
User Query → Agent → [
  Tool 1: Search Docs
  Tool 2: Get Schema
  Tool 3: Execute Text2SQL
  Tool 4: Visualize
] → Final Answer
```

## Technology Stack

### Core Technologies
- **Python 3.11**: Main programming language
- **PostgreSQL 16**: Relational database
- **pgvector**: Vector similarity search extension
- **Docker Compose**: Container orchestration

### AI/ML Stack
- **LangChain**: LLM application framework
- **LangGraph**: Stateful agent workflows
- **Sentence Transformers**: Text embeddings
- **Ollama**: Local LLM runtime

### Data & Visualization
- **pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **Matplotlib/Seaborn**: Static visualizations
- **SQLAlchemy**: Database ORM

### Monitoring & Observability
- **Langfuse**: LLM observability platform
- **PostgreSQL logs**: Query logging
- **Custom metrics**: Performance tracking

## Scalability Considerations

### Horizontal Scaling
- Multiple Jupyter containers for concurrent users
- PostgreSQL read replicas for query load
- Load balancer for Ollama instances

### Vertical Scaling
- GPU allocation for Ollama/vLLM
- Database memory tuning
- Connection pooling

### Performance Optimization
- Vector index tuning (IVFFlat parameters)
- Query result caching
- Batch embedding generation
- Async query execution

## Security Considerations

### SQL Injection Prevention
- Parameterized queries only
- SQL validation before execution
- Whitelist-based table access

### Data Access Control
- Database user permissions
- Query result filtering
- Rate limiting on API calls

### Model Safety
- Local model execution (no data leakage)
- Prompt injection protection
- Output validation

## Future Enhancements

1. **Multi-tenant Support**: Separate data per user/org
2. **Query Caching**: Cache frequent queries
3. **Real-time Updates**: WebSocket for live results
4. **Advanced Agents**: Self-improving agents
5. **Custom Models**: Fine-tuned models for specific domains
6. **API Gateway**: RESTful API for external access
7. **Streaming**: Stream LLM responses
8. **Feedback Loop**: Learn from user corrections
