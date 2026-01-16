# Usage Examples

## Quick Start Examples

### 1. Connect to Database

```python
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()
tables = db.get_all_tables()
print(f"Found {len(tables)} tables")
```

### 2. Simple Text2SQL Query

```python
from src.utils.text2sql_utils import execute_text2sql
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()
result = execute_text2sql(db, "Show me all employees with salary greater than 6000000")

if result['success']:
    print(result['results'])
else:
    print(f"Error: {result['error']}")
```

### 3. Generate and Store Embeddings

```python
from src.utils.embedding_utils import EmbeddingGenerator, store_document_with_embedding
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()
embedder = EmbeddingGenerator()

# Add a new document
doc_id = store_document_with_embedding(
    db,
    title="My Document",
    content="This is the content of my document",
    doc_type="Guide",
    metadata={"author": "me"}
)
print(f"Document stored with ID: {doc_id}")
```

### 4. Semantic Search

```python
from src.utils.embedding_utils import search_similar_documents
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()
results = search_similar_documents(db, "How to use text2sql?", limit=3)

for doc_id, title, content, similarity in results:
    print(f"{title} (similarity: {similarity:.4f})")
```

### 5. Create Visualization

```python
from src.utils.viz_utils import create_bar_chart
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()
df = db.execute_query_df("SELECT region, SUM(total_amount) as total FROM sales GROUP BY region")

fig = create_bar_chart(df, 'region', 'total', title='Sales by Region')
fig.show()
```

## Advanced Examples

### Complete Pipeline with RAG

```python
from src.utils.db_utils import DatabaseConnection
from src.utils.text2sql_utils import execute_text2sql
from src.utils.embedding_utils import search_similar_documents
from src.utils.viz_utils import auto_visualize

db = DatabaseConnection()

# 1. Search for relevant context
query = "What are the total sales by region?"
docs = search_similar_documents(db, query, limit=2)
print(f"Found {len(docs)} relevant documents")

# 2. Execute text2sql
result = execute_text2sql(db, query)

# 3. Visualize results
if result['success']:
    viz = auto_visualize(result['results'])
    if hasattr(viz, 'show'):
        viz.show()
```

### Custom Agent with LangChain

```python
from langchain_community.llms import Ollama
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from src.utils.text2sql_utils import execute_text2sql
from src.utils.db_utils import DatabaseConnection
import os

db = DatabaseConnection()

# Create LLM
ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
llm = Ollama(base_url=ollama_host, model="llama2")

# Create tool
def query_database(query: str) -> str:
    result = execute_text2sql(db, query)
    if result['success']:
        return result['results'].to_string()
    return f"Error: {result['error']}"

tools = [
    Tool(
        name="QueryDatabase",
        func=query_database,
        description="Query the database using natural language"
    )
]

# Create agent
template = """Answer questions using the tools available.

Tools: {tools}
Tool Names: {tool_names}

Question: {input}
{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Use agent
response = agent_executor.invoke({
    "input": "How many employees are in the Engineering department?"
})
print(response['output'])
```

### Batch Processing Queries

```python
from src.utils.db_utils import DatabaseConnection
from src.utils.text2sql_utils import execute_text2sql
import pandas as pd

db = DatabaseConnection()

queries = [
    "What is the total sales by region?",
    "How many employees are in each department?",
    "What is the average salary by job title?",
    "Show me all active projects"
]

results = []
for query in queries:
    result = execute_text2sql(db, query)
    results.append({
        'query': query,
        'success': result['success'],
        'rows': result['row_count'] if result['success'] else 0,
        'time_ms': result['execution_time_ms']
    })

summary_df = pd.DataFrame(results)
print(summary_df)
```

### Custom Visualization Dashboard

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()

# Create subplots
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Sales by Region', 'Employees by Dept', 
                    'Top Projects', 'Salary Distribution')
)

# Chart 1: Sales
df1 = db.execute_query_df(
    "SELECT region, SUM(total_amount) as total FROM sales GROUP BY region"
)
fig.add_trace(
    go.Bar(x=df1['region'], y=df1['total'], name='Sales'),
    row=1, col=1
)

# Chart 2: Employees
df2 = db.execute_query_df(
    """SELECT d.department_name, COUNT(*) as count 
       FROM employees e 
       JOIN departments d ON e.department_id = d.department_id 
       GROUP BY d.department_name"""
)
fig.add_trace(
    go.Pie(labels=df2['department_name'], values=df2['count']),
    row=1, col=2
)

# Chart 3: Projects
df3 = db.execute_query_df(
    "SELECT project_name, budget FROM projects ORDER BY budget DESC LIMIT 5"
)
fig.add_trace(
    go.Bar(x=df3['project_name'], y=df3['budget'], name='Budget'),
    row=2, col=1
)

# Chart 4: Salaries
df4 = db.execute_query_df("SELECT salary FROM employees")
fig.add_trace(
    go.Histogram(x=df4['salary'], name='Salary'),
    row=2, col=2
)

fig.update_layout(height=800, showlegend=False, title_text="Analytics Dashboard")
fig.show()
```

### Monitoring Query Performance

```python
from src.utils.db_utils import DatabaseConnection
import pandas as pd
import matplotlib.pyplot as plt

db = DatabaseConnection()

# Get performance metrics
perf_query = """
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as query_count,
    AVG(execution_time_ms) as avg_time,
    SUM(CASE WHEN execution_success THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_rate
FROM query_history
GROUP BY hour
ORDER BY hour DESC
LIMIT 24
"""

df = db.execute_query_df(perf_query)

# Plot metrics
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(df['hour'], df['query_count'], marker='o')
ax1.set_title('Query Volume Over Time')
ax1.set_ylabel('Number of Queries')
ax1.grid(True)

ax2.plot(df['hour'], df['avg_time'], marker='o', color='orange')
ax2.set_title('Average Query Execution Time')
ax2.set_ylabel('Time (ms)')
ax2.grid(True)

plt.tight_layout()
plt.show()
```

## Common Patterns

### Error Handling

```python
from src.utils.text2sql_utils import execute_text2sql
from src.utils.db_utils import DatabaseConnection

db = DatabaseConnection()

def safe_query(natural_query: str, max_retries: int = 3):
    """Execute query with retries"""
    for attempt in range(max_retries):
        try:
            result = execute_text2sql(db, natural_query)
            if result['success']:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result['error']}")
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
    
    return None

result = safe_query("Show me all employees")
```

### Caching Results

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_text2sql(query: str):
    """Cache text2sql results"""
    result = execute_text2sql(db, query, log_execution=False)
    return result

# Use cached version
result1 = cached_text2sql("Show me all employees")
result2 = cached_text2sql("Show me all employees")  # Returns cached result
```

### Async Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def process_query(query):
    return execute_text2sql(db, query)

async def process_queries_async(queries):
    """Process multiple queries in parallel"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = [
            loop.run_in_executor(executor, process_query, query)
            for query in queries
        ]
        results = await asyncio.gather(*tasks)
    return results

# Use async processing
queries = [
    "Show me all employees",
    "What is the total sales?",
    "List all departments"
]
results = asyncio.run(process_queries_async(queries))
```
