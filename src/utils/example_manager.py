"""
Few-shot 예제 관리자 유틸리티

Text2SQL의 정확도를 향상시키기 위한 Few-shot 예제를 관리하는 유틸리티
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleManager:
    """Few-shot 예제 관리 클래스"""
    
    def __init__(self, db):
        """
        ExampleManager 초기화
        
        Args:
            db: DatabaseConnection 인스턴스
        """
        self.db = db
        logger.info("ExampleManager 초기화 완료")
    
    def add_example(self, natural_query: str, sql_query: str, category: str,
                   difficulty: str, tags: Optional[List[str]] = None,
                   description: Optional[str] = None) -> Optional[int]:
        """
        새로운 Few-shot 예제 추가
        
        Args:
            natural_query: 자연어 질의
            sql_query: 대응하는 SQL 쿼리
            category: 쿼리 카테고리 (예: basic_select, join, aggregation)
            difficulty: 난이도 (easy, medium, hard)
            tags: 태그 리스트 (예: ['select', 'where', 'join'])
            description: 예제 설명
        
        Returns:
            추가된 예제의 ID 또는 실패 시 None
        """
        try:
            query = """
            INSERT INTO query_examples 
                (natural_language_query, sql_query, query_category, difficulty, tags, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            result = self.db.execute_query(query, (
                natural_query,
                sql_query,
                category,
                difficulty,
                tags,
                description
            ))
            
            example_id = result[0]['id'] if result else None
            logger.info(f"예제 추가 완료: ID={example_id}, 카테고리={category}")
            return example_id
            
        except Exception as e:
            logger.error(f"예제 추가 실패: {str(e)}")
            return None
    
    def search_similar_examples(self, query: str, limit: int = 3,
                               embedding: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        유사한 예제 검색 (임베딩 기반 또는 키워드 기반)
        
        Args:
            query: 검색할 자연어 질의
            limit: 반환할 예제 수
            embedding: 쿼리의 임베딩 벡터 (None이면 키워드 검색으로 폴백)
        
        Returns:
            유사 예제 리스트 (각 예제는 딕셔너리)
        """
        try:
            if embedding is not None:
                # 임베딩 기반 유사도 검색
                # Validate embedding format
                if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
                    raise ValueError("Embedding must be a list of numbers")
                
                embedding_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'
                
                sql = """
                SELECT 
                    id,
                    natural_language_query,
                    sql_query,
                    query_category,
                    difficulty,
                    success_rate,
                    usage_count,
                    tags,
                    description,
                    1 - (embedding <=> %s::vector) as similarity
                FROM query_examples
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """
                
                results = self.db.execute_query(sql, (embedding_str, embedding_str, limit))
                logger.info(f"임베딩 기반 유사 예제 검색: {len(results)}개 발견")
                
            else:
                # 키워드 기반 폴백 검색
                logger.warning("임베딩이 제공되지 않아 키워드 검색으로 폴백")
                results = self._keyword_search(query, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"유사 예제 검색 실패: {str(e)}")
            # 에러 발생 시 키워드 검색으로 폴백
            logger.info("키워드 검색으로 폴백 시도")
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """
        키워드 기반 예제 검색 (폴백 메서드)
        
        Args:
            query: 검색할 자연어 질의
            limit: 반환할 예제 수
        
        Returns:
            매칭된 예제 리스트
        """
        try:
            # 한글/영문 단어 추출
            keywords = re.findall(r'[가-힣a-zA-Z]+', query.lower())
            
            if not keywords:
                # 키워드가 없으면 최근 성공률이 높은 예제 반환
                return self.get_best_examples(limit)
            
            # ILIKE를 사용한 부분 매칭 검색
            conditions = []
            params = []
            for keyword in keywords[:5]:  # 최대 5개 키워드만 사용
                conditions.append("LOWER(natural_language_query) LIKE %s")
                params.append(f"%{keyword}%")
            
            where_clause = " OR ".join(conditions)
            params.append(limit)
            
            sql = f"""
            SELECT 
                id,
                natural_language_query,
                sql_query,
                query_category,
                difficulty,
                success_rate,
                usage_count,
                tags,
                description
            FROM query_examples
            WHERE {where_clause}
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT %s
            """
            
            results = self.db.execute_query(sql, tuple(params))
            logger.info(f"키워드 기반 검색: {len(results)}개 발견")
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {str(e)}")
            return []
    
    def get_examples_by_category(self, category: str, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        카테고리별 예제 조회
        
        Args:
            category: 쿼리 카테고리 (예: basic_select, join, aggregation)
            limit: 반환할 예제 수 (None이면 전체)
        
        Returns:
            해당 카테고리의 예제 리스트
        """
        try:
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            sql = f"""
            SELECT 
                id,
                natural_language_query,
                sql_query,
                query_category,
                difficulty,
                success_rate,
                usage_count,
                tags,
                description,
                created_at,
                updated_at
            FROM query_examples
            WHERE query_category = %s
            ORDER BY success_rate DESC, usage_count DESC
            {limit_clause}
            """
            
            results = self.db.execute_query(sql, (category,))
            logger.info(f"카테고리 '{category}' 예제 조회: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"카테고리별 예제 조회 실패: {str(e)}")
            return []
    
    def get_examples_by_difficulty(self, difficulty: str,
                                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        난이도별 예제 조회
        
        Args:
            difficulty: 난이도 (easy, medium, hard)
            limit: 반환할 예제 수 (None이면 전체)
        
        Returns:
            해당 난이도의 예제 리스트
        """
        try:
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            sql = f"""
            SELECT 
                id,
                natural_language_query,
                sql_query,
                query_category,
                difficulty,
                success_rate,
                usage_count,
                tags,
                description,
                created_at,
                updated_at
            FROM query_examples
            WHERE difficulty = %s
            ORDER BY success_rate DESC, usage_count DESC
            {limit_clause}
            """
            
            results = self.db.execute_query(sql, (difficulty,))
            logger.info(f"난이도 '{difficulty}' 예제 조회: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"난이도별 예제 조회 실패: {str(e)}")
            return []
    
    def update_example_success(self, example_id: int, was_successful: bool) -> bool:
        """
        예제 실행 후 성공률 업데이트
        
        Args:
            example_id: 예제 ID
            was_successful: 실행 성공 여부
        
        Returns:
            업데이트 성공 여부
        """
        try:
            sql = """
            UPDATE query_examples
            SET 
                usage_count = usage_count + 1,
                success_rate = CASE 
                    WHEN %s THEN 
                        (success_rate * usage_count + 1.0) / (usage_count + 1)
                    ELSE 
                        (success_rate * usage_count) / (usage_count + 1)
                END,
                updated_at = NOW()
            WHERE id = %s
            """
            
            self.db.execute_query(sql, (was_successful, example_id))
            
            status = "성공" if was_successful else "실패"
            logger.info(f"예제 ID={example_id} 성공률 업데이트: {status}")
            return True
            
        except Exception as e:
            logger.error(f"성공률 업데이트 실패: {str(e)}")
            return False
    
    def get_statistics(self) -> List[Dict[str, Any]]:
        """
        카테고리별 예제 통계 조회
        
        Returns:
            각 카테고리의 통계 정보 (예제 수, 평균 성공률, 평균 사용 횟수)
        """
        try:
            sql = """
            SELECT 
                query_category as category,
                COUNT(*) as example_count,
                ROUND(AVG(success_rate)::numeric, 3) as avg_success_rate,
                ROUND(AVG(usage_count)::numeric, 2) as avg_usage_count,
                MIN(difficulty) as min_difficulty,
                MAX(difficulty) as max_difficulty
            FROM query_examples
            GROUP BY query_category
            ORDER BY example_count DESC
            """
            
            results = self.db.execute_query(sql)
            logger.info(f"예제 통계 조회: {len(results)}개 카테고리")
            return results
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return []
    
    def get_best_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        성공률이 높은 상위 예제 조회
        
        Args:
            limit: 반환할 예제 수
        
        Returns:
            성공률 상위 예제 리스트
        """
        try:
            sql = """
            SELECT 
                id,
                natural_language_query,
                sql_query,
                query_category,
                difficulty,
                success_rate,
                usage_count,
                tags,
                description
            FROM query_examples
            WHERE usage_count > 0
            ORDER BY success_rate DESC, usage_count DESC
            LIMIT %s
            """
            
            results = self.db.execute_query(sql, (limit,))
            logger.info(f"상위 예제 조회: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"상위 예제 조회 실패: {str(e)}")
            return []
    
    def delete_example(self, example_id: int) -> bool:
        """
        예제 삭제
        
        Args:
            example_id: 삭제할 예제 ID
        
        Returns:
            삭제 성공 여부
        """
        try:
            sql = "DELETE FROM query_examples WHERE id = %s"
            self.db.execute_query(sql, (example_id,))
            logger.info(f"예제 ID={example_id} 삭제 완료")
            return True
            
        except Exception as e:
            logger.error(f"예제 삭제 실패: {str(e)}")
            return False
    
    def format_examples_for_prompt(self, examples: List[Dict[str, Any]], 
                                   include_description: bool = True) -> str:
        """
        프롬프트에 사용할 예제 포맷팅
        
        Args:
            examples: 예제 리스트
            include_description: 설명 포함 여부
        
        Returns:
            포맷팅된 예제 문자열
        """
        if not examples:
            return ""
        
        formatted = []
        for i, ex in enumerate(examples, 1):
            example_text = f"\n예제 {i}:\n"
            example_text += f"질문: {ex['natural_language_query']}\n"
            example_text += f"SQL: {ex['sql_query']}\n"
            
            if include_description and ex.get('description'):
                example_text += f"설명: {ex['description']}\n"
            
            formatted.append(example_text)
        
        return "\n".join(formatted)
    
    def get_example_by_id(self, example_id: int) -> Optional[Dict[str, Any]]:
        """
        ID로 특정 예제 조회
        
        Args:
            example_id: 예제 ID
        
        Returns:
            예제 정보 또는 None
        """
        try:
            sql = """
            SELECT 
                id,
                natural_language_query,
                sql_query,
                query_category,
                difficulty,
                success_rate,
                usage_count,
                tags,
                description,
                created_at,
                updated_at
            FROM query_examples
            WHERE id = %s
            """
            
            results = self.db.execute_query(sql, (example_id,))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"예제 조회 실패: {str(e)}")
            return None
    
    def update_example_embedding(self, example_id: int, 
                                embedding: List[float]) -> bool:
        """
        예제의 임베딩 업데이트
        
        Args:
            example_id: 예제 ID
            embedding: 임베딩 벡터
        
        Returns:
            업데이트 성공 여부
        """
        try:
            # Validate embedding format
            if not isinstance(embedding, list) or not all(isinstance(x, (int, float)) for x in embedding):
                raise ValueError("Embedding must be a list of numbers")
            
            embedding_str = '[' + ','.join(str(float(x)) for x in embedding) + ']'
            
            sql = """
            UPDATE query_examples
            SET embedding = %s::vector, updated_at = NOW()
            WHERE id = %s
            """
            
            self.db.execute_query(sql, (embedding_str, example_id))
            logger.info(f"예제 ID={example_id} 임베딩 업데이트 완료")
            return True
            
        except Exception as e:
            logger.error(f"임베딩 업데이트 실패: {str(e)}")
            return False


if __name__ == "__main__":
    """사용 예제"""
    from db_utils import DatabaseConnection
    from embedding_utils import EmbeddingGenerator
    
    # 데이터베이스 연결
    db = DatabaseConnection()
    
    # ExampleManager 초기화
    manager = ExampleManager(db)
    
    print("=" * 60)
    print("ExampleManager 사용 예제")
    print("=" * 60)
    
    # 1. 새로운 예제 추가
    print("\n1. 새로운 예제 추가:")
    example_id = manager.add_example(
        natural_query="IT부서 직원들의 평균 급여는?",
        sql_query="SELECT AVG(e.salary) FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = 'IT부'",
        category="aggregation",
        difficulty="medium",
        tags=["avg", "join", "where"],
        description="특정 부서 평균 급여 조회"
    )
    print(f"추가된 예제 ID: {example_id}")
    
    # 2. 카테고리별 예제 조회
    print("\n2. 카테고리별 예제 조회 (aggregation):")
    agg_examples = manager.get_examples_by_category("aggregation", limit=3)
    for ex in agg_examples:
        print(f"  - {ex['natural_language_query'][:50]}... (성공률: {ex['success_rate']:.2f})")
    
    # 3. 난이도별 예제 조회
    print("\n3. 난이도별 예제 조회 (easy):")
    easy_examples = manager.get_examples_by_difficulty("easy", limit=3)
    for ex in easy_examples:
        print(f"  - {ex['natural_language_query'][:50]}...")
    
    # 4. 통계 조회
    print("\n4. 카테고리별 통계:")
    stats = manager.get_statistics()
    for stat in stats:
        print(f"  - {stat['category']}: {stat['example_count']}개, "
              f"평균 성공률: {stat['avg_success_rate']:.3f}, "
              f"평균 사용: {stat['avg_usage_count']:.2f}회")
    
    # 5. 상위 예제 조회
    print("\n5. 성공률 상위 예제:")
    best = manager.get_best_examples(limit=3)
    for ex in best:
        print(f"  - {ex['natural_language_query'][:50]}... "
              f"(성공률: {ex['success_rate']:.2f}, 사용: {ex['usage_count']}회)")
    
    # 6. 임베딩 기반 유사 예제 검색
    print("\n6. 유사 예제 검색 (임베딩 사용):")
    try:
        embed_gen = EmbeddingGenerator()
        query = "부서별로 직원들의 평균 월급을 알려줘"
        query_embedding = embed_gen.generate_embedding(query)
        
        similar = manager.search_similar_examples(query, limit=3, embedding=query_embedding)
        for ex in similar:
            similarity = ex.get('similarity', 0)
            print(f"  - {ex['natural_language_query'][:50]}... "
                  f"(유사도: {similarity:.3f})")
    except Exception as e:
        print(f"  임베딩 검색 실패: {str(e)}")
        print("  키워드 기반 검색으로 폴백:")
        similar = manager.search_similar_examples(query, limit=3)
        for ex in similar:
            print(f"  - {ex['natural_language_query'][:50]}...")
    
    # 7. 성공률 업데이트
    if example_id:
        print(f"\n7. 예제 ID={example_id} 성공률 업데이트:")
        manager.update_example_success(example_id, was_successful=True)
        updated = manager.get_example_by_id(example_id)
        if updated:
            print(f"  업데이트된 성공률: {updated['success_rate']:.3f}, "
                  f"사용 횟수: {updated['usage_count']}")
    
    # 8. 프롬프트용 포맷팅
    print("\n8. 프롬프트용 예제 포맷팅:")
    if agg_examples:
        formatted = manager.format_examples_for_prompt(agg_examples[:2])
        print(formatted)
    
    print("\n" + "=" * 60)
    print("ExampleManager 테스트 완료")
    print("=" * 60)
