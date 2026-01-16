"""
Lexicon manager for Text2SQL Lab
도메인 특화 용어 사전 관리 및 용어 매핑 기능을 제공합니다.
"""
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from src.utils.db_utils import DatabaseConnection


class LexiconManager:
    """용어 사전 관리 클래스"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """필요한 테이블이 존재하는지 확인"""
        # Check if term_mappings table exists
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'term_mappings'
        );
        """
        result = self.db.execute_query(query)
        
        if not result[0]['exists']:
            print("Warning: term_mappings table does not exist. Run init_lexicon.sql to create it.")
    
    def add_term_mapping(
        self,
        business_term: str,
        technical_term: str,
        synonyms: Optional[List[str]] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> int:
        """
        용어 매핑 추가
        
        Args:
            business_term: 비즈니스 용어 (예: "매출")
            technical_term: 기술 용어 (예: "sales_amount")
            synonyms: 동의어 리스트 (예: ["판매액", "매출액"])
            description: 용어 설명
            category: 카테고리 (예: "finance", "hr")
        
        Returns:
            생성된 매핑 ID
        """
        query = """
        INSERT INTO term_mappings (
            business_term, technical_term, synonyms, description, category
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (business_term, technical_term, synonyms or [], description, category)
                )
                result = cursor.fetchone()
                conn.commit()
                return result[0]
        finally:
            conn.close()
    
    def get_technical_term(self, business_term: str) -> Optional[str]:
        """
        비즈니스 용어에 해당하는 기술 용어 조회
        
        Args:
            business_term: 비즈니스 용어
        
        Returns:
            기술 용어 또는 None
        """
        query = """
        SELECT technical_term
        FROM term_mappings
        WHERE LOWER(business_term) = LOWER(%s)
           OR %s = ANY(synonyms)
        LIMIT 1
        """
        
        result = self.db.execute_query(query, (business_term, business_term))
        
        if result:
            return result[0]['technical_term']
        return None
    
    def search_terms(
        self,
        search_text: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        용어 검색
        
        Args:
            search_text: 검색어
            category: 카테고리 필터
            limit: 최대 결과 수
        
        Returns:
            검색 결과 리스트
        """
        if category:
            query = """
            SELECT *
            FROM term_mappings
            WHERE (
                LOWER(business_term) LIKE LOWER(%s)
                OR LOWER(technical_term) LIKE LOWER(%s)
                OR LOWER(description) LIKE LOWER(%s)
            )
            AND category = %s
            ORDER BY business_term
            LIMIT %s
            """
            params = (
                f"%{search_text}%",
                f"%{search_text}%",
                f"%{search_text}%",
                category,
                limit
            )
        else:
            query = """
            SELECT *
            FROM term_mappings
            WHERE LOWER(business_term) LIKE LOWER(%s)
               OR LOWER(technical_term) LIKE LOWER(%s)
               OR LOWER(description) LIKE LOWER(%s)
            ORDER BY business_term
            LIMIT %s
            """
            params = (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", limit)
        
        return self.db.execute_query(query, params)
    
    def get_all_mappings(self, category: Optional[str] = None) -> pd.DataFrame:
        """
        모든 용어 매핑 조회
        
        Args:
            category: 카테고리 필터 (선택사항)
        
        Returns:
            용어 매핑 DataFrame
        """
        if category:
            query = """
            SELECT *
            FROM term_mappings
            WHERE category = %s
            ORDER BY business_term
            """
            return self.db.execute_query_df(query, (category,))
        else:
            query = """
            SELECT *
            FROM term_mappings
            ORDER BY business_term
            """
            return self.db.execute_query_df(query)
    
    def update_term_mapping(
        self,
        mapping_id: int,
        business_term: Optional[str] = None,
        technical_term: Optional[str] = None,
        synonyms: Optional[List[str]] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        용어 매핑 업데이트
        
        Args:
            mapping_id: 매핑 ID
            business_term: 새 비즈니스 용어 (선택사항)
            technical_term: 새 기술 용어 (선택사항)
            synonyms: 새 동의어 리스트 (선택사항)
            description: 새 설명 (선택사항)
            category: 새 카테고리 (선택사항)
        
        Returns:
            성공 여부
        """
        updates = []
        params = []
        
        if business_term is not None:
            updates.append("business_term = %s")
            params.append(business_term)
        
        if technical_term is not None:
            updates.append("technical_term = %s")
            params.append(technical_term)
        
        if synonyms is not None:
            updates.append("synonyms = %s")
            params.append(synonyms)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if category is not None:
            updates.append("category = %s")
            params.append(category)
        
        if not updates:
            return False
        
        query = f"""
        UPDATE term_mappings
        SET {', '.join(updates)}
        WHERE id = %s
        """
        params.append(mapping_id)
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_term_mapping(self, mapping_id: int) -> bool:
        """
        용어 매핑 삭제
        
        Args:
            mapping_id: 매핑 ID
        
        Returns:
            성공 여부
        """
        query = "DELETE FROM term_mappings WHERE id = %s"
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (mapping_id,))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
    
    def normalize_query(self, natural_query: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        자연어 질의에서 비즈니스 용어를 기술 용어로 변환
        
        Args:
            natural_query: 자연어 질의
        
        Returns:
            (정규화된 질의, 적용된 매핑 리스트) 튜플
        """
        normalized_query = natural_query
        applied_mappings = []
        
        # Get all term mappings
        mappings = self.get_all_mappings()
        
        # Sort by business term length (longest first) to avoid partial matches
        mappings = mappings.sort_values(
            by='business_term',
            key=lambda x: x.str.len(),
            ascending=False
        )
        
        for _, mapping in mappings.iterrows():
            business_term = mapping['business_term']
            technical_term = mapping['technical_term']
            synonyms = mapping['synonyms'] if mapping['synonyms'] else []
            
            # Check if business term or synonyms are in the query
            terms_to_check = [business_term] + synonyms
            
            for term in terms_to_check:
                if term.lower() in normalized_query.lower():
                    # Replace with technical term
                    import re
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    normalized_query = pattern.sub(technical_term, normalized_query)
                    
                    applied_mappings.append({
                        'original': term,
                        'replacement': technical_term,
                        'category': mapping['category']
                    })
        
        return normalized_query, applied_mappings
    
    def add_bulk_mappings(self, mappings: List[Dict[str, Any]]) -> int:
        """
        여러 용어 매핑을 한번에 추가
        
        Args:
            mappings: 매핑 딕셔너리 리스트
                     각 딕셔너리는 business_term, technical_term, synonyms, description, category 키를 가짐
        
        Returns:
            추가된 매핑 수
        """
        count = 0
        
        for mapping in mappings:
            try:
                self.add_term_mapping(
                    business_term=mapping['business_term'],
                    technical_term=mapping['technical_term'],
                    synonyms=mapping.get('synonyms'),
                    description=mapping.get('description'),
                    category=mapping.get('category')
                )
                count += 1
            except Exception as e:
                print(f"Warning: Failed to add mapping {mapping}: {str(e)}")
        
        return count
    
    def get_categories(self) -> List[str]:
        """
        모든 카테고리 목록 조회
        
        Returns:
            카테고리 리스트
        """
        query = """
        SELECT DISTINCT category
        FROM term_mappings
        WHERE category IS NOT NULL
        ORDER BY category
        """
        
        result = self.db.execute_query(query)
        return [row['category'] for row in result]
    
    def export_to_csv(self, file_path: str, category: Optional[str] = None):
        """
        용어 매핑을 CSV 파일로 내보내기
        
        Args:
            file_path: CSV 파일 경로
            category: 카테고리 필터 (선택사항)
        """
        df = self.get_all_mappings(category)
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def import_from_csv(self, file_path: str) -> int:
        """
        CSV 파일에서 용어 매핑 가져오기
        
        Args:
            file_path: CSV 파일 경로
        
        Returns:
            가져온 매핑 수
        """
        df = pd.read_csv(file_path, encoding='utf-8')
        
        required_columns = ['business_term', 'technical_term']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        mappings = []
        for _, row in df.iterrows():
            mapping = {
                'business_term': row['business_term'],
                'technical_term': row['technical_term'],
                'synonyms': eval(row['synonyms']) if pd.notna(row.get('synonyms')) else None,
                'description': row.get('description') if pd.notna(row.get('description')) else None,
                'category': row.get('category') if pd.notna(row.get('category')) else None
            }
            mappings.append(mapping)
        
        return self.add_bulk_mappings(mappings)


def initialize_default_lexicon(db: DatabaseConnection) -> int:
    """
    기본 용어 사전 초기화
    
    Args:
        db: 데이터베이스 연결
    
    Returns:
        추가된 매핑 수
    """
    manager = LexiconManager(db)
    
    default_mappings = [
        # HR/직원 관련
        {
            'business_term': '직원',
            'technical_term': 'employees',
            'synonyms': ['사원', '임직원', 'employee'],
            'description': '직원 테이블',
            'category': 'hr'
        },
        {
            'business_term': '급여',
            'technical_term': 'salary',
            'synonyms': ['연봉', '월급', 'wage', 'pay'],
            'description': '직원 급여',
            'category': 'hr'
        },
        {
            'business_term': '부서',
            'technical_term': 'department',
            'synonyms': ['부서명', 'dept'],
            'description': '부서 정보',
            'category': 'hr'
        },
        {
            'business_term': '입사일',
            'technical_term': 'hire_date',
            'synonyms': ['채용일', '입사날짜'],
            'description': '직원 입사일',
            'category': 'hr'
        },
        
        # 판매/영업 관련
        {
            'business_term': '매출',
            'technical_term': 'total_amount',
            'synonyms': ['판매액', '매출액', 'sales', 'revenue'],
            'description': '판매 금액',
            'category': 'sales'
        },
        {
            'business_term': '고객',
            'technical_term': 'customer',
            'synonyms': ['구매자', '클라이언트', 'client'],
            'description': '고객 정보',
            'category': 'sales'
        },
        {
            'business_term': '주문',
            'technical_term': 'order',
            'synonyms': ['구매', '오더'],
            'description': '주문 정보',
            'category': 'sales'
        },
        {
            'business_term': '지역',
            'technical_term': 'region',
            'synonyms': ['지방', '권역'],
            'description': '판매 지역',
            'category': 'sales'
        },
        
        # 프로젝트 관련
        {
            'business_term': '프로젝트',
            'technical_term': 'project',
            'synonyms': ['과제', 'PJ'],
            'description': '프로젝트 정보',
            'category': 'project'
        },
        {
            'business_term': '예산',
            'technical_term': 'budget',
            'synonyms': ['비용'],
            'description': '프로젝트 예산',
            'category': 'project'
        },
    ]
    
    return manager.add_bulk_mappings(default_mappings)


if __name__ == "__main__":
    # Example usage
    db = DatabaseConnection()
    manager = LexiconManager(db)
    
    # Normalize a query
    original_query = "매출이 가장 높은 직원 5명을 보여주세요"
    normalized, mappings = manager.normalize_query(original_query)
    
    print(f"Original: {original_query}")
    print(f"Normalized: {normalized}")
    print(f"Applied mappings: {mappings}")
