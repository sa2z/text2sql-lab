# n8n 워크플로우 템플릿

이 디렉토리에는 Text2SQL Lab에서 즉시 사용 가능한 n8n 워크플로우 템플릿이 포함되어 있습니다.

## 📁 템플릿 목록

### 1. daily_sales_report.json
매일 아침 9시에 자동으로 전날 매출 현황을 조회하는 워크플로우

**기능**:
- 스케줄 트리거 (매일 09:00)
- PostgreSQL 쿼리 실행
- 전날 매출 데이터 집계

**사용 방법**:
1. n8n UI에서 워크플로우 가져오기
2. PostgreSQL Credentials 설정
3. 워크플로우 활성화

### 2. slack_text2sql_bot.json
Slack을 통해 자연어 질의를 받아 SQL 결과를 반환하는 봇

**기능**:
- Slack Webhook 트리거
- 자연어를 SQL로 변환 (Ollama 사용)
- 쿼리 실행 및 결과 반환

**사용 방법**:
1. Slack App 생성 및 Webhook URL 획득
2. n8n에서 워크플로우 가져오기
3. Webhook URL 및 Credentials 설정
4. 워크플로우 활성화

## 🚀 템플릿 가져오기

### 방법 1: n8n UI 사용

1. n8n 접속: http://localhost:55678
2. 로그인 (admin/admin123)
3. 우측 상단 메뉴 → **Import from File**
4. JSON 파일 선택
5. **Save** 클릭

### 방법 2: n8n CLI 사용

```bash
# n8n 컨테이너에서 직접 가져오기
docker exec text2sql-n8n n8n import:workflow --input=/path/to/workflow.json
```

## 🔧 Credentials 설정

### PostgreSQL

워크플로우에서 PostgreSQL을 사용하려면 다음 정보로 Credentials를 생성하세요:

```
Host: postgres
Port: 5432
Database: text2sql_db
User: text2sql
Password: text2sql123
```

**설정 방법**:
1. n8n UI → Credentials → Add Credential
2. **Postgres** 선택
3. 위 정보 입력
4. **Test** → **Save**

### Ollama (HTTP Request 사용)

Ollama API는 별도의 Credentials 없이 HTTP Request 노드로 호출 가능합니다:

```
URL: http://ollama:11434/api/generate
Method: POST
Body:
{
  "model": "llama2",
  "prompt": "{{$json.query}}",
  "stream": false
}
```

## 📝 워크플로우 커스터마이징

### 스케줄 변경

Schedule Trigger 노드의 Cron Expression을 수정:

```
0 9 * * *   → 매일 09:00
0 */6 * * * → 6시간마다
0 18 * * 1  → 매주 월요일 18:00
```

### 쿼리 수정

PostgreSQL 노드의 Query 필드를 수정하여 원하는 쿼리로 변경하세요.

### 알림 추가

워크플로우 끝에 다음 노드를 추가할 수 있습니다:

- **Email** - 이메일 발송
- **Slack** - Slack 메시지 발송
- **Discord** - Discord 메시지 발송
- **HTTP Request** - 커스텀 Webhook 호출

## 🔍 문제 해결

### 워크플로우 가져오기 실패

- JSON 파일이 올바른 형식인지 확인
- n8n 버전이 호환되는지 확인

### PostgreSQL 연결 실패

- 호스트명을 `postgres` 사용 (localhost 아님)
- Docker 네트워크 내부이므로 포트는 `5432` 사용

### Ollama API 실패

- Ollama 컨테이너가 실행 중인지 확인
- 모델이 설치되어 있는지 확인: `make list-models`

## 📚 추가 리소스

- [n8n 공식 문서](https://docs.n8n.io)
- [PostgreSQL 노드 문서](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/)
- [Webhook 노드 문서](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [Schedule Trigger 문서](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/)

## 💡 워크플로우 아이디어

더 많은 워크플로우 아이디어:

1. **재고 부족 알림** - 재고가 임계값 이하일 때 알림
2. **신규 고객 환영 메시지** - 신규 고객 등록 시 자동 이메일
3. **주간 리포트** - 주간 매출/성과 리포트 자동 생성
4. **데이터 백업** - 정기적인 데이터 백업 및 외부 저장소 업로드
5. **이상 거래 탐지** - 비정상 패턴 탐지 및 알림
