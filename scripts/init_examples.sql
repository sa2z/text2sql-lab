-- Create table for few-shot query examples
-- This script should be run after init_db.sql and requires pgvector extension

-- Query examples table for few-shot learning
CREATE TABLE IF NOT EXISTS query_examples (
    id SERIAL PRIMARY KEY,
    natural_language_query TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    query_category VARCHAR(50),  -- aggregation, join, filter, sort, etc.
    difficulty VARCHAR(20) DEFAULT 'medium',  -- easy, medium, hard
    tags TEXT[],
    success_rate FLOAT DEFAULT 0.0,  -- Success rate when used as example
    usage_count INT DEFAULT 0,  -- How many times this example was used
    embedding vector(384),  -- Embedding for semantic search
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_query_examples_category ON query_examples(query_category);
CREATE INDEX idx_query_examples_difficulty ON query_examples(difficulty);
CREATE INDEX idx_query_examples_success ON query_examples(success_rate DESC);
CREATE INDEX idx_query_examples_tags ON query_examples USING GIN(tags);

-- Create vector index for semantic search (requires pgvector)
-- This will speed up similarity searches
CREATE INDEX IF NOT EXISTS idx_query_examples_embedding 
ON query_examples USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comments
COMMENT ON TABLE query_examples IS 'Stores example queries for few-shot learning in Text2SQL';
COMMENT ON COLUMN query_examples.embedding IS 'Vector embedding of the natural language query for semantic similarity search';
COMMENT ON COLUMN query_examples.success_rate IS 'Success rate (0-1) when this example is used in few-shot prompts';
COMMENT ON COLUMN query_examples.usage_count IS 'Number of times this example has been retrieved and used';

-- Sample few-shot examples
INSERT INTO query_examples (natural_language_query, sql_query, query_category, difficulty, tags) VALUES
-- Basic SELECT queries
('모든 직원을 보여주세요', 'SELECT * FROM employees;', 'select', 'easy', ARRAY['basic', 'employees']),
('모든 부서를 보여주세요', 'SELECT * FROM departments;', 'select', 'easy', ARRAY['basic', 'departments']),
('모든 판매 내역을 보여주세요', 'SELECT * FROM sales;', 'select', 'easy', ARRAY['basic', 'sales']),

-- Filtering queries
('급여가 6000000보다 큰 직원을 보여주세요', 'SELECT * FROM employees WHERE salary > 6000000;', 'filter', 'easy', ARRAY['filter', 'employees', 'salary']),
('2020년 이후에 입사한 직원을 보여주세요', 'SELECT * FROM employees WHERE hire_date > ''2020-01-01'';', 'filter', 'easy', ARRAY['filter', 'employees', 'date']),
('개발팀 직원만 보여주세요', 'SELECT e.* FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = ''개발팀'';', 'filter', 'medium', ARRAY['filter', 'join', 'employees']),

-- JOIN queries
('직원 이름과 소속 부서명을 보여주세요', 'SELECT e.name, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id;', 'join', 'medium', ARRAY['join', 'employees', 'departments']),
('각 프로젝트에 할당된 직원 목록을 보여주세요', 'SELECT p.project_name, e.name FROM projects p JOIN project_assignments pa ON p.project_id = pa.project_id JOIN employees e ON pa.employee_id = e.employee_id;', 'join', 'hard', ARRAY['join', 'projects', 'employees']),

-- Aggregation queries
('부서별 평균 급여를 계산해주세요', 'SELECT d.department_name, AVG(e.salary) as avg_salary FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name;', 'aggregation', 'medium', ARRAY['aggregation', 'join', 'salary']),
('각 부서의 직원 수를 세어주세요', 'SELECT d.department_name, COUNT(*) as employee_count FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name;', 'aggregation', 'medium', ARRAY['aggregation', 'count', 'departments']),
('지역별 총 매출을 보여주세요', 'SELECT region, SUM(total_amount) as total_sales FROM sales GROUP BY region ORDER BY total_sales DESC;', 'aggregation', 'medium', ARRAY['aggregation', 'sales', 'sort']),
('월별 매출을 계산해주세요', 'SELECT DATE_TRUNC(''month'', sale_date) as month, SUM(total_amount) as monthly_sales FROM sales GROUP BY DATE_TRUNC(''month'', sale_date) ORDER BY month;', 'aggregation', 'hard', ARRAY['aggregation', 'date', 'sales']),

-- Sorting and limiting
('급여가 가장 높은 5명의 직원을 보여주세요', 'SELECT * FROM employees ORDER BY salary DESC LIMIT 5;', 'sort', 'easy', ARRAY['sort', 'limit', 'salary']),
('가장 최근에 입사한 10명의 직원을 보여주세요', 'SELECT * FROM employees ORDER BY hire_date DESC LIMIT 10;', 'sort', 'easy', ARRAY['sort', 'limit', 'date']),

-- Complex queries
('마케팅 부서의 총 급여는 얼마인가요?', 'SELECT SUM(e.salary) as total_salary FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE d.department_name = ''마케팅팀'';', 'aggregation', 'medium', ARRAY['aggregation', 'filter', 'join']),
('급여가 부서 평균보다 높은 직원을 보여주세요', 'SELECT e.name, e.salary, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id WHERE e.salary > (SELECT AVG(salary) FROM employees WHERE department_id = e.department_id);', 'subquery', 'hard', ARRAY['subquery', 'aggregation', 'filter']),
('각 부서에서 가장 높은 급여를 받는 직원을 보여주세요', 'WITH max_salaries AS (SELECT department_id, MAX(salary) as max_salary FROM employees GROUP BY department_id) SELECT e.name, e.salary, d.department_name FROM employees e JOIN departments d ON e.department_id = d.department_id JOIN max_salaries ms ON e.department_id = ms.department_id AND e.salary = ms.max_salary;', 'subquery', 'hard', ARRAY['cte', 'aggregation', 'join']),

-- Date and time queries
('2023년에 입사한 직원 수는?', 'SELECT COUNT(*) as count FROM employees WHERE EXTRACT(YEAR FROM hire_date) = 2023;', 'aggregation', 'medium', ARRAY['aggregation', 'date', 'count']),
('최근 30일간의 매출을 보여주세요', 'SELECT * FROM sales WHERE sale_date >= CURRENT_DATE - INTERVAL ''30 days'' ORDER BY sale_date DESC;', 'filter', 'medium', ARRAY['filter', 'date', 'sales']),

-- NULL handling
('부서가 할당되지 않은 직원을 보여주세요', 'SELECT * FROM employees WHERE department_id IS NULL;', 'filter', 'easy', ARRAY['filter', 'null']),

-- Pattern matching
('이름이 김으로 시작하는 직원을 보여주세요', 'SELECT * FROM employees WHERE name LIKE ''김%'';', 'filter', 'easy', ARRAY['filter', 'pattern', 'employees']),

-- HAVING clause
('직원이 5명 이상인 부서만 보여주세요', 'SELECT d.department_name, COUNT(*) as employee_count FROM employees e JOIN departments d ON e.department_id = d.department_id GROUP BY d.department_name HAVING COUNT(*) >= 5;', 'aggregation', 'medium', ARRAY['aggregation', 'having', 'filter'])

ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON query_examples TO text2sql;
GRANT USAGE, SELECT ON SEQUENCE query_examples_id_seq TO text2sql;
