"""
Database connection and utility functions for text2sql-lab
"""
import os
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Handle PostgreSQL database connections"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.user = os.getenv('POSTGRES_USER', 'text2sql')
        self.password = os.getenv('POSTGRES_PASSWORD', 'text2sql123')
        self.database = os.getenv('POSTGRES_DB', 'text2sql_db')
        
        self.connection_string = (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
    
    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine"""
        return create_engine(self.connection_string)
    
    def get_connection(self):
        """Get psycopg2 connection"""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        finally:
            conn.close()
    
    def execute_query_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute a query and return results as pandas DataFrame"""
        engine = self.get_engine()
        return pd.read_sql(query, engine, params=params)
    
    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """Get schema information for a table"""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
        """
        return self.execute_query_df(query, (table_name,))
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """
        result = self.execute_query(query)
        return [row['table_name'] for row in result]
    
    def get_table_sample(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample rows from a table"""
        query = f"SELECT * FROM {table_name} LIMIT %s"
        return self.execute_query_df(query, (limit,))
    
    def log_query(self, natural_query: str, sql_query: str, 
                  success: bool, execution_time: int, 
                  result_count: int = 0, error_message: str = None):
        """Log query to query_history table"""
        query = """
        INSERT INTO query_history 
        (natural_language_query, generated_sql, execution_success, 
         execution_time_ms, result_count, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    natural_query, sql_query, success, 
                    execution_time, result_count, error_message
                ))
            conn.commit()
        finally:
            conn.close()


def get_database_context() -> str:
    """Get database schema context for LLM prompts"""
    db = DatabaseConnection()
    tables = db.get_all_tables()
    
    context = "Database Schema:\n\n"
    for table in tables:
        if table in ['query_history']:  # Skip internal tables
            continue
        schema = db.get_table_schema(table)
        context += f"Table: {table}\n"
        context += "Columns:\n"
        for _, row in schema.iterrows():
            context += f"  - {row['column_name']} ({row['data_type']})\n"
        context += "\n"
    
    return context
