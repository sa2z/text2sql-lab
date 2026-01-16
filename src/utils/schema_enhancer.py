"""
Schema enhancer for Text2SQL Lab
데이터베이스 스키마에 비즈니스 의미와 설명을 추가하여 Text2SQL 품질을 향상시킵니다.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from src.utils.db_utils import DatabaseConnection


class SchemaEnhancer:
    """스키마 설명 관리 클래스"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """필요한 테이블이 존재하는지 확인"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'column_descriptions'
        );
        """
        result = self.db.execute_query(query)
        
        if not result[0]['exists']:
            print("Warning: column_descriptions table does not exist. Run init_lexicon.sql to create it.")
    
    def add_column_description(
        self,
        table_name: str,
        column_name: str,
        description: str,
        business_meaning: Optional[str] = None,
        example_values: Optional[List[str]] = None,
        data_type: Optional[str] = None,
        constraints: Optional[str] = None
    ) -> bool:
        """
        컬럼 설명 추가 또는 업데이트
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
            description: 컬럼 설명
            business_meaning: 비즈니스 의미
            example_values: 예시 값 리스트
            data_type: 데이터 타입
            constraints: 제약 조건
        
        Returns:
            성공 여부
        """
        query = """
        INSERT INTO column_descriptions (
            table_name, column_name, description, business_meaning,
            example_values, data_type, constraints
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (table_name, column_name)
        DO UPDATE SET
            description = EXCLUDED.description,
            business_meaning = EXCLUDED.business_meaning,
            example_values = EXCLUDED.example_values,
            data_type = EXCLUDED.data_type,
            constraints = EXCLUDED.constraints,
            updated_at = NOW()
        """
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (table_name, column_name, description, business_meaning,
                     example_values, data_type, constraints)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding column description: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_column_description(
        self,
        table_name: str,
        column_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        컬럼 설명 조회
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
        
        Returns:
            컬럼 설명 딕셔너리 또는 None
        """
        query = """
        SELECT *
        FROM column_descriptions
        WHERE table_name = %s AND column_name = %s
        """
        
        result = self.db.execute_query(query, (table_name, column_name))
        return result[0] if result else None
    
    def get_table_descriptions(self, table_name: str) -> pd.DataFrame:
        """
        테이블의 모든 컬럼 설명 조회
        
        Args:
            table_name: 테이블 이름
        
        Returns:
            컬럼 설명 DataFrame
        """
        query = """
        SELECT *
        FROM column_descriptions
        WHERE table_name = %s
        ORDER BY column_name
        """
        
        return self.db.execute_query_df(query, (table_name,))
    
    def get_enhanced_schema(
        self,
        table_name: Optional[str] = None
    ) -> str:
        """
        향상된 스키마 정보 생성 (Text2SQL 프롬프트용)
        
        Args:
            table_name: 특정 테이블 (None이면 모든 테이블)
        
        Returns:
            향상된 스키마 설명 문자열
        """
        if table_name:
            tables = [table_name]
        else:
            tables = self.db.get_all_tables()
        
        schema_text = "# Enhanced Database Schema\n\n"
        
        for table in tables:
            # Get basic schema
            basic_schema = self.db.get_table_schema(table)
            
            # Get enhanced descriptions
            descriptions = self.get_table_descriptions(table)
            
            schema_text += f"## Table: {table}\n\n"
            
            # Create description map
            desc_map = {}
            if not descriptions.empty:
                for _, row in descriptions.iterrows():
                    desc_map[row['column_name']] = row
            
            schema_text += "| Column | Type | Description | Business Meaning | Examples |\n"
            schema_text += "|--------|------|-------------|------------------|----------|\n"
            
            for _, col in basic_schema.iterrows():
                col_name = col['column_name']
                col_type = col['data_type']
                
                if col_name in desc_map:
                    desc = desc_map[col_name]
                    description = desc['description'] or ''
                    business = desc['business_meaning'] or ''
                    examples = ', '.join(desc['example_values'][:3]) if desc['example_values'] else ''
                else:
                    description = ''
                    business = ''
                    examples = ''
                
                schema_text += f"| {col_name} | {col_type} | {description} | {business} | {examples} |\n"
            
            schema_text += "\n"
            
            # Add sample data
            try:
                sample = self.db.get_table_sample(table, limit=3)
                if not sample.empty:
                    schema_text += f"### Sample Data ({table}):\n"
                    schema_text += sample.to_markdown(index=False)
                    schema_text += "\n\n"
            except:
                pass
        
        return schema_text
    
    def add_bulk_descriptions(
        self,
        descriptions: List[Dict[str, Any]]
    ) -> int:
        """
        여러 컬럼 설명을 한번에 추가
        
        Args:
            descriptions: 설명 딕셔너리 리스트
        
        Returns:
            추가된 설명 수
        """
        count = 0
        
        for desc in descriptions:
            success = self.add_column_description(
                table_name=desc['table_name'],
                column_name=desc['column_name'],
                description=desc.get('description'),
                business_meaning=desc.get('business_meaning'),
                example_values=desc.get('example_values'),
                data_type=desc.get('data_type'),
                constraints=desc.get('constraints')
            )
            if success:
                count += 1
        
        return count
    
    def delete_column_description(
        self,
        table_name: str,
        column_name: str
    ) -> bool:
        """
        컬럼 설명 삭제
        
        Args:
            table_name: 테이블 이름
            column_name: 컬럼 이름
        
        Returns:
            성공 여부
        """
        query = """
        DELETE FROM column_descriptions
        WHERE table_name = %s AND column_name = %s
        """
        
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name, column_name))
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_all_descriptions(self) -> pd.DataFrame:
        """
        모든 컬럼 설명 조회
        
        Returns:
            모든 설명 DataFrame
        """
        query = """
        SELECT *
        FROM column_descriptions
        ORDER BY table_name, column_name
        """
        
        return self.db.execute_query_df(query)
    
    def export_to_csv(self, file_path: str):
        """
        컬럼 설명을 CSV 파일로 내보내기
        
        Args:
            file_path: CSV 파일 경로
        """
        df = self.get_all_descriptions()
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def import_from_csv(self, file_path: str) -> int:
        """
        CSV 파일에서 컬럼 설명 가져오기
        
        Args:
            file_path: CSV 파일 경로
        
        Returns:
            가져온 설명 수
        """
        df = pd.read_csv(file_path, encoding='utf-8')
        
        required_columns = ['table_name', 'column_name', 'description']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        descriptions = []
        for _, row in df.iterrows():
            desc = {
                'table_name': row['table_name'],
                'column_name': row['column_name'],
                'description': row['description'],
                'business_meaning': row.get('business_meaning') if pd.notna(row.get('business_meaning')) else None,
                'example_values': eval(row['example_values']) if pd.notna(row.get('example_values')) else None,
                'data_type': row.get('data_type') if pd.notna(row.get('data_type')) else None,
                'constraints': row.get('constraints') if pd.notna(row.get('constraints')) else None
            }
            descriptions.append(desc)
        
        return self.add_bulk_descriptions(descriptions)


