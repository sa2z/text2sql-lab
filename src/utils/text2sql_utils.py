"""
Text2SQL utilities for converting natural language to SQL queries
"""
import os
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class Text2SQLGenerator:
    """Generate SQL queries from natural language using LLM"""
    
    def __init__(self, llm_provider: str = "ollama", model_name: str = None):
        self.llm_provider = llm_provider
        self.model_name = model_name or os.getenv('OLLAMA_MODEL', 'llama2')
        
        if llm_provider == "ollama":
            from langchain_community.llms import Ollama
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            self.llm = Ollama(base_url=ollama_host, model=self.model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    
    def generate_sql(self, natural_query: str, schema_context: str, 
                     few_shot_examples: str = "") -> str:
        """
        Generate SQL query from natural language
        
        Args:
            natural_query: Natural language question
            schema_context: Database schema information
            few_shot_examples: Optional few-shot examples
        
        Returns:
            Generated SQL query
        """
        prompt = self._create_prompt(natural_query, schema_context, few_shot_examples)
        
        try:
            response = self.llm.invoke(prompt)
            sql_query = self._extract_sql(response)
            return sql_query
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def _create_prompt(self, natural_query: str, schema_context: str, 
                      few_shot_examples: str = "") -> str:
        """Create prompt for LLM"""
        prompt = f"""You are a SQL expert. Convert the following natural language query into a valid PostgreSQL SQL query.

{schema_context}

{few_shot_examples}

Rules:
1. Only generate the SQL query, no explanations
2. Use proper PostgreSQL syntax
3. Use appropriate JOINs when needed
4. Include WHERE clauses for filtering
5. Use aggregate functions when appropriate
6. Ensure the query is safe and doesn't modify data

Natural Language Query: {natural_query}

SQL Query:"""
        return prompt
    
    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```sql'):
            response = response[6:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        response = response.strip()
        
        # Remove any explanatory text before or after the query
        lines = response.split('\n')
        sql_lines = []
        in_query = False
        
        for line in lines:
            line_upper = line.strip().upper()
            if any(line_upper.startswith(keyword) for keyword in 
                   ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
                in_query = True
            
            if in_query:
                sql_lines.append(line)
                if line.strip().endswith(';'):
                    break
        
        if sql_lines:
            return '\n'.join(sql_lines)
        
        return response


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
    from .db_utils import DatabaseConnection, get_database_context
    import pandas as pd
    
    if not isinstance(db_connection, DatabaseConnection):
        db_connection = DatabaseConnection()
    
    start_time = time.time()
    result = {
        'natural_query': natural_query,
        'sql_query': None,
        'success': False,
        'results': None,
        'error': None,
        'execution_time_ms': 0,
        'row_count': 0
    }
    
    try:
        # Get schema context
        schema_context = get_database_context()
        
        # Generate SQL
        generator = Text2SQLGenerator()
        sql_query = generator.generate_sql(natural_query, schema_context)
        result['sql_query'] = sql_query
        
        # Execute SQL
        df = db_connection.execute_query_df(sql_query)
        result['results'] = df
        result['success'] = True
        result['row_count'] = len(df)
        
    except Exception as e:
        result['error'] = str(e)
    
    finally:
        result['execution_time_ms'] = int((time.time() - start_time) * 1000)
        
        # Log execution
        if log_execution:
            try:
                db_connection.log_query(
                    natural_query,
                    result['sql_query'],
                    result['success'],
                    result['execution_time_ms'],
                    result['row_count'],
                    result['error']
                )
            except Exception as log_error:
                print(f"Failed to log query: {log_error}")
    
    return result


def get_few_shot_examples() -> str:
    """Get few-shot examples for text2sql"""
    examples = """
Example 1:
Natural Language: Show me all employees in the Engineering department
SQL: SELECT e.* FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = 'Engineering';

Example 2:
Natural Language: What is the total sales amount by region?
SQL: SELECT region, SUM(total_amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC;

Example 3:
Natural Language: Find employees with salary greater than 6000000
SQL: SELECT * FROM employees WHERE salary > 6000000 ORDER BY salary DESC;

Example 4:
Natural Language: List all active projects with their department names
SQL: SELECT p.project_name, p.status, d.department_name FROM projects p JOIN departments d ON p.department_id = d.department_id WHERE p.status = 'Active';
"""
    return examples
