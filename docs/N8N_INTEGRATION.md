# n8n 워크플로우 자동화 가이드

## 개요

n8n은 노드 기반 워크플로우 자동화 도구로, Text2SQL 시스템과 연계하여 다양한 자동화를 구현할 수 있습니다.

## 접속 정보

- **URL**: http://localhost:55678
- **사용자명**: admin
- **비밀번호**: admin123

⚠️ **보안**: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!

---

## 주요 활용 시나리오

### 1. 📊 스케줄링된 보고서 생성

매일 아침 9시에 전날 매출 현황을 자동으로 이메일 발송

**워크플로우**:
```
[스케줄 트리거] → [PostgreSQL 쿼리] → [데이터 가공] → [이메일 발송]
```

---

### 2. 💬 Slack/Discord 봇

Slack 메시지로 자연어 질의를 보내면 SQL 결과 반환

**워크플로우**:
```
[Slack Webhook] → [Text2SQL API 호출] → [결과 포맷팅] → [Slack 응답]
```

---

### 3. 🔗 REST API 엔드포인트

외부 시스템에서 Text2SQL을 API로 호출

**API 예시**:
```bash
curl -X POST http://localhost:55678/webhook/text2sql \
  -H "Content-Type: application/json" \
  -d '{"query": "각 부서별 직원 수는?"}'
```

---

### 4. 🚨 알림 시스템

특정 조건 만족 시 자동 알림 (예: 재고 부족)

---

## PostgreSQL 연결 설정

### Credentials 생성

1. n8n UI에서 Credentials → Add Credential
2. PostgreSQL 선택
3. 연결 정보 입력:
   - **Host**: `postgres`
   - **Port**: `5432`
   - **Database**: `text2sql_db`
   - **User**: `text2sql`
   - **Password**: `text2sql123`

---

## 자주 사용하는 쿼리

### 일일 매출 현황
```sql
SELECT 
    DATE(sale_date) as date,
    SUM(total_amount) as total,
    COUNT(*) as orders
FROM sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY DATE(sale_date)
```

### 부서별 통계
```sql
SELECT 
    d.department_name,
    COUNT(e.employee_id) as count,
    AVG(e.salary) as avg_salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
GROUP BY d.department_name
```

---

## Ollama 연동

HTTP Request 노드로 Ollama API 호출:

**URL**: `http://ollama:11434/api/generate`

**Body**:
```json
{
  "model": "llama2",
  "prompt": "Convert to SQL: {{$json.query}}",
  "stream": false
}
```

---

## 보안 설정

### 비밀번호 변경

docker-compose.yml 또는 .env에서:
```yaml
- N8N_BASIC_AUTH_USER=your_username
- N8N_BASIC_AUTH_PASSWORD=strong_password
```

---

## 워크플로우 템플릿

`workflows/` 디렉토리에 다음 템플릿 제공:

1. **daily_sales_report.json** - 일일 매출 리포트
2. **slack_text2sql_bot.json** - Slack 봇

### 템플릿 사용법

1. n8n UI → Settings → Import from File
2. JSON 파일 선택
3. Credentials 설정
4. 워크플로우 활성화

---

## 문제 해결

### PostgreSQL 연결 실패
- 호스트명을 `postgres` 사용 (localhost 아님)
- 포트는 `5432` (내부 포트)

### Ollama API 실패
- URL: `http://ollama:11434`
- 모델 다운로드 확인: `docker exec text2sql-ollama ollama list`

---

## 참고 자료

- n8n 공식 문서: https://docs.n8n.io
- PostgreSQL 노드: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/