def initialize_default_schema_descriptions(db: DatabaseConnection) -> int:
    """
    기본 스키마 설명 초기화
    
    Args:
        db: 데이터베이스 연결
    
    Returns:
        추가된 설명 수
    """
    enhancer = SchemaEnhancer(db)
    
    default_descriptions = [
        # employees 테이블
        {
            'table_name': 'employees',
            'column_name': 'employee_id',
            'description': '직원 고유 식별자',
            'business_meaning': '각 직원을 구분하는 유일한 번호',
            'example_values': ['1', '2', '3'],
            'data_type': 'serial',
            'constraints': 'PRIMARY KEY'
        },
        {
            'table_name': 'employees',
            'column_name': 'name',
            'description': '직원 이름',
            'business_meaning': '직원의 전체 이름',
            'example_values': ['김철수', '이영희', '박민수'],
            'data_type': 'varchar(100)',
            'constraints': 'NOT NULL'
        },
        {
            'table_name': 'employees',
            'column_name': 'salary',
            'description': '직원 연봉',
            'business_meaning': '연간 급여 (원 단위)',
            'example_values': ['5000000', '6500000', '7000000'],
            'data_type': 'decimal',
            'constraints': 'CHECK (salary > 0)'
        },
        {
            'table_name': 'employees',
            'column_name': 'hire_date',
            'description': '입사일',
            'business_meaning': '직원이 회사에 입사한 날짜',
            'example_values': ['2020-01-15', '2019-03-01', '2021-06-10'],
            'data_type': 'date',
            'constraints': None
        },
        {
            'table_name': 'employees',
            'column_name': 'department_id',
            'description': '소속 부서 ID',
            'business_meaning': '직원이 속한 부서의 식별자',
            'example_values': ['1', '2', '3'],
            'data_type': 'integer',
            'constraints': 'FOREIGN KEY (departments)'
        },
        
        # departments 테이블
        {
            'table_name': 'departments',
            'column_name': 'department_id',
            'description': '부서 고유 식별자',
            'business_meaning': '각 부서를 구분하는 유일한 번호',
            'example_values': ['1', '2', '3'],
            'data_type': 'serial',
            'constraints': 'PRIMARY KEY'
        },
        {
            'table_name': 'departments',
            'column_name': 'department_name',
            'description': '부서 이름',
            'business_meaning': '부서의 공식 명칭',
            'example_values': ['개발팀', '영업팀', '마케팅팀'],
            'data_type': 'varchar(100)',
            'constraints': 'NOT NULL, UNIQUE'
        },
        
        # sales 테이블
        {
            'table_name': 'sales',
            'column_name': 'sale_id',
            'description': '판매 고유 식별자',
            'business_meaning': '각 판매 건을 구분하는 유일한 번호',
            'example_values': ['1', '2', '3'],
            'data_type': 'serial',
            'constraints': 'PRIMARY KEY'
        },
        {
            'table_name': 'sales',
            'column_name': 'total_amount',
            'description': '판매 총액',
            'business_meaning': '해당 판매 건의 총 금액 (원 단위)',
            'example_values': ['100000', '250000', '500000'],
            'data_type': 'decimal',
            'constraints': 'CHECK (total_amount > 0)'
        },
        {
            'table_name': 'sales',
            'column_name': 'sale_date',
            'description': '판매 일자',
            'business_meaning': '상품이 판매된 날짜',
            'example_values': ['2024-01-15', '2024-02-20', '2024-03-10'],
            'data_type': 'date',
            'constraints': None
        },
        {
            'table_name': 'sales',
            'column_name': 'region',
            'description': '판매 지역',
            'business_meaning': '상품이 판매된 지역',
            'example_values': ['서울', '부산', '대구'],
            'data_type': 'varchar(50)',
            'constraints': None
        },
    ]
    
    return enhancer.add_bulk_descriptions(default_descriptions)


if __name__ == "__main__":
    # Example usage
    db = DatabaseConnection()
    enhancer = SchemaEnhancer(db)
    
    # Get enhanced schema
    enhanced = enhancer.get_enhanced_schema()
    print(enhanced)
