"""
렉시콘 관리자 유틸리티

도메인 특화 용어 사전을 관리하고 자연어 질의에서 용어를 매핑하는 유틸리티
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LexiconManager:
    """도메인 특화 용어 사전 관리 클래스"""
    
    def __init__(self, db):
        """
        Args:
            db: DatabaseConnection 인스턴스
        """
        self.db = db
        self._cache = {}  # 성능 향상을 위한 캐시
        self._load_cache()
    
    def _load_cache(self):
        """데이터베이스에서 용어 매핑을 캐시로 로드"""
        try:
            query = """
            SELECT business_term, technical_terms, synonyms, category
            FROM term_mappings
            """
            results = self.db.execute_query(query)
            
            for row in results:
                business_term = row['business_term'].lower()
                self._cache[business_term] = {
                    'technical_terms': row['technical_terms'],
                    'synonyms': row['synonyms'] or [],
                    'category': row['category']
                }
                
                # 동의어도 캐시에 추가
                if row['synonyms']:
                    for synonym in row['synonyms']:
                        synonym_lower = synonym.lower()
                        if synonym_lower not in self._cache:
                            self._cache[synonym_lower] = {
                                'technical_terms': row['technical_terms'],
                                'synonyms': [],
                                'category': row['category'],
                                'is_synonym': True,
                                'original_term': business_term
                            }
            
            logger.info(f"용어 캐시 로드 완료: {len(self._cache)} 항목")
        except Exception as e:
            logger.warning(f"용어 캐시 로드 실패: {str(e)}")
            self._cache = {}
    
    def add_term(self, business_term: str, technical_terms: List[str], 
                 synonyms: Optional[List[str]] = None, 
                 description: Optional[str] = None,
                 category: str = 'general') -> bool:
        """
        새로운 용어 추가
        
        Args:
            business_term: 비즈니스 용어 (예: "매출")
            technical_terms: 기술 용어 리스트 (예: ["sales_amount", "revenue"])
            synonyms: 동의어 리스트 (예: ["판매액", "수익"])
            description: 용어 설명
            category: 카테고리 (finance, hr, operations 등)
        
        Returns:
            성공 여부
        """
        try:
            # PostgreSQL 배열 문법으로 변환
            tech_terms_str = '{' + ','.join(f'"{t}"' for t in technical_terms) + '}'
            synonyms_str = '{' + ','.join(f'"{s}"' for s in (synonyms or [])) + '}' if synonyms else 'NULL'
            
            query = f"""
            INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category)
            VALUES (%s, %s, {synonyms_str if synonyms else 'NULL'}, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """
            
            self.db.execute_query(query, (
                business_term, 
                technical_terms,
                description,
                category
            ))
            
            # 캐시 업데이트
            self._load_cache()
            
            logger.info(f"용어 추가 완료: {business_term} → {technical_terms}")
            return True
            
        except Exception as e:
            logger.error(f"용어 추가 실패: {business_term}, 에러: {str(e)}")
            return False
    
    def get_technical_terms(self, business_term: str) -> Optional[List[str]]:
        """
        비즈니스 용어에 대응하는 기술 용어 조회
        
        Args:
            business_term: 비즈니스 용어
        
        Returns:
            기술 용어 리스트 또는 None
        """
        term_lower = business_term.lower().strip()
        
        if term_lower in self._cache:
            return self._cache[term_lower]['technical_terms']
        
        return None
    
    def find_term_in_query(self, query: str) -> List[Tuple[str, List[str]]]:
        """
        자연어 질의에서 매핑 가능한 용어 찾기
        
        Args:
            query: 자연어 질의
        
        Returns:
            (비즈니스_용어, 기술_용어_리스트) 튜플의 리스트
        """
        found_terms = []
        query_lower = query.lower()
        
        # 긴 용어부터 매칭 (예: "평균 급여"가 "급여"보다 먼저 매칭되도록)
        sorted_terms = sorted(self._cache.keys(), key=len, reverse=True)
        
        for term in sorted_terms:
            if term in query_lower:
                technical_terms = self._cache[term]['technical_terms']
                found_terms.append((term, technical_terms))
        
        return found_terms
    
    def map_terms(self, query: str, replace_mode: str = 'append') -> str:
        """
        자연어 질의에서 용어를 기술 용어로 매핑
        
        Args:
            query: 원본 자연어 질의
            replace_mode: 'replace' (치환) 또는 'append' (추가)
        
        Returns:
            매핑된 질의
        """
        mapped_query = query
        found_terms = self.find_term_in_query(query)
        
        if replace_mode == 'replace':
            # 비즈니스 용어를 기술 용어로 치환
            for business_term, technical_terms in found_terms:
                # 가장 대표적인 기술 용어 사용
                primary_tech_term = technical_terms[0] if technical_terms else business_term
                
                # 단어 경계를 고려한 치환 (부분 매칭 방지)
                pattern = r'\b' + re.escape(business_term) + r'\b'
                mapped_query = re.sub(pattern, primary_tech_term, mapped_query, flags=re.IGNORECASE)
        
        elif replace_mode == 'append':
            # 비즈니스 용어 뒤에 기술 용어 추가 (괄호 안에)
            for business_term, technical_terms in found_terms:
                tech_terms_str = ', '.join(technical_terms)
                pattern = r'\b' + re.escape(business_term) + r'\b'
                replacement = f"{business_term}({tech_terms_str})"
                mapped_query = re.sub(pattern, replacement, mapped_query, 
                                     flags=re.IGNORECASE, count=1)
        
        return mapped_query
    
    def detect_unknown_terms(self, query: str) -> List[str]:
        """
        질의에서 미등록된 용어 감지 (휴리스틱 기반)
        
        Args:
            query: 자연어 질의
        
        Returns:
            미등록 가능성이 있는 용어 리스트
        """
        # 간단한 휴리스틱: 한글 명사로 보이지만 매핑되지 않은 용어
        # 실제로는 더 정교한 NLP 분석이 필요
        
        # 한글 단어 추출 (2글자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', query)
        
        unknown_terms = []
        for word in korean_words:
            if word.lower() not in self._cache:
                # 일반적인 조사, 접속사 등은 제외
                common_particles = ['입니다', '있습니다', '보여주세요', '알려주세요', 
                                   '해주세요', '되나요', '인가요', '때문', '이다']
                if not any(word.endswith(p) for p in common_particles):
                    unknown_terms.append(word)
        
        return list(set(unknown_terms))  # 중복 제거
    
    def get_terms_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        특정 카테고리의 모든 용어 조회
        
        Args:
            category: 카테고리 이름
        
        Returns:
            용어 정보 딕셔너리 리스트
        """
        try:
            query = """
            SELECT business_term, technical_terms, synonyms, description
            FROM term_mappings
            WHERE category = %s
            ORDER BY business_term
            """
            results = self.db.execute_query(query, (category,))
            return results
        except Exception as e:
            logger.error(f"카테고리별 용어 조회 실패: {category}, 에러: {str(e)}")
            return []
    
    def get_all_categories(self) -> List[str]:
        """
        모든 카테고리 목록 조회
        
        Returns:
            카테고리 리스트
        """
        try:
            query = """
            SELECT DISTINCT category
            FROM term_mappings
            WHERE category IS NOT NULL
            ORDER BY category
            """
            results = self.db.execute_query(query)
            return [row['category'] for row in results]
        except Exception as e:
            logger.error(f"카테고리 조회 실패: {str(e)}")
            return []
    
    def search_terms(self, search_text: str) -> List[Dict[str, Any]]:
        """
        용어 검색 (비즈니스 용어, 동의어, 설명에서 검색)
        
        Args:
            search_text: 검색 텍스트
        
        Returns:
            검색 결과 리스트
        """
        try:
            query = """
            SELECT business_term, technical_terms, synonyms, description, category
            FROM term_mappings
            WHERE LOWER(business_term) LIKE %s
               OR LOWER(description) LIKE %s
               OR EXISTS (
                   SELECT 1 FROM unnest(synonyms) AS syn
                   WHERE LOWER(syn) LIKE %s
               )
            ORDER BY business_term
            """
            search_pattern = f"%{search_text.lower()}%"
            results = self.db.execute_query(query, (search_pattern, search_pattern, search_pattern))
            return results
        except Exception as e:
            logger.error(f"용어 검색 실패: {search_text}, 에러: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        용어 사전 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            query = """
            SELECT 
                COUNT(*) as total_terms,
                COUNT(DISTINCT category) as total_categories,
                AVG(array_length(technical_terms, 1)) as avg_technical_terms_per_business_term,
                AVG(array_length(synonyms, 1)) as avg_synonyms_per_term
            FROM term_mappings
            """
            result = self.db.execute_query(query)
            
            if result:
                return result[0]
            return {}
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {}
    
    def update_term(self, business_term: str, 
                   technical_terms: Optional[List[str]] = None,
                   synonyms: Optional[List[str]] = None,
                   description: Optional[str] = None,
                   category: Optional[str] = None) -> bool:
        """
        기존 용어 업데이트
        
        Args:
            business_term: 업데이트할 비즈니스 용어
            technical_terms: 새로운 기술 용어 리스트
            synonyms: 새로운 동의어 리스트
            description: 새로운 설명
            category: 새로운 카테고리
        
        Returns:
            성공 여부
        """
        try:
            update_parts = []
            params = []
            
            if technical_terms is not None:
                update_parts.append("technical_terms = %s")
                params.append(technical_terms)
            
            if synonyms is not None:
                update_parts.append("synonyms = %s")
                params.append(synonyms)
            
            if description is not None:
                update_parts.append("description = %s")
                params.append(description)
            
            if category is not None:
                update_parts.append("category = %s")
                params.append(category)
            
            if not update_parts:
                return False
            
            update_parts.append("updated_at = NOW()")
            params.append(business_term)
            
            query = f"""
            UPDATE term_mappings
            SET {', '.join(update_parts)}
            WHERE business_term = %s
            """
            
            self.db.execute_query(query, tuple(params))
            
            # 캐시 재로드
            self._load_cache()
            
            logger.info(f"용어 업데이트 완료: {business_term}")
            return True
            
        except Exception as e:
            logger.error(f"용어 업데이트 실패: {business_term}, 에러: {str(e)}")
            return False
    
    def delete_term(self, business_term: str) -> bool:
        """
        용어 삭제
        
        Args:
            business_term: 삭제할 비즈니스 용어
        
        Returns:
            성공 여부
        """
        try:
            query = "DELETE FROM term_mappings WHERE business_term = %s"
            self.db.execute_query(query, (business_term,))
            
            # 캐시 재로드
            self._load_cache()
            
            logger.info(f"용어 삭제 완료: {business_term}")
            return True
            
        except Exception as e:
            logger.error(f"용어 삭제 실패: {business_term}, 에러: {str(e)}")
            return False


# 사용 예제
if __name__ == '__main__':
    from db_utils import DatabaseConnection
    
    # 데이터베이스 연결
    db = DatabaseConnection()
    
    # LexiconManager 초기화
    lexicon = LexiconManager(db)
    
    # 용어 추가
    # lexicon.add_term(
    #     business_term="매출",
    #     technical_terms=["sales_amount", "revenue"],
    #     synonyms=["판매액", "수익"],
    #     description="제품이나 서비스 판매로 발생한 금액",
    #     category="finance"
    # )
    
    # 용어 매핑
    # query = "부서별 매출 합계를 보여줘"
    # mapped = lexicon.map_terms(query, replace_mode='append')
    # print(f"원본: {query}")
    # print(f"매핑: {mapped}")
    
    # 통계 조회
    # stats = lexicon.get_statistics()
    # print(f"통계: {stats}")
    
    print("LexiconManager 준비 완료")
