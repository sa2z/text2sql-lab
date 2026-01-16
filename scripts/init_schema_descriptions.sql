-- =====================================================================
-- 스키마 설명 테이블 초기화 스크립트
-- 
-- 목적: 데이터베이스 스키마에 대한 상세한 설명을 저장하여
--       LLM이 더 정확한 SQL을 생성할 수 있도록 지원합니다.
-- =====================================================================

-- 컬럼 설명 테이블 생성
CREATE TABLE IF NOT EXISTS column_descriptions (
    table_name VARCHAR(100),                            -- 테이블 이름
    column_name VARCHAR(100),                           -- 컬럼 이름
    korean_name VARCHAR(100),                           -- 한글 이름
    description TEXT,                                   -- 컬럼 설명
    business_meaning TEXT,                              -- 비즈니스 의미
    example_values TEXT[],                              -- 예시 값들
    data_type VARCHAR(50),                              -- 데이터 타입
    constraints TEXT,                                   -- 제약 조건
    related_columns TEXT[],                             -- 연관 컬럼들
    notes TEXT,                                         -- 추가 노트
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (table_name, column_name)
);

-- 테이블 설명 테이블 생성
CREATE TABLE IF NOT EXISTS table_descriptions (
    table_name VARCHAR(100) PRIMARY KEY,                -- 테이블 이름
    korean_name VARCHAR(100),                           -- 한글 이름
    description TEXT,                                   -- 테이블 설명
    business_purpose TEXT,                              -- 비즈니스 목적
    related_tables TEXT[],                              -- 연관 테이블들
    common_queries TEXT[],                              -- 자주 사용되는 쿼리 패턴
    notes TEXT,                                         -- 추가 노트
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_column_descriptions_table ON column_descriptions(table_name);
CREATE INDEX IF NOT EXISTS idx_column_descriptions_korean ON column_descriptions(korean_name);

-- 업데이트 트리거
CREATE TRIGGER update_column_descriptions_updated_at
    BEFORE UPDATE ON column_descriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_table_descriptions_updated_at
    BEFORE UPDATE ON table_descriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- 초기 테이블 설명 데이터
-- =====================================================================

INSERT INTO table_descriptions (table_name, korean_name, description, business_purpose, related_tables, common_queries) VALUES
('employees', '직원', 
 '회사 직원들의 기본 정보를 저장하는 테이블', 
 '직원 관리, 인사 정보 조회, 급여 관리',
 ARRAY['departments', 'project_assignments'],
 ARRAY['부서별 직원 수', '급여 통계', '입사일 조회']),

('departments', '부서', 
 '회사의 부서 정보를 저장하는 테이블', 
 '조직 구조 관리, 부서별 집계',
 ARRAY['employees', 'projects'],
 ARRAY['부서 목록', '부서별 직원 수', '부서별 예산']),

('projects', '프로젝트', 
 '진행 중이거나 완료된 프로젝트 정보를 저장하는 테이블', 
 '프로젝트 관리, 진행 상황 추적',
 ARRAY['project_assignments', 'departments'],
 ARRAY['진행 중인 프로젝트', '프로젝트별 예산', '완료율']),

('project_assignments', '프로젝트 할당', 
 '직원들의 프로젝트 배정 정보를 저장하는 테이블', 
 '인력 배치 관리, 업무 할당 추적',
 ARRAY['employees', 'projects'],
 ARRAY['프로젝트별 인원', '직원별 담당 프로젝트', '역할별 할당']),

('sales', '매출', 
 '제품이나 서비스의 판매 기록을 저장하는 테이블', 
 '매출 분석, 영업 실적 추적',
 ARRAY['customers', 'employees'],
 ARRAY['월별 매출', '지역별 매출', '고객별 구매 이력']),

('customers', '고객', 
 '거래처 및 고객 정보를 저장하는 테이블', 
 '고객 관리, CRM, 매출 분석',
 ARRAY['sales'],
 ARRAY['고객 목록', '지역별 고객 수', '주요 고객']);

-- =====================================================================
-- 초기 컬럼 설명 데이터: employees 테이블
-- =====================================================================

INSERT INTO column_descriptions (table_name, column_name, korean_name, description, business_meaning, example_values, data_type, constraints, related_columns) VALUES
('employees', 'employee_id', '직원ID', 
 '직원을 고유하게 식별하는 번호', 
 '직원의 고유 식별자. 시스템 내에서 중복되지 않는 값',
 ARRAY['1', '2', '100'],
 'INTEGER', 'PRIMARY KEY, AUTO_INCREMENT',
 ARRAY['project_assignments.employee_id', 'sales.employee_id']),

('employees', 'name', '이름', 
 '직원의 성명', 
 '직원의 실명. 한글 또는 영문으로 기록',
 ARRAY['김철수', '이영희', 'John Smith'],
 'VARCHAR(100)', 'NOT NULL',
 NULL),

('employees', 'email', '이메일', 
 '직원의 회사 이메일 주소', 
 '업무용 이메일. 사내 커뮤니케이션 및 시스템 로그인에 사용',
 ARRAY['kim.cs@company.com', 'lee.yh@company.com'],
 'VARCHAR(100)', 'UNIQUE, NOT NULL',
 NULL),

('employees', 'phone', '전화번호', 
 '직원의 연락처', 
 '긴급 연락처 또는 업무 연락처',
 ARRAY['010-1234-5678', '02-1234-5678'],
 'VARCHAR(20)', NULL,
 NULL),

('employees', 'hire_date', '입사일', 
 '직원이 회사에 입사한 날짜', 
 '근속 기간 계산, 연차 계산 등에 사용',
 ARRAY['2020-01-15', '2019-03-01', '2023-06-10'],
 'DATE', 'NOT NULL',
 NULL),

('employees', 'salary', '급여', 
 '직원의 월급', 
 '세전 월 급여액. 원화(KRW) 단위',
 ARRAY['3000000', '4500000', '6000000'],
 'DECIMAL(10,2)', 'NOT NULL, CHECK (salary > 0)',
 NULL),

('employees', 'department_id', '부서ID', 
 '직원이 소속된 부서의 식별자', 
 '부서 정보와 조인하여 부서명 등을 조회',
 ARRAY['1', '2', '5'],
 'INTEGER', 'FOREIGN KEY REFERENCES departments(department_id)',
 ARRAY['departments.department_id']),

('employees', 'position', '직급', 
 '직원의 직급이나 직책', 
 '사원, 대리, 과장, 부장 등의 직급',
 ARRAY['사원', '대리', '과장', '부장', '이사'],
 'VARCHAR(50)', NULL,
 NULL),

('employees', 'status', '재직상태', 
 '직원의 현재 재직 상태', 
 'active: 재직 중, inactive: 퇴사',
 ARRAY['active', 'inactive'],
 'VARCHAR(20)', 'DEFAULT ''active''',
 NULL);

-- =====================================================================
-- 초기 컬럼 설명 데이터: departments 테이블
-- =====================================================================

INSERT INTO column_descriptions (table_name, column_name, korean_name, description, business_meaning, example_values, data_type, constraints, related_columns) VALUES
('departments', 'department_id', '부서ID', 
 '부서를 고유하게 식별하는 번호', 
 '부서의 고유 식별자',
 ARRAY['1', '2', '10'],
 'INTEGER', 'PRIMARY KEY, AUTO_INCREMENT',
 ARRAY['employees.department_id', 'projects.department_id']),

('departments', 'department_name', '부서명', 
 '부서의 공식 명칭', 
 '조직도에 표시되는 부서 이름',
 ARRAY['영업부', '개발부', '인사부', '마케팅부'],
 'VARCHAR(100)', 'NOT NULL, UNIQUE',
 NULL),

('departments', 'location', '위치', 
 '부서가 위치한 사무실이나 층', 
 '물리적 사무 공간 위치',
 ARRAY['본관 3층', '별관 2층', '서울 본사'],
 'VARCHAR(100)', NULL,
 NULL),

('departments', 'budget', '예산', 
 '부서에 배정된 연간 예산', 
 '부서 운영 및 프로젝트 수행을 위한 예산. 원화(KRW) 단위',
 ARRAY['100000000', '500000000', '1000000000'],
 'DECIMAL(12,2)', 'CHECK (budget >= 0)',
 NULL),

('departments', 'manager_id', '부서장ID', 
 '부서를 책임지는 관리자의 직원 ID', 
 '부서장 정보 조회 시 employees 테이블과 조인',
 ARRAY['5', '12', '23'],
 'INTEGER', 'FOREIGN KEY REFERENCES employees(employee_id)',
 ARRAY['employees.employee_id']);

-- =====================================================================
-- 초기 컬럼 설명 데이터: projects 테이블
-- =====================================================================

INSERT INTO column_descriptions (table_name, column_name, korean_name, description, business_meaning, example_values, data_type, constraints, related_columns) VALUES
('projects', 'project_id', '프로젝트ID', 
 '프로젝트를 고유하게 식별하는 번호', 
 '프로젝트의 고유 식별자',
 ARRAY['1', '2', '100'],
 'INTEGER', 'PRIMARY KEY, AUTO_INCREMENT',
 ARRAY['project_assignments.project_id']),

('projects', 'project_name', '프로젝트명', 
 '프로젝트의 공식 명칭', 
 '프로젝트를 구분하기 위한 이름',
 ARRAY['신제품 개발', 'ERP 시스템 구축', '마케팅 캠페인'],
 'VARCHAR(200)', 'NOT NULL',
 NULL),

('projects', 'start_date', '시작일', 
 '프로젝트가 시작된 날짜', 
 '프로젝트 기간 계산에 사용',
 ARRAY['2023-01-01', '2023-06-15'],
 'DATE', 'NOT NULL',
 ARRAY['projects.end_date']),

('projects', 'end_date', '종료일', 
 '프로젝트 완료 예정 또는 완료된 날짜', 
 '프로젝트 기간 및 일정 관리에 사용',
 ARRAY['2023-12-31', '2024-03-31'],
 'DATE', NULL,
 ARRAY['projects.start_date']),

('projects', 'budget', '예산', 
 '프로젝트에 배정된 예산', 
 '프로젝트 수행을 위한 총 예산. 원화(KRW) 단위',
 ARRAY['50000000', '200000000', '500000000'],
 'DECIMAL(12,2)', 'CHECK (budget > 0)',
 NULL),

('projects', 'status', '상태', 
 '프로젝트의 현재 진행 상태', 
 'planning: 계획 중, in_progress: 진행 중, completed: 완료, cancelled: 취소',
 ARRAY['planning', 'in_progress', 'completed', 'cancelled'],
 'VARCHAR(20)', 'DEFAULT ''planning''',
 NULL),

('projects', 'department_id', '담당부서ID', 
 '프로젝트를 주관하는 부서의 식별자', 
 '프로젝트 책임 부서',
 ARRAY['1', '2', '5'],
 'INTEGER', 'FOREIGN KEY REFERENCES departments(department_id)',
 ARRAY['departments.department_id']);

-- =====================================================================
-- 초기 컬럼 설명 데이터: sales 테이블
-- =====================================================================

INSERT INTO column_descriptions (table_name, column_name, korean_name, description, business_meaning, example_values, data_type, constraints, related_columns) VALUES
('sales', 'sale_id', '매출ID', 
 '매출 기록을 고유하게 식별하는 번호', 
 '각 판매 거래의 고유 식별자',
 ARRAY['1', '2', '1000'],
 'INTEGER', 'PRIMARY KEY, AUTO_INCREMENT',
 NULL),

('sales', 'customer_id', '고객ID', 
 '구매한 고객의 식별자', 
 '고객 정보 조회 시 customers 테이블과 조인',
 ARRAY['1', '50', '100'],
 'INTEGER', 'FOREIGN KEY REFERENCES customers(customer_id)',
 ARRAY['customers.customer_id']),

('sales', 'employee_id', '담당직원ID', 
 '판매를 담당한 직원의 식별자', 
 '영업 실적 집계에 사용',
 ARRAY['5', '12', '23'],
 'INTEGER', 'FOREIGN KEY REFERENCES employees(employee_id)',
 ARRAY['employees.employee_id']),

('sales', 'amount', '매출금액', 
 '판매 금액', 
 '실제 판매된 금액. 원화(KRW) 단위',
 ARRAY['100000', '500000', '2000000'],
 'DECIMAL(10,2)', 'NOT NULL, CHECK (amount > 0)',
 NULL),

('sales', 'sale_date', '판매일', 
 '판매가 이루어진 날짜', 
 '매출 집계 및 추이 분석에 사용',
 ARRAY['2023-01-15', '2023-12-20'],
 'DATE', 'NOT NULL',
 NULL),

('sales', 'region', '지역', 
 '판매가 이루어진 지역', 
 '지역별 매출 분석에 사용',
 ARRAY['서울', '경기', '부산', '대구', '인천'],
 'VARCHAR(50)', NULL,
 NULL),

('sales', 'product_name', '제품명', 
 '판매된 제품이나 서비스의 이름', 
 '제품별 매출 분석에 사용',
 ARRAY['제품A', '제품B', '서비스X'],
 'VARCHAR(100)', NULL,
 NULL);

-- =====================================================================
-- 초기 컬럼 설명 데이터: customers 테이블
-- =====================================================================

INSERT INTO column_descriptions (table_name, column_name, korean_name, description, business_meaning, example_values, data_type, constraints, related_columns) VALUES
('customers', 'customer_id', '고객ID', 
 '고객을 고유하게 식별하는 번호', 
 '고객의 고유 식별자',
 ARRAY['1', '2', '500'],
 'INTEGER', 'PRIMARY KEY, AUTO_INCREMENT',
 ARRAY['sales.customer_id']),

('customers', 'customer_name', '고객명', 
 '고객의 이름 또는 회사명', 
 '개인 고객의 경우 이름, 법인 고객의 경우 회사명',
 ARRAY['홍길동', '(주)ABC', '김영희'],
 'VARCHAR(100)', 'NOT NULL',
 NULL),

('customers', 'email', '이메일', 
 '고객의 이메일 주소', 
 '연락 및 마케팅에 사용',
 ARRAY['hong@example.com', 'info@abc.com'],
 'VARCHAR(100)', NULL,
 NULL),

('customers', 'phone', '전화번호', 
 '고객의 연락처', 
 '고객 응대 및 주문 확인에 사용',
 ARRAY['010-1234-5678', '02-1234-5678'],
 'VARCHAR(20)', NULL,
 NULL),

('customers', 'region', '지역', 
 '고객이 위치한 지역', 
 '지역별 고객 분석에 사용',
 ARRAY['서울', '경기', '부산', '제주'],
 'VARCHAR(50)', NULL,
 ARRAY['sales.region']),

('customers', 'registration_date', '등록일', 
 '고객 정보가 등록된 날짜', 
 '고객 획득 시기 분석에 사용',
 ARRAY['2020-01-01', '2022-05-15'],
 'DATE', 'DEFAULT CURRENT_DATE',
 NULL);

-- =====================================================================
-- 스키마 정보 조회 함수
-- =====================================================================

-- 테이블의 전체 스키마 정보 (설명 포함) 조회
CREATE OR REPLACE FUNCTION get_enhanced_table_schema(target_table VARCHAR(100))
RETURNS TABLE (
    column_name VARCHAR(100),
    korean_name VARCHAR(100),
    data_type VARCHAR(50),
    description TEXT,
    example_values TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cd.column_name,
        cd.korean_name,
        cd.data_type,
        cd.description,
        array_to_string(cd.example_values, ', ') as example_values
    FROM column_descriptions cd
    WHERE cd.table_name = target_table
    ORDER BY cd.column_name;
END;
$$ LANGUAGE plpgsql;

-- 전체 데이터베이스의 테이블 목록과 설명 조회
CREATE OR REPLACE FUNCTION get_all_tables_summary()
RETURNS TABLE (
    table_name VARCHAR(100),
    korean_name VARCHAR(100),
    description TEXT,
    column_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        td.table_name,
        td.korean_name,
        td.description,
        (SELECT COUNT(*) FROM column_descriptions cd WHERE cd.table_name = td.table_name) as column_count
    FROM table_descriptions td
    ORDER BY td.table_name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 사용 예제 (주석)
-- =====================================================================

-- 예제 1: 특정 테이블의 컬럼 설명 조회
-- SELECT * FROM get_enhanced_table_schema('employees');

-- 예제 2: 모든 테이블 요약 정보 조회
-- SELECT * FROM get_all_tables_summary();

-- 예제 3: 특정 한글 이름으로 컬럼 찾기
-- SELECT table_name, column_name, description 
-- FROM column_descriptions 
-- WHERE korean_name LIKE '%급여%';

-- 예제 4: 테이블 관계 파악
-- SELECT table_name, korean_name, related_tables 
-- FROM table_descriptions;

-- =====================================================================
-- 완료 메시지
-- =====================================================================

DO $$
DECLARE
    table_count INT;
    column_count INT;
BEGIN
    SELECT COUNT(*) INTO table_count FROM table_descriptions;
    SELECT COUNT(*) INTO column_count FROM column_descriptions;
    RAISE NOTICE '✓ 스키마 설명 테이블 초기화 완료';
    RAISE NOTICE '  - table_descriptions: % 개 테이블', table_count;
    RAISE NOTICE '  - column_descriptions: % 개 컬럼', column_count;
    RAISE NOTICE '  - 헬퍼 함수 생성 완료';
END $$;
