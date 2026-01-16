"""
스키마 향상 유틸리티

데이터베이스 스키마에 대한 상세한 설명을 관리하여
LLM이 더 정확한 SQL을 생성할 수 있도록 지원하는 유틸리티
"""
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaEnhancer:
    """데이터베이스 스키마 설명 관리 클래스"""
    
    def __init__(self, db, lazy_load: bool = False):
        """
        Args:
            db: DatabaseConnection 인스턴스
            lazy_load: True면 초기 캐시 로드를 건너뜀 (필요시 수동으로 로드)
        """
        self.db = db
        self._table_cache = {}
        self._column_cache = {}
        if not lazy_load:
            self._load_cache()
    
    def _load_cache(self):
        """
        데이터베이스에서 스키마 설명을 캐시로 로드
        
        Note:
            대용량 데이터베이스의 경우 성능 영향을 고려하여
            필요한 테이블만 선택적으로 로드하거나 lazy_load=True 사용 권장
        """
        try:
            # 테이블 설명 캐시 로드
            table_query = """
            SELECT table_name, korean_name, description, business_purpose, 
                   related_tables, common_queries
            FROM table_descriptions
            """
            table_results = self.db.execute_query(table_query)
            
            for row in table_results:
                self._table_cache[row['table_name']] = {
                    'korean_name': row['korean_name'],
                    'description': row['description'],
                    'business_purpose': row['business_purpose'],
                    'related_tables': row['related_tables'] or [],
                    'common_queries': row['common_queries'] or []
                }
            
            # 컬럼 설명 캐시 로드
            column_query = """
            SELECT table_name, column_name, korean_name, description, 
                   business_meaning, example_values, data_type, constraints,
                   related_columns
            FROM column_descriptions
            """
            column_results = self.db.execute_query(column_query)
            
            for row in column_results:
                key = f"{row['table_name']}.{row['column_name']}"
                self._column_cache[key] = {
                    'korean_name': row['korean_name'],
                    'description': row['description'],
                    'business_meaning': row['business_meaning'],
                    'example_values': row['example_values'] or [],
                    'data_type': row['data_type'],
                    'constraints': row['constraints'],
                    'related_columns': row['related_columns'] or []
                }
            
            logger.info(f"스키마 캐시 로드 완료: {len(self._table_cache)} 테이블, {len(self._column_cache)} 컬럼")
        except Exception as e:
            logger.warning(f"스키마 캐시 로드 실패: {str(e)}")
            self._table_cache = {}
            self._column_cache = {}
    
    def reload_cache(self):
        """
        캐시를 수동으로 다시 로드
        
        Returns:
            성공 여부
        """
        try:
            self._load_cache()
            return True
        except Exception as e:
            logger.error(f"캐시 재로드 실패: {str(e)}")
            return False
    
    def add_column_description(self, table_name: str, column_name: str,
                              korean_name: str, description: str,
                              business_meaning: str,
                              example_values: Optional[List[str]] = None,
                              data_type: Optional[str] = None,
                              constraints: Optional[str] = None) -> bool:
        """
        컬럼 설명 추가 또는 업데이트
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
            korean_name: 한글 이름
            description: 컬럼 설명
            business_meaning: 비즈니스 의미
            example_values: 예시 값 리스트
            data_type: 데이터 타입
            constraints: 제약 조건
        
        Returns:
            성공 여부
        """
        try:
            query = """
            INSERT INTO column_descriptions 
                (table_name, column_name, korean_name, description, business_meaning,
                 example_values, data_type, constraints)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (table_name, column_name) 
            DO UPDATE SET
                korean_name = EXCLUDED.korean_name,
                description = EXCLUDED.description,
                business_meaning = EXCLUDED.business_meaning,
                example_values = EXCLUDED.example_values,
                data_type = EXCLUDED.data_type,
                constraints = EXCLUDED.constraints,
                updated_at = NOW()
            """
            
            self.db.execute_query(query, (
                table_name,
                column_name,
                korean_name,
                description,
                business_meaning,
                example_values or [],
                data_type,
                constraints
            ))
            
            # 캐시 점진적 업데이트
            key = f"{table_name}.{column_name}"
            self._column_cache[key] = {
                'korean_name': korean_name,
                'description': description,
                'business_meaning': business_meaning,
                'example_values': example_values or [],
                'data_type': data_type,
                'constraints': constraints,
                'related_columns': []
            }
            
            logger.info(f"컬럼 설명 추가 완료: {table_name}.{column_name}")
            return True
            
        except Exception as e:
            logger.error(f"컬럼 설명 추가 실패: {table_name}.{column_name}, 에러: {str(e)}")
            return False
    
    def add_table_description(self, table_name: str, korean_name: str,
                            description: str, business_purpose: str,
                            related_tables: Optional[List[str]] = None,
                            common_queries: Optional[List[str]] = None) -> bool:
        """
        테이블 설명 추가 또는 업데이트
        
        Args:
            table_name: 테이블 이름
            korean_name: 한글 이름
            description: 테이블 설명
            business_purpose: 비즈니스 목적
            related_tables: 연관 테이블 리스트
            common_queries: 자주 사용되는 쿼리 패턴 리스트
        
        Returns:
            성공 여부
        """
        try:
            query = """
            INSERT INTO table_descriptions 
                (table_name, korean_name, description, business_purpose,
                 related_tables, common_queries)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (table_name) 
            DO UPDATE SET
                korean_name = EXCLUDED.korean_name,
                description = EXCLUDED.description,
                business_purpose = EXCLUDED.business_purpose,
                related_tables = EXCLUDED.related_tables,
                common_queries = EXCLUDED.common_queries,
                updated_at = NOW()
            """
            
            self.db.execute_query(query, (
                table_name,
                korean_name,
                description,
                business_purpose,
                related_tables or [],
                common_queries or []
            ))
            
            # 캐시 점진적 업데이트
            self._table_cache[table_name] = {
                'korean_name': korean_name,
                'description': description,
                'business_purpose': business_purpose,
                'related_tables': related_tables or [],
                'common_queries': common_queries or []
            }
            
            logger.info(f"테이블 설명 추가 완료: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"테이블 설명 추가 실패: {table_name}, 에러: {str(e)}")
            return False
    
    def get_enhanced_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 테이블의 향상된 스키마 정보 조회
        
        Args:
            table_name: 테이블 이름
        
        Returns:
            테이블 정보와 컬럼 정보를 포함한 딕셔너리
        """
        try:
            # 테이블 정보
            table_info = self._table_cache.get(table_name)
            if not table_info:
                logger.warning(f"테이블 설명을 찾을 수 없음: {table_name}")
                return None
            
            # 컬럼 정보
            columns = []
            for key, col_info in self._column_cache.items():
                tbl, col = key.split('.')
                if tbl == table_name:
                    columns.append({
                        'column_name': col,
                        'korean_name': col_info['korean_name'],
                        'data_type': col_info['data_type'],
                        'description': col_info['description'],
                        'business_meaning': col_info['business_meaning'],
                        'example_values': col_info['example_values'],
                        'constraints': col_info['constraints'],
                        'related_columns': col_info['related_columns']
                    })
            
            # 컬럼명으로 정렬
            columns.sort(key=lambda x: x['column_name'])
            
            result = {
                'table_name': table_name,
                'korean_name': table_info['korean_name'],
                'description': table_info['description'],
                'business_purpose': table_info['business_purpose'],
                'related_tables': table_info['related_tables'],
                'common_queries': table_info['common_queries'],
                'columns': columns
            }
            
            return result
            
        except Exception as e:
            logger.error(f"스키마 조회 실패: {table_name}, 에러: {str(e)}")
            return None
    
    def get_all_schemas_with_descriptions(self) -> List[Dict[str, Any]]:
        """
        모든 테이블의 스키마 정보와 설명 조회
        
        Returns:
            모든 테이블의 향상된 스키마 정보 리스트
        """
        try:
            all_schemas = []
            
            for table_name in self._table_cache.keys():
                schema = self.get_enhanced_schema(table_name)
                if schema:
                    all_schemas.append(schema)
            
            logger.info(f"전체 스키마 조회 완료: {len(all_schemas)} 테이블")
            return all_schemas
            
        except Exception as e:
            logger.error(f"전체 스키마 조회 실패: {str(e)}")
            return []
    
    def get_column_description(self, table_name: str, column_name: str) -> Optional[Dict[str, Any]]:
        """
        특정 컬럼의 상세 설명 조회
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
        
        Returns:
            컬럼 설명 딕셔너리
        """
        key = f"{table_name}.{column_name}"
        col_info = self._column_cache.get(key)
        
        if col_info:
            return {
                'table_name': table_name,
                'column_name': column_name,
                **col_info
            }
        else:
            logger.warning(f"컬럼 설명을 찾을 수 없음: {table_name}.{column_name}")
            return None
    
    def search_columns_by_korean_name(self, korean_name: str) -> List[Dict[str, Any]]:
        """
        한글 이름으로 컬럼 검색
        
        Args:
            korean_name: 검색할 한글 이름 (부분 매칭)
        
        Returns:
            매칭되는 컬럼 정보 리스트
        """
        try:
            query = """
            SELECT table_name, column_name, korean_name, description, 
                   business_meaning, example_values, data_type
            FROM column_descriptions
            WHERE korean_name LIKE %s
            ORDER BY table_name, column_name
            """
            
            search_pattern = f"%{korean_name}%"
            results = self.db.execute_query(query, (search_pattern,))
            
            logger.info(f"한글 이름 검색 완료: '{korean_name}' → {len(results)} 결과")
            return results
            
        except Exception as e:
            logger.error(f"컬럼 검색 실패: {korean_name}, 에러: {str(e)}")
            return []
    
    def get_schema_for_llm(self, table_names: Optional[List[str]] = None) -> str:
        """
        LLM에게 제공할 포맷의 스키마 정보 생성
        
        Args:
            table_names: 포함할 테이블 리스트 (None이면 모든 테이블)
        
        Returns:
            LLM용 포맷의 스키마 정보 문자열
        """
        try:
            schemas = []
            
            if table_names:
                target_tables = table_names
            else:
                target_tables = list(self._table_cache.keys())
            
            for table_name in target_tables:
                schema = self.get_enhanced_schema(table_name)
                if not schema:
                    continue
                
                # 테이블 정보
                schema_text = f"\n### 테이블: {table_name} ({schema['korean_name']})\n"
                schema_text += f"설명: {schema['description']}\n"
                schema_text += f"목적: {schema['business_purpose']}\n"
                
                if schema['related_tables']:
                    schema_text += f"연관 테이블: {', '.join(schema['related_tables'])}\n"
                
                if schema['common_queries']:
                    schema_text += f"자주 사용되는 쿼리: {', '.join(schema['common_queries'])}\n"
                
                # 컬럼 정보
                schema_text += "\n컬럼:\n"
                for col in schema['columns']:
                    schema_text += f"  - {col['column_name']} ({col['korean_name']})\n"
                    schema_text += f"    타입: {col['data_type']}\n"
                    schema_text += f"    설명: {col['description']}\n"
                    schema_text += f"    의미: {col['business_meaning']}\n"
                    
                    if col['example_values']:
                        examples = ', '.join(col['example_values'][:3])
                        schema_text += f"    예시: {examples}\n"
                    
                    if col['constraints']:
                        schema_text += f"    제약: {col['constraints']}\n"
                
                schemas.append(schema_text)
            
            return '\n'.join(schemas)
            
        except Exception as e:
            logger.error(f"LLM용 스키마 생성 실패: {str(e)}")
            return ""
    
    def get_table_summary(self) -> List[Dict[str, Any]]:
        """
        모든 테이블의 요약 정보 조회
        
        Returns:
            테이블 요약 정보 리스트
        """
        try:
            query = """
            SELECT 
                td.table_name,
                td.korean_name,
                td.description,
                (SELECT COUNT(*) FROM column_descriptions cd 
                 WHERE cd.table_name = td.table_name) as column_count
            FROM table_descriptions td
            ORDER BY td.table_name
            """
            
            results = self.db.execute_query(query)
            logger.info(f"테이블 요약 조회 완료: {len(results)} 테이블")
            return results
            
        except Exception as e:
            logger.error(f"테이블 요약 조회 실패: {str(e)}")
            return []
    
    def find_related_tables(self, table_name: str) -> List[str]:
        """
        특정 테이블과 연관된 테이블 찾기
        
        Args:
            table_name: 테이블 이름
        
        Returns:
            연관 테이블 리스트
        """
        table_info = self._table_cache.get(table_name)
        if table_info:
            return table_info['related_tables']
        return []
    
    def get_common_queries(self, table_name: str) -> List[str]:
        """
        특정 테이블의 자주 사용되는 쿼리 패턴 조회
        
        Args:
            table_name: 테이블 이름
        
        Returns:
            자주 사용되는 쿼리 패턴 리스트
        """
        table_info = self._table_cache.get(table_name)
        if table_info:
            return table_info['common_queries']
        return []
    
    def export_schema_to_dict(self) -> Dict[str, Any]:
        """
        전체 스키마 정보를 딕셔너리로 내보내기
        
        Returns:
            전체 스키마 정보를 포함한 딕셔너리
        """
        return {
            'tables': self._table_cache.copy(),
            'columns': self._column_cache.copy()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        스키마 설명 통계 조회
        
        Returns:
            통계 정보 딕셔너리
        """
        try:
            query = """
            SELECT 
                (SELECT COUNT(*) FROM table_descriptions) as total_tables,
                (SELECT COUNT(*) FROM column_descriptions) as total_columns,
                (SELECT COUNT(DISTINCT table_name) FROM column_descriptions) as tables_with_columns,
                (SELECT AVG(array_length(example_values, 1)) 
                 FROM column_descriptions 
                 WHERE example_values IS NOT NULL) as avg_examples_per_column
            """
            
            result = self.db.execute_query(query)
            
            if result:
                stats = result[0]
                stats['cache_status'] = {
                    'tables_cached': len(self._table_cache),
                    'columns_cached': len(self._column_cache)
                }
                return stats
            return {}
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {str(e)}")
            return {}


# 사용 예제
if __name__ == '__main__':
    from db_utils import DatabaseConnection
    
    # 데이터베이스 연결
    db = DatabaseConnection()
    
    # SchemaEnhancer 초기화
    enhancer = SchemaEnhancer(db)
    
    # 예제 1: 특정 테이블의 향상된 스키마 조회
    print("\n=== 예제 1: employees 테이블 스키마 ===")
    schema = enhancer.get_enhanced_schema('employees')
    if schema:
        print(f"테이블: {schema['table_name']} ({schema['korean_name']})")
        print(f"설명: {schema['description']}")
        print(f"컬럼 수: {len(schema['columns'])}")
        print("\n주요 컬럼:")
        for col in schema['columns'][:3]:
            print(f"  - {col['column_name']} ({col['korean_name']}): {col['description']}")
    
    # 예제 2: 한글 이름으로 컬럼 검색
    print("\n=== 예제 2: '급여' 관련 컬럼 검색 ===")
    results = enhancer.search_columns_by_korean_name('급여')
    for result in results:
        print(f"{result['table_name']}.{result['column_name']} ({result['korean_name']})")
        print(f"  설명: {result['description']}")
    
    # 예제 3: LLM용 스키마 정보 생성
    print("\n=== 예제 3: LLM용 스키마 정보 (employees, departments만) ===")
    llm_schema = enhancer.get_schema_for_llm(['employees', 'departments'])
    print(llm_schema[:500] + "...")  # 처음 500자만 출력
    
    # 예제 4: 테이블 요약 정보
    print("\n=== 예제 4: 테이블 요약 ===")
    summary = enhancer.get_table_summary()
    for table in summary:
        print(f"{table['table_name']} ({table['korean_name']}): {table['column_count']} 컬럼")
    
    # 예제 5: 연관 테이블 찾기
    print("\n=== 예제 5: employees 테이블의 연관 테이블 ===")
    related = enhancer.find_related_tables('employees')
    print(f"연관 테이블: {', '.join(related)}")
    
    # 예제 6: 통계 정보
    print("\n=== 예제 6: 스키마 통계 ===")
    stats = enhancer.get_statistics()
    print(f"총 테이블: {stats.get('total_tables', 0)}")
    print(f"총 컬럼: {stats.get('total_columns', 0)}")
    print(f"컬럼당 평균 예시 값: {stats.get('avg_examples_per_column', 0):.1f}")
    
    # 예제 7: 새로운 컬럼 설명 추가 (주석 처리)
    # enhancer.add_column_description(
    #     table_name='employees',
    #     column_name='bonus',
    #     korean_name='보너스',
    #     description='직원의 성과급',
    #     business_meaning='연간 또는 분기별 성과에 따른 보너스',
    #     example_values=['1000000', '2000000', '5000000'],
    #     data_type='DECIMAL(10,2)',
    #     constraints='CHECK (bonus >= 0)'
    # )
    
    print("\nSchemaEnhancer 준비 완료")
