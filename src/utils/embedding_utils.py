"""
Embedding generation and vector operations for text2sql-lab
"""
import os
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class EmbeddingGenerator:
    """Generate embeddings for text using sentence transformers"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv(
            'EMBEDDING_MODEL', 
            'sentence-transformers/all-MiniLM-L6-v2'
        )
        self.model = SentenceTransformer(self.model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def cosine_similarity(self, embedding1: List[float], 
                         embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def chunk_text(text: str, chunk_size: int = 1000, 
               overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to split
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence or word boundary
        if end < len(text):
            # Look for sentence boundary
            last_period = text[start:end].rfind('. ')
            if last_period > chunk_size * 0.5:  # If we found a period in the latter half
                end = start + last_period + 1
            else:
                # Look for word boundary
                last_space = text[start:end].rfind(' ')
                if last_space > chunk_size * 0.5:
                    end = start + last_space
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks


def store_document_with_embedding(db_connection, title: str, content: str, 
                                  doc_type: str, metadata: dict = None) -> int:
    """
    Store a document with its embedding in the database
    
    Args:
        db_connection: Database connection object
        title: Document title
        content: Document content
        doc_type: Type of document
        metadata: Additional metadata as dictionary
    
    Returns:
        Document ID
    """
    from .db_utils import DatabaseConnection
    import json
    
    if not isinstance(db_connection, DatabaseConnection):
        db_connection = DatabaseConnection()
    
    # Generate embedding
    embedder = EmbeddingGenerator()
    embedding = embedder.generate_embedding(content)
    
    # Insert document
    query = """
    INSERT INTO documents (title, content, document_type, metadata, embedding)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING document_id
    """
    
    conn = db_connection.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (
                title, content, doc_type, 
                json.dumps(metadata) if metadata else None,
                embedding
            ))
            doc_id = cursor.fetchone()[0]
        conn.commit()
        return doc_id
    finally:
        conn.close()


def search_similar_documents(db_connection, query_text: str, 
                             limit: int = 5) -> List[Tuple[int, str, str, float]]:
    """
    Search for similar documents using vector similarity
    
    Args:
        db_connection: Database connection object
        query_text: Text to search for
        limit: Maximum number of results
    
    Returns:
        List of tuples (document_id, title, content, similarity_score)
    """
    from .db_utils import DatabaseConnection
    
    if not isinstance(db_connection, DatabaseConnection):
        db_connection = DatabaseConnection()
    
    # Generate query embedding
    embedder = EmbeddingGenerator()
    query_embedding = embedder.generate_embedding(query_text)
    
    # Search using cosine similarity
    query = """
    SELECT 
        document_id,
        title,
        content,
        1 - (embedding <=> %s::vector) as similarity
    FROM documents
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT %s
    """
    
    result = db_connection.execute_query(query, (query_embedding, query_embedding, limit))
    return [(row['document_id'], row['title'], row['content'], row['similarity']) 
            for row in result]
