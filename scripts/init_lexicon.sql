-- Create tables for lexicon and schema enhancement
-- This script should be run after init_db.sql

-- Term mappings table for lexicon management
CREATE TABLE IF NOT EXISTS term_mappings (
    id SERIAL PRIMARY KEY,
    business_term VARCHAR(100) NOT NULL,
    technical_term VARCHAR(100) NOT NULL,
    synonyms TEXT[],
    description TEXT,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_term_mappings_business ON term_mappings(LOWER(business_term));
CREATE INDEX idx_term_mappings_technical ON term_mappings(LOWER(technical_term));
CREATE INDEX idx_term_mappings_category ON term_mappings(category);

-- Column descriptions table for schema enhancement
CREATE TABLE IF NOT EXISTS column_descriptions (
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    description TEXT,
    business_meaning TEXT,
    example_values TEXT[],
    data_type VARCHAR(50),
    constraints TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (table_name, column_name)
);

CREATE INDEX idx_column_descriptions_table ON column_descriptions(table_name);

-- Comments
COMMENT ON TABLE term_mappings IS 'Stores mappings between business terms and technical database terms';
COMMENT ON TABLE column_descriptions IS 'Stores detailed descriptions and business meanings for database columns';

-- Sample data for term_mappings
INSERT INTO term_mappings (business_term, technical_term, synonyms, description, category) VALUES
('직원', 'employees', ARRAY['사원', '임직원', 'employee'], '직원 테이블', 'hr'),
('급여', 'salary', ARRAY['연봉', '월급', 'wage', 'pay'], '직원 급여', 'hr'),
('부서', 'department', ARRAY['부서명', 'dept'], '부서 정보', 'hr'),
('입사일', 'hire_date', ARRAY['채용일', '입사날짜'], '직원 입사일', 'hr'),
('매출', 'total_amount', ARRAY['판매액', '매출액', 'sales', 'revenue'], '판매 금액', 'sales'),
('고객', 'customer', ARRAY['구매자', '클라이언트', 'client'], '고객 정보', 'sales'),
('주문', 'order', ARRAY['구매', '오더'], '주문 정보', 'sales'),
('지역', 'region', ARRAY['지방', '권역'], '판매 지역', 'sales'),
('프로젝트', 'project', ARRAY['과제', 'PJ'], '프로젝트 정보', 'project'),
('예산', 'budget', ARRAY['비용'], '프로젝트 예산', 'project')
ON CONFLICT DO NOTHING;

-- Sample data for column_descriptions
INSERT INTO column_descriptions (table_name, column_name, description, business_meaning, example_values, data_type, constraints) VALUES
('employees', 'employee_id', '직원 고유 식별자', '각 직원을 구분하는 유일한 번호', ARRAY['1', '2', '3'], 'serial', 'PRIMARY KEY'),
('employees', 'name', '직원 이름', '직원의 전체 이름', ARRAY['김철수', '이영희', '박민수'], 'varchar(100)', 'NOT NULL'),
('employees', 'salary', '직원 연봉', '연간 급여 (원 단위)', ARRAY['5000000', '6500000', '7000000'], 'decimal', 'CHECK (salary > 0)'),
('employees', 'hire_date', '입사일', '직원이 회사에 입사한 날짜', ARRAY['2020-01-15', '2019-03-01', '2021-06-10'], 'date', NULL),
('employees', 'department_id', '소속 부서 ID', '직원이 속한 부서의 식별자', ARRAY['1', '2', '3'], 'integer', 'FOREIGN KEY (departments)'),
('departments', 'department_id', '부서 고유 식별자', '각 부서를 구분하는 유일한 번호', ARRAY['1', '2', '3'], 'serial', 'PRIMARY KEY'),
('departments', 'department_name', '부서 이름', '부서의 공식 명칭', ARRAY['개발팀', '영업팀', '마케팅팀'], 'varchar(100)', 'NOT NULL, UNIQUE'),
('sales', 'sale_id', '판매 고유 식별자', '각 판매 건을 구분하는 유일한 번호', ARRAY['1', '2', '3'], 'serial', 'PRIMARY KEY'),
('sales', 'total_amount', '판매 총액', '해당 판매 건의 총 금액 (원 단위)', ARRAY['100000', '250000', '500000'], 'decimal', 'CHECK (total_amount > 0)'),
('sales', 'sale_date', '판매 일자', '상품이 판매된 날짜', ARRAY['2024-01-15', '2024-02-20', '2024-03-10'], 'date', NULL),
('sales', 'region', '판매 지역', '상품이 판매된 지역', ARRAY['서울', '부산', '대구'], 'varchar(50)', NULL)
ON CONFLICT (table_name, column_name) DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON term_mappings TO text2sql;
GRANT SELECT, INSERT, UPDATE, DELETE ON column_descriptions TO text2sql;
GRANT USAGE, SELECT ON SEQUENCE term_mappings_id_seq TO text2sql;
