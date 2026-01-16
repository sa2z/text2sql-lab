"""
Example manager for Text2SQL Lab
Few-shot 예제를 관리하고 유사한 예제를 검색하여 Text2SQL 품질을 향상시킵니다.
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from src.utils.db_utils import DatabaseConnection


class ExampleManager:
    """Few-shot 예제 관리 클래스"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """필요한 테이블이 존재하는지 확인"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'query_examples'
        );
        """
        result = self.db.execute_query(query)
        
        if not result[0]['exists']:
            print("Warning: query_examples table does not exist. Run init_examples.sql to create it.")
    
    def add_example(
        self,
        natural_language_query: str,
        sql_query: str,
        query_category: Optional[str] = None,
        difficulty: Optional[str] = 'medium',
        tags: Optional[List[str]] = None
    ) -> int:
        """
        예제 추가
        
        Args:
            natural_language_query: 자연어 질의
            sql_query: 대응하는 SQL 쿼리
            query_category: 쿼리 카테고리 (aggregation, join, filter 등)
            difficulty: 난이도 (easy, medium, hard)
            tags: 태그 리스트
        
        Returns:
            생성된 예제 ID
        """
        query = """
        INSERT INTO query_examples (
            natural_language_query, sql_query, query_category, difficulty, tags
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (natural_language_query, sql_query, query_category, difficulty, tags or [])
                )
                result = cursor.fetchone()
                conn.commit()
                return result[0]
        finally:
            conn.close()
    
    def get_example(self, example_id: int) -> Optional[Dict[str, Any]]:
        """
        예제 조회
        
        Args:
            example_id: 예제 ID
        
        Returns:
            예제 딕셔너리 또는 None
        """
        query = """
        SELECT *
        FROM query_examples
        WHERE id = %s
        """
        
        result = self.db.execute_query(query, (example_id,))
        return result[0] if result else None
    
    def search_examples(
        self,
        query_text: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        예제 검색
        
        Args:
            query_text: 검색할 텍스트
            category: 카테고리 필터
            difficulty: 난이도 필터
            tags: 태그 필터
            limit: 최대 결과 수
        
        Returns:
            검색 결과 리스트
        """
        where_clauses = []
        params = []
        
        if query_text:
            where_clauses.append(
                "(LOWER(natural_language_query) LIKE LOWER(%s) OR LOWER(sql_query) LIKE LOWER(%s))"
            )
            params.extend([f"%{query_text}%", f"%{query_text}%"])
        
        if category:
            where_clauses.append("query_category = %s")
            params.append(category)
        
        if difficulty:
            where_clauses.append("difficulty = %s")
            params.append(difficulty)
        
        if tags:
            where_clauses.append("tags && %s")
            params.append(tags)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"
        
        query = f"""
        SELECT *
        FROM query_examples
        WHERE {where_clause}
        ORDER BY success_rate DESC, usage_count DESC
        LIMIT %s
        """
        params.append(limit)
        
        return self.db.execute_query(query, tuple(params))
    
    def find_similar_examples(
        self,
        natural_query: str,
        limit: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        유사한 예제 검색 (임베딩 기반)
        
        Args:
            natural_query: 사용자 질의
            limit: 최대 결과 수
            similarity_threshold: 최소 유사도 임계값
        
        Returns:
            (예제, 유사도) 튜플 리스트
        """
        # Check if embeddings exist
        check_query = """
        SELECT COUNT(*) as count
        FROM query_examples
        WHERE embedding IS NOT NULL
        """
        result = self.db.execute_query(check_query)
        
        if result[0]['count'] == 0:
            # No embeddings, fallback to keyword search
            print("Warning: No embeddings found. Using keyword search instead.")
            examples = self.search_examples(query_text=natural_query, limit=limit)
            return [(ex, 0.0) for ex in examples]
        
        # Generate embedding for the natural query
        try:
            from src.utils.embedding_utils import generate_embedding
            query_embedding = generate_embedding(natural_query)
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {str(e)}")
            examples = self.search_examples(query_text=natural_query, limit=limit)
            return [(ex, 0.0) for ex in examples]
        
        # Search using cosine similarity
        query = """
        SELECT *,
               1 - (embedding <=> %s::vector) as similarity
        FROM query_examples
        WHERE embedding IS NOT NULL
          AND 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        
        result = self.db.execute_query(
            query,
            (query_embedding, query_embedding, similarity_threshold, query_embedding, limit)
        )
        
        return [(ex, ex['similarity']) for ex in result]
    
    def update_example_stats(
        self,
        example_id: int,
        success: bool
    ):
        """
        예제 사용 통계 업데이트
        
        Args:
            example_id: 예제 ID
            success: 성공 여부
        """
        query = """
        UPDATE query_examples
        SET usage_count = usage_count + 1,
            success_rate = (
                (success_rate * usage_count + CASE WHEN %s THEN 1 ELSE 0 END) 
                / (usage_count + 1)
            )
        WHERE id = %s
        """
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (success, example_id))
                conn.commit()
        finally:
            conn.close()
    
    def get_top_examples(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        성공률이 높은 예제 조회
        
        Args:
            category: 카테고리 필터
            limit: 최대 결과 수
        
        Returns:
            예제 리스트
        """
        if category:
            query = """
            SELECT *
            FROM query_examples
            WHERE query_category = %s
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT %s
            """
            return self.db.execute_query(query, (category, limit))
        else:
            query = """
            SELECT *
            FROM query_examples
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT %s
            """
            return self.db.execute_query(query, (limit,))
    
    def delete_example(self, example_id: int) -> bool:
        """
        예제 삭제
        
        Args:
            example_id: 예제 ID
        
        Returns:
            성공 여부
        """
        query = "DELETE FROM query_examples WHERE id = %s"
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (example_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
    
    def add_bulk_examples(
        self,
        examples: List[Dict[str, Any]]
    ) -> int:
        """
        여러 예제를 한번에 추가
        
        Args:
            examples: 예제 딕셔너리 리스트
        
        Returns:
            추가된 예제 수
        """
        count = 0
        
        for example in examples:
            try:
                self.add_example(
                    natural_language_query=example['natural_language_query'],
                    sql_query=example['sql_query'],
                    query_category=example.get('query_category'),
                    difficulty=example.get('difficulty', 'medium'),
                    tags=example.get('tags')
                )
                count += 1
            except Exception as e:
                print(f"Warning: Failed to add example: {str(e)}")
        
        return count
    
    def generate_embeddings_for_all(self):
        """
        모든 예제에 대해 임베딩 생성
        """
        try:
            from src.utils.embedding_utils import generate_embedding
        except ImportError:
            print("Error: embedding_utils not available")
            return
        
        # Get all examples without embeddings
        query = """
        SELECT id, natural_language_query
        FROM query_examples
        WHERE embedding IS NULL
        """
        
        examples = self.db.execute_query(query)
        
        for example in examples:
            try:
                embedding = generate_embedding(example['natural_language_query'])
                
                update_query = """
                UPDATE query_examples
                SET embedding = %s::vector
                WHERE id = %s
                """
                
                conn = self.db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(update_query, (embedding, example['id']))
                        conn.commit()
                finally:
                    conn.close()
                
                print(f"Generated embedding for example {example['id']}")
                
            except Exception as e:
                print(f"Warning: Failed to generate embedding for example {example['id']}: {str(e)}")
    
    def get_categories(self) -> List[str]:
        """
        모든 카테고리 목록 조회
        
        Returns:
            카테고리 리스트
        """
        query = """
        SELECT DISTINCT query_category
        FROM query_examples
        WHERE query_category IS NOT NULL
        ORDER BY query_category
        """
        
        result = self.db.execute_query(query)
        return [row['query_category'] for row in result]
    
    def export_to_csv(self, file_path: str):
        """
        예제를 CSV 파일로 내보내기
        
        Args:
            file_path: CSV 파일 경로
        """
        query = """
        SELECT id, natural_language_query, sql_query, query_category, 
               difficulty, tags, success_rate, usage_count
        FROM query_examples
        ORDER BY id
        """
        
        df = self.db.execute_query_df(query)
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def import_from_csv(self, file_path: str) -> int:
        """
        CSV 파일에서 예제 가져오기
        
        Args:
            file_path: CSV 파일 경로
        
        Returns:
            가져온 예제 수
        """
        df = pd.read_csv(file_path, encoding='utf-8')
        
        required_columns = ['natural_language_query', 'sql_query']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        examples = []
        for _, row in df.iterrows():
            example = {
                'natural_language_query': row['natural_language_query'],
                'sql_query': row['sql_query'],
                'query_category': row.get('query_category') if pd.notna(row.get('query_category')) else None,
                'difficulty': row.get('difficulty') if pd.notna(row.get('difficulty')) else 'medium',
                'tags': eval(row['tags']) if pd.notna(row.get('tags')) else None
            }
            examples.append(example)
        
        return self.add_bulk_examples(examples)


def initialize_default_examples(db: DatabaseConnection) -> int:
    """
    기본 예제 초기화
    
    Args:
        db: 데이터베이스 연결
    
    Returns:
        추가된 예제 수
    """
    manager = ExampleManager(db)
    
    default_examples = [
        # 기본 SELECT 쿼리
        {
            'natural_language_query': '모든 직원을 보여주세요',
            'sql_query': 'SELECT * FROM employees;',
            'query_category': 'select',
            'difficulty': 'easy',
            'tags': ['basic', 'employees']
        },
        {
            'natural_language_query': '모든 부서를 보여주세요',
            'sql_query': 'SELECT * FROM departments;',
            'query_category': 'select',
            'difficulty': 'easy',
            'tags': ['basic', 'departments']
        },
        
        # 필터링
        {
            'natural_language_query': '급여가 6000000보다 큰 직원을 보여주세요',
            'sql_query': 'SELECT * FROM employees WHERE salary > 6000000;',
            'query_category': 'filter',
            'difficulty': 'easy',
            'tags': ['filter', 'employees', 'salary']
        },
        {
            'natural_language_query': '2020년 이후에 입사한 직원을 보여주세요',
            'sql_query': "SELECT * FROM employees WHERE hire_date > '2020-01-01';",
            'query_category': 'filter',
            'difficulty': 'easy',
            'tags': ['filter', 'employees', 'date']
        },
        
        # JOIN 쿼리
        {
            'natural_language_query': '직원 이름과 소속 부서명을 보여주세요',
            'sql_query': '''SELECT e.name, d.department_name 
                           FROM employees e 
                           JOIN departments d ON e.department_id = d.department_id;''',
            'query_category': 'join',
            'difficulty': 'medium',
            'tags': ['join', 'employees', 'departments']
        },
        
        # 집계 쿼리
        {
            'natural_language_query': '부서별 평균 급여를 계산해주세요',
            'sql_query': '''SELECT d.department_name, AVG(e.salary) as avg_salary
                           FROM employees e
                           JOIN departments d ON e.department_id = d.department_id
                           GROUP BY d.department_name;''',
            'query_category': 'aggregation',
            'difficulty': 'medium',
            'tags': ['aggregation', 'join', 'salary']
        },
        {
            'natural_language_query': '각 부서의 직원 수를 세어주세요',
            'sql_query': '''SELECT d.department_name, COUNT(*) as employee_count
                           FROM employees e
                           JOIN departments d ON e.department_id = d.department_id
                           GROUP BY d.department_name;''',
            'query_category': 'aggregation',
            'difficulty': 'medium',
            'tags': ['aggregation', 'count', 'departments']
        },
        
        # 정렬
        {
            'natural_language_query': '급여가 가장 높은 5명의 직원을 보여주세요',
            'sql_query': 'SELECT * FROM employees ORDER BY salary DESC LIMIT 5;',
            'query_category': 'sort',
            'difficulty': 'easy',
            'tags': ['sort', 'limit', 'salary']
        },
        
        # 복잡한 쿼리
        {
            'natural_language_query': '마케팅 부서의 총 급여는 얼마인가요?',
            'sql_query': '''SELECT SUM(e.salary) as total_salary
                           FROM employees e
                           JOIN departments d ON e.department_id = d.department_id
                           WHERE d.department_name = '마케팅팀';''',
            'query_category': 'aggregation',
            'difficulty': 'medium',
            'tags': ['aggregation', 'filter', 'join']
        },
        {
            'natural_language_query': '지역별 총 매출을 보여주세요',
            'sql_query': '''SELECT region, SUM(total_amount) as total_sales
                           FROM sales
                           GROUP BY region
                           ORDER BY total_sales DESC;''',
            'query_category': 'aggregation',
            'difficulty': 'medium',
            'tags': ['aggregation', 'sales', 'sort']
        },
    ]
    
    return manager.add_bulk_examples(default_examples)


if __name__ == "__main__":
    # Example usage
    db = DatabaseConnection()
    manager = ExampleManager(db)
    
    # Find similar examples
    query = "급여가 높은 직원들을 보여주세요"
    similar = manager.find_similar_examples(query, limit=3)
    
    print(f"Similar examples for: {query}")
    for example, similarity in similar:
        print(f"\nSimilarity: {similarity:.4f}")
        print(f"Query: {example['natural_language_query']}")
        print(f"SQL: {example['sql_query']}")
