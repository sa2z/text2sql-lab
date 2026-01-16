-- =====================================================================
-- Few-shot 예제 테이블 초기화 스크립트
-- 
-- 목적: Text2SQL 시스템에서 사용할 예제 질의-SQL 쌍을 관리하여
--       Few-shot 학습을 통해 SQL 생성 정확도를 향상시킵니다.
-- =====================================================================

-- pgvector 확장 활성화 (임베딩 저장용)
CREATE EXTENSION IF NOT EXISTS vector;

-- Few-shot 예제 테이블 생성
CREATE TABLE IF NOT EXISTS query_examples (
    id SERIAL PRIMARY KEY,
    natural_language_query TEXT NOT NULL,               -- 자연어 질의
    sql_query TEXT NOT NULL,                            -- 대응하는 SQL 쿼리
    query_category VARCHAR(50),                         -- 쿼리 카테고리
    difficulty VARCHAR(20),                             -- 난이도 (easy, medium, hard)
    success_rate FLOAT DEFAULT 1.0,                     -- 성공률 (0.0 ~ 1.0)
    usage_count INT DEFAULT 0,                          -- 사용 횟수
    embedding vector(384),                              -- 질의 임베딩 (유사도 검색용)
    tags TEXT[],                                        -- 태그 배열
    description TEXT,                                   -- 예제 설명
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_query_examples_category ON query_examples(query_category);
CREATE INDEX IF NOT EXISTS idx_query_examples_difficulty ON query_examples(difficulty);
CREATE INDEX IF NOT EXISTS idx_query_examples_success_rate ON query_examples(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_query_examples_usage_count ON query_examples(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_query_examples_embedding ON query_examples USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 업데이트 트리거
CREATE TRIGGER update_query_examples_updated_at
    BEFORE UPDATE ON query_examples
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- 초기 예제 데이터 삽입
-- =====================================================================

-- 카테고리: 기본 조회 (easy)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('모든 직원 정보를 보여줘', 
 'SELECT * FROM employees', 
 'basic_select', 'easy', 
 ARRAY['select', 'all'], 
 '전체 직원 조회'),

('직원 테이블의 모든 데이터를 가져와줘', 
 'SELECT * FROM employees', 
 'basic_select', 'easy', 
 ARRAY['select', 'all'], 
 '전체 직원 조회'),

('급여가 5000000 이상인 직원들을 보여줘', 
 'SELECT * FROM employees WHERE salary >= 5000000', 
 'basic_select', 'easy', 
 ARRAY['select', 'where', 'comparison'], 
 '조건부 조회'),

('영업부 직원들을 조회해줘', 
 'SELECT e.* FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = ''영업부''', 
 'join', 'easy', 
 ARRAY['select', 'join', 'where'], 
 '부서별 직원 조회');

-- 카테고리: 집계 함수 (easy ~ medium)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('직원 수를 세어줘', 
 'SELECT COUNT(*) as employee_count FROM employees', 
 'aggregation', 'easy', 
 ARRAY['count', 'aggregation'], 
 '전체 직원 수 집계'),

('각 부서별 직원 수를 보여줘', 
 'SELECT d.department_name, COUNT(*) as employee_count FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name', 
 'aggregation', 'medium', 
 ARRAY['count', 'group by', 'join'], 
 '부서별 직원 수 집계'),

('부서별 평균 급여를 계산해줘', 
 'SELECT d.department_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name', 
 'aggregation', 'medium', 
 ARRAY['avg', 'group by', 'join'], 
 '부서별 평균 급여'),

('전체 직원의 평균 급여는 얼마야?', 
 'SELECT AVG(salary) as average_salary FROM employees', 
 'aggregation', 'easy', 
 ARRAY['avg', 'aggregation'], 
 '전체 평균 급여'),

('가장 높은 급여는 얼마야?', 
 'SELECT MAX(salary) as max_salary FROM employees', 
 'aggregation', 'easy', 
 ARRAY['max', 'aggregation'], 
 '최대 급여 조회');

-- 카테고리: 정렬 (easy ~ medium)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('직원들을 급여 순으로 정렬해서 보여줘', 
 'SELECT * FROM employees ORDER BY salary DESC', 
 'sorting', 'easy', 
 ARRAY['order by', 'desc'], 
 '급여 내림차순 정렬'),

('이름 순으로 직원 목록을 보여줘', 
 'SELECT * FROM employees ORDER BY name ASC', 
 'sorting', 'easy', 
 ARRAY['order by', 'asc'], 
 '이름 오름차순 정렬'),

('급여가 높은 직원 상위 10명을 보여줘', 
 'SELECT * FROM employees ORDER BY salary DESC LIMIT 10', 
 'sorting', 'medium', 
 ARRAY['order by', 'limit', 'top'], 
 '상위 N개 조회');

-- 카테고리: JOIN (medium)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('각 직원의 부서 이름을 함께 보여줘', 
 'SELECT e.name, e.salary, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id', 
 'join', 'medium', 
 ARRAY['join', 'select'], 
 '직원-부서 조인'),

('각 프로젝트에 할당된 직원 수를 보여줘', 
 'SELECT p.project_name, COUNT(pa.employee_id) as employee_count FROM projects p LEFT JOIN project_assignments pa ON p.project_id = pa.project_id GROUP BY p.project_name', 
 'join', 'medium', 
 ARRAY['left join', 'count', 'group by'], 
 '프로젝트별 인원 수'),

('프로젝트에 참여 중인 직원들의 이름과 프로젝트 이름을 보여줘', 
 'SELECT e.name as employee_name, p.project_name FROM employees e JOIN project_assignments pa ON e.employee_id = pa.employee_id JOIN projects p ON pa.project_id = p.project_id', 
 'join', 'medium', 
 ARRAY['join', 'multiple join'], 
 '다중 조인 조회');

-- 카테고리: 날짜/시간 (medium)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('올해 입사한 직원들을 보여줘', 
 'SELECT * FROM employees WHERE EXTRACT(YEAR FROM hire_date) = EXTRACT(YEAR FROM CURRENT_DATE)', 
 'datetime', 'medium', 
 ARRAY['date', 'extract', 'current_date'], 
 '올해 입사자 조회'),

('최근 6개월 내에 입사한 직원을 보여줘', 
 'SELECT * FROM employees WHERE hire_date >= CURRENT_DATE - INTERVAL ''6 months''', 
 'datetime', 'medium', 
 ARRAY['date', 'interval'], 
 '최근 입사자 조회'),

('월별 매출 합계를 보여줘', 
 'SELECT DATE_TRUNC(''month'', sale_date) as month, SUM(amount) as total_sales FROM sales GROUP BY DATE_TRUNC(''month'', sale_date) ORDER BY month', 
 'datetime', 'medium', 
 ARRAY['date_trunc', 'group by', 'sum'], 
 '월별 집계');

-- 카테고리: 복잡한 쿼리 (hard)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('각 부서별로 가장 높은 급여를 받는 직원을 보여줘', 
 'SELECT e.* FROM employees e WHERE e.salary = (SELECT MAX(e2.salary) FROM employees e2 WHERE e2.department_id = e.department_id)', 
 'complex', 'hard', 
 ARRAY['subquery', 'max', 'correlated'], 
 '부서별 최고 급여자'),

('평균 급여보다 높은 급여를 받는 직원들을 보여줘', 
 'SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)', 
 'complex', 'hard', 
 ARRAY['subquery', 'avg', 'comparison'], 
 '평균 이상 급여자'),

('부서별 매출 합계가 가장 높은 상위 3개 부서를 보여줘', 
 'SELECT d.department_name, SUM(s.amount) as total_sales FROM departments d JOIN employees e ON d.department_id = e.department_id JOIN sales s ON e.employee_id = s.employee_id GROUP BY d.department_name ORDER BY total_sales DESC LIMIT 3', 
 'complex', 'hard', 
 ARRAY['join', 'group by', 'order by', 'limit'], 
 '상위 부서 매출 분석');

-- 카테고리: 매출 분석 (medium ~ hard)
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags, description) VALUES
('지역별 매출 합계를 보여줘', 
 'SELECT region, SUM(amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC', 
 'sales_analysis', 'medium', 
 ARRAY['sum', 'group by'], 
 '지역별 매출 집계'),

('올해 월별 매출 추이를 보여줘', 
 'SELECT DATE_TRUNC(''month'', sale_date) as month, SUM(amount) as monthly_sales FROM sales WHERE EXTRACT(YEAR FROM sale_date) = EXTRACT(YEAR FROM CURRENT_DATE) GROUP BY DATE_TRUNC(''month'', sale_date) ORDER BY month', 
 'sales_analysis', 'hard', 
 ARRAY['date_trunc', 'sum', 'group by', 'where'], 
 '월별 매출 추이'),

('고객별 총 구매액을 보여줘', 
 'SELECT c.customer_name, SUM(s.amount) as total_purchase FROM customers c JOIN sales s ON c.customer_id = s.customer_id GROUP BY c.customer_name ORDER BY total_purchase DESC', 
 'sales_analysis', 'medium', 
 ARRAY['join', 'sum', 'group by'], 
 '고객별 구매액');

-- =====================================================================
-- 예제 관리 헬퍼 함수
-- =====================================================================

-- 유사 예제 검색 함수 (임베딩 기반)
-- 주의: 이 함수는 임베딩이 설정된 후에 사용 가능합니다
CREATE OR REPLACE FUNCTION find_similar_examples(query_embedding vector(384), limit_count INT DEFAULT 3)
RETURNS TABLE (
    example_id INT,
    natural_query TEXT,
    sql_query TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id,
        natural_language_query,
        query_examples.sql_query,
        1 - (embedding <=> query_embedding) as similarity
    FROM query_examples
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- 카테고리별 예제 통계
CREATE OR REPLACE FUNCTION get_example_statistics()
RETURNS TABLE (
    category VARCHAR(50),
    example_count BIGINT,
    avg_success_rate FLOAT,
    avg_usage_count FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        query_category,
        COUNT(*) as example_count,
        AVG(success_rate) as avg_success_rate,
        AVG(usage_count::FLOAT) as avg_usage_count
    FROM query_examples
    GROUP BY query_category
    ORDER BY example_count DESC;
END;
$$ LANGUAGE plpgsql;

-- 성공률 업데이트 함수
CREATE OR REPLACE FUNCTION update_example_success(example_id INT, was_successful BOOLEAN)
RETURNS VOID AS $$
BEGIN
    UPDATE query_examples
    SET 
        usage_count = usage_count + 1,
        success_rate = CASE 
            WHEN was_successful THEN 
                (success_rate * usage_count + 1.0) / (usage_count + 1)
            ELSE 
                (success_rate * usage_count) / (usage_count + 1)
        END,
        updated_at = NOW()
    WHERE id = example_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 사용 예제 (주석)
-- =====================================================================

-- 예제 1: 모든 예제 조회
-- SELECT natural_language_query, sql_query, difficulty 
-- FROM query_examples 
-- ORDER BY difficulty, query_category;

-- 예제 2: 특정 카테고리 예제 조회
-- SELECT * FROM query_examples WHERE query_category = 'aggregation';

-- 예제 3: 난이도별 예제 수
-- SELECT difficulty, COUNT(*) FROM query_examples GROUP BY difficulty;

-- 예제 4: 통계 조회
-- SELECT * FROM get_example_statistics();

-- 예제 5: 성공률 업데이트
-- SELECT update_example_success(1, TRUE);

-- =====================================================================
-- 완료 메시지
-- =====================================================================

DO $$
DECLARE
    example_count INT;
BEGIN
    SELECT COUNT(*) INTO example_count FROM query_examples;
    RAISE NOTICE '✓ Few-shot 예제 테이블 초기화 완료';
    RAISE NOTICE '  - query_examples 테이블 생성';
    RAISE NOTICE '  - 초기 예제 % 개 삽입 완료', example_count;
    RAISE NOTICE '  - 헬퍼 함수 생성 완료';
END $$;
