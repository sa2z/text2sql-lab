-- =====================================================================
-- 용어 매핑 테이블 초기화 스크립트
-- 
-- 목적: 비즈니스 용어와 기술 용어 간의 매핑을 관리하여
--       자연어 질의의 이해도를 향상시킵니다.
-- =====================================================================

-- 용어 매핑 테이블 생성
CREATE TABLE IF NOT EXISTS term_mappings (
    id SERIAL PRIMARY KEY,
    business_term VARCHAR(100) NOT NULL,                -- 비즈니스 용어 (예: "매출")
    technical_terms TEXT[] NOT NULL,                    -- 기술 용어 배열 (예: ["sales_amount", "revenue"])
    synonyms TEXT[],                                    -- 동의어 배열 (예: ["판매액", "수익"])
    description TEXT,                                   -- 용어 설명
    category VARCHAR(50),                               -- 카테고리 (finance, hr, operations 등)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_term_mappings_business_term ON term_mappings(business_term);
CREATE INDEX IF NOT EXISTS idx_term_mappings_category ON term_mappings(category);
CREATE INDEX IF NOT EXISTS idx_term_mappings_technical_terms ON term_mappings USING GIN(technical_terms);

-- 업데이트 트리거 (updated_at 자동 갱신)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_term_mappings_updated_at
    BEFORE UPDATE ON term_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================================
-- 초기 용어 데이터 삽입
-- =====================================================================

-- 재무/회계 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('매출', ARRAY['sales_amount', 'total_amount', 'revenue'], ARRAY['판매액', '수익', '영업수익'], '제품이나 서비스 판매로 발생한 총 금액', 'finance'),
('매출액', ARRAY['sales_amount', 'revenue'], ARRAY['판매액'], '판매로 발생한 금액', 'finance'),
('수익', ARRAY['revenue', 'income'], ARRAY['이익', '수입'], '총 수익 금액', 'finance'),
('비용', ARRAY['cost', 'expense'], ARRAY['경비', '지출'], '사업 운영에 소요된 금액', 'finance'),
('이익', ARRAY['profit', 'net_income'], ARRAY['순이익'], '수익에서 비용을 뺀 금액', 'finance'),
('예산', ARRAY['budget'], ARRAY['배정액', '할당액'], '특정 목적을 위해 배정된 금액', 'finance'),
('금액', ARRAY['amount', 'value'], ARRAY['액수'], '화폐 단위의 수량', 'finance');

-- 인사/HR 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('직원', ARRAY['employee', 'emp'], ARRAY['사원', '임직원', '종업원'], '회사에 고용된 사람', 'hr'),
('사원', ARRAY['employee', 'emp'], ARRAY['직원'], '회사에 소속된 직원', 'hr'),
('급여', ARRAY['salary'], ARRAY['월급', '봉급', '임금'], '근로의 대가로 지급되는 금액', 'hr'),
('연봉', ARRAY['annual_salary'], ARRAY['연간급여'], '1년간 받는 총 급여', 'hr'),
('직급', ARRAY['position', 'job_title'], ARRAY['직위', '직책'], '조직 내 직무 등급', 'hr'),
('입사일', ARRAY['hire_date', 'join_date'], ARRAY['입사날짜', '채용일'], '회사에 입사한 날짜', 'hr'),
('퇴사일', ARRAY['termination_date', 'leave_date'], ARRAY['퇴직일'], '회사를 떠난 날짜', 'hr');

-- 조직 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('부서', ARRAY['department', 'dept'], ARRAY['팀', '부문'], '업무 기능별 조직 단위', 'organization'),
('팀', ARRAY['team', 'department'], ARRAY['부서'], '특정 업무를 수행하는 그룹', 'organization'),
('본부', ARRAY['division', 'headquarters'], ARRAY['사업부'], '여러 부서를 포괄하는 조직', 'organization'),
('지점', ARRAY['branch', 'office'], ARRAY['영업소', '사업소'], '본사와 별도 위치의 사무소', 'organization');

-- 프로젝트 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('프로젝트', ARRAY['project'], ARRAY['과제', '업무'], '특정 목표 달성을 위한 작업', 'project'),
('과제', ARRAY['task', 'project'], ARRAY['업무', '일감'], '수행해야 할 작업', 'project'),
('납기', ARRAY['deadline', 'due_date'], ARRAY['마감일', '완료일'], '작업 완료 기한', 'project'),
('진척도', ARRAY['progress', 'completion_rate'], ARRAY['진행률', '완료율'], '작업 진행 정도', 'project'),
('담당자', ARRAY['assignee', 'owner'], ARRAY['책임자'], '업무 담당 인원', 'project');

-- 고객/영업 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('고객', ARRAY['customer', 'client'], ARRAY['거래처', '클라이언트'], '제품이나 서비스를 구매하는 대상', 'sales'),
('거래처', ARRAY['customer', 'account'], ARRAY['고객사'], '거래 관계에 있는 회사', 'sales'),
('주문', ARRAY['order', 'purchase_order'], ARRAY['발주'], '제품이나 서비스 구매 요청', 'sales'),
('배송', ARRAY['delivery', 'shipment'], ARRAY['운송'], '제품을 고객에게 전달', 'sales'),
('지역', ARRAY['region', 'area'], ARRAY['지방', '구역'], '지리적 영업 구역', 'sales');

-- 시간 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('날짜', ARRAY['date'], ARRAY['일자'], '특정 시점의 년월일', 'datetime'),
('기간', ARRAY['period', 'duration'], ARRAY['시간', '구간'], '시작과 끝이 있는 시간 범위', 'datetime'),
('년도', ARRAY['year'], ARRAY['연도'], '특정 년도', 'datetime'),
('월', ARRAY['month'], ARRAY['월별'], '특정 월', 'datetime'),
('분기', ARRAY['quarter'], ARRAY['쿼터'], '3개월 단위 기간', 'datetime'),
('주', ARRAY['week'], ARRAY['주간'], '7일 단위 기간', 'datetime'),
('최근', ARRAY['recent', 'latest'], ARRAY['최신'], '가까운 과거', 'datetime'),
('올해', ARRAY['this_year', 'current_year'], ARRAY['금년'], '현재 년도', 'datetime'),
('작년', ARRAY['last_year'], ARRAY['전년', '지난해'], '직전 년도', 'datetime');

-- 집계/통계 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('합계', ARRAY['sum', 'total'], ARRAY['총합', '누계'], '모든 값을 더한 결과', 'aggregation'),
('평균', ARRAY['average', 'avg', 'mean'], ARRAY['평균값'], '값들의 산술 평균', 'aggregation'),
('최대', ARRAY['max', 'maximum'], ARRAY['최댓값', '최고'], '가장 큰 값', 'aggregation'),
('최소', ARRAY['min', 'minimum'], ARRAY['최솟값', '최저'], '가장 작은 값', 'aggregation'),
('개수', ARRAY['count', 'number'], ARRAY['건수', '수량'], '항목의 개수', 'aggregation'),
('비율', ARRAY['rate', 'ratio', 'percentage'], ARRAY['비중', '백분율'], '전체 대비 비율', 'aggregation'),
('순위', ARRAY['rank', 'ranking'], ARRAY['등수'], '크기 순서에 따른 위치', 'aggregation');

-- 비교/필터링 관련 용어
INSERT INTO term_mappings (business_term, technical_terms, synonyms, description, category) VALUES
('상위', ARRAY['top', 'highest'], ARRAY['높은', '많은'], '순위가 높은', 'comparison'),
('하위', ARRAY['bottom', 'lowest'], ARRAY['낮은', '적은'], '순위가 낮은', 'comparison'),
('이상', ARRAY['greater_than_or_equal', 'gte'], ARRAY['초과'], '특정 값보다 크거나 같음', 'comparison'),
('이하', ARRAY['less_than_or_equal', 'lte'], ARRAY['미만'], '특정 값보다 작거나 같음', 'comparison'),
('초과', ARRAY['greater_than', 'gt'], ARRAY['이상'], '특정 값보다 큼', 'comparison'),
('미만', ARRAY['less_than', 'lt'], ARRAY['이하'], '특정 값보다 작음', 'comparison');

-- =====================================================================
-- 용어 검색을 위한 헬퍼 함수
-- =====================================================================

-- 비즈니스 용어로 기술 용어 찾기
CREATE OR REPLACE FUNCTION find_technical_terms(business_term_input TEXT)
RETURNS TEXT[] AS $$
DECLARE
    result TEXT[];
BEGIN
    SELECT technical_terms INTO result
    FROM term_mappings
    WHERE LOWER(business_term) = LOWER(business_term_input)
    LIMIT 1;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 동의어로 비즈니스 용어 찾기
CREATE OR REPLACE FUNCTION find_business_term_by_synonym(synonym_input TEXT)
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    SELECT business_term INTO result
    FROM term_mappings
    WHERE synonym_input = ANY(synonyms)
    LIMIT 1;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- 사용 예제 (주석)
-- =====================================================================

-- 예제 1: 특정 카테고리의 모든 용어 조회
-- SELECT business_term, technical_terms, synonyms 
-- FROM term_mappings 
-- WHERE category = 'finance';

-- 예제 2: 비즈니스 용어로 기술 용어 찾기
-- SELECT find_technical_terms('매출');

-- 예제 3: 동의어로 비즈니스 용어 찾기
-- SELECT find_business_term_by_synonym('판매액');

-- 예제 4: 전체 용어 통계
-- SELECT category, COUNT(*) as term_count 
-- FROM term_mappings 
-- GROUP BY category 
-- ORDER BY term_count DESC;

-- =====================================================================
-- 완료 메시지
-- =====================================================================

DO $$
BEGIN
    RAISE NOTICE '✓ 용어 매핑 테이블 초기화 완료';
    RAISE NOTICE '  - term_mappings 테이블 생성';
    RAISE NOTICE '  - 초기 용어 데이터 삽입 완료';
    RAISE NOTICE '  - 헬퍼 함수 생성 완료';
END $$;
