# Langfuse 별도 설치 가이드

Langfuse는 LLM 관찰성(Observability) 및 모니터링을 위한 강력한 도구입니다. 그러나 ClickHouse, Redis 등 복잡한 의존성을 가지고 있어 Text2SQL Lab의 메인 docker-compose에서 분리하여 별도로 관리하는 것을 권장합니다.

## 📌 중요 참고사항

**Langfuse 없이도 Text2SQL Lab의 모든 핵심 기능을 사용할 수 있습니다.**

Langfuse는 다음과 같은 경우에 유용합니다:
- 프로덕션 환경에서 LLM 호출 추적
- 프롬프트 버전 관리 및 A/B 테스팅
- 비용 분석 및 성능 모니터링
- 팀 단위 LLM 애플리케이션 관리

학습 및 개발 목적으로는 Langfuse가 필수는 아닙니다.

---

## 🚀 설치 방법

### 방법 1: 공식 Docker Compose 사용 (권장)

가장 간단하고 안정적인 방법입니다.

```bash
# 별도 디렉토리에 Langfuse 설치
mkdir -p ~/langfuse
cd ~/langfuse

# 공식 저장소에서 docker-compose 다운로드
curl -O https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml

# 환경 변수 설정
cat > .env << EOF
# Database
POSTGRES_USER=langfuse
POSTGRES_PASSWORD=langfuse_password_change_me
POSTGRES_DB=langfuse

# Langfuse Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=$(openssl rand -base64 32)
SALT=$(openssl rand -base64 32)

# ClickHouse
CLICKHOUSE_USER=langfuse
CLICKHOUSE_PASSWORD=clickhouse_password_change_me
EOF

# Langfuse 시작
docker compose up -d

# 로그 확인
docker compose logs -f
```

접속: http://localhost:3000

### 방법 2: Langfuse Cloud 사용 (무료 티어 제공)

로컬 설치가 부담스러운 경우, Langfuse Cloud를 사용할 수 있습니다.

1. https://cloud.langfuse.com 방문
2. 무료 계정 생성
3. 프로젝트 생성 및 API 키 발급
4. Text2SQL Lab에서 API 키 사용 (아래 통합 섹션 참조)

**장점:**
- 설치 불필요
- 자동 백업 및 업데이트
- 무료 티어로 시작 가능

**단점:**
- 데이터가 클라우드에 저장됨
- 네트워크 연결 필요

### 방법 3: 간소화 버전 (최소 구성)

개발/테스트 목적으로 간소화된 버전을 설치할 수 있습니다.

```bash
# 간소화 docker-compose.yml 생성
cat > docker-compose.langfuse.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL for Langfuse
  langfuse-postgres:
    image: postgres:15
    container_name: langfuse-postgres
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse123
      POSTGRES_DB: langfuse
    ports:
      - "54321:5432"
    volumes:
      - langfuse_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ClickHouse for analytics
  langfuse-clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: langfuse-clickhouse
    environment:
      CLICKHOUSE_DB: langfuse
      CLICKHOUSE_USER: langfuse
      CLICKHOUSE_PASSWORD: langfuse123
      CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT: 1
    ports:
      - "58123:8123"
      - "59000:9000"
    volumes:
      - langfuse_clickhouse_data:/var/lib/clickhouse
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Langfuse Server
  langfuse-server:
    image: langfuse/langfuse:latest
    container_name: langfuse-server
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse123@langfuse-postgres:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: changeme-nextauth-secret-min-32-chars
      SALT: changeme-salt-min-32-chars
      CLICKHOUSE_URL: http://langfuse-clickhouse:8123
      CLICKHOUSE_USER: langfuse
      CLICKHOUSE_PASSWORD: langfuse123
    depends_on:
      langfuse-postgres:
        condition: service_healthy
      langfuse-clickhouse:
        condition: service_healthy

volumes:
  langfuse_postgres_data:
  langfuse_clickhouse_data:
EOF

# 시작
docker compose -f docker-compose.langfuse.yml up -d
```

---

## 🔗 Text2SQL Lab과 통합

Langfuse를 설치한 후, Text2SQL Lab의 노트북에서 사용하려면:

### 1. API 키 발급

Langfuse 웹 인터페이스 (http://localhost:3000)에서:
1. 계정 생성/로그인
2. Settings → API Keys로 이동
3. "Create new API keys" 클릭
4. Public Key와 Secret Key 복사

### 2. 환경 변수 설정

Text2SQL Lab의 `.env` 파일에 추가:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxxxxx
LANGFUSE_HOST=http://localhost:3000

# Langfuse Cloud를 사용하는 경우
# LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. 노트북에서 사용

```python
import os
from langfuse import Langfuse

# Langfuse 초기화
langfuse = Langfuse(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    host=os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
)

# LLM 호출 추적
trace = langfuse.trace(
    name="text2sql-query",
    user_id="test-user"
)

# Text2SQL 실행 (예제)
generation = trace.generation(
    name="sql-generation",
    model="llama2",
    input={"query": "Show me all employees"},
    output={"sql": "SELECT * FROM employees"}
)
```

### 4. LangChain과 통합

```python
from langchain.callbacks.langfuse import LangfuseCallbackHandler

# Callback handler 생성
langfuse_handler = LangfuseCallbackHandler(
    public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
    host=os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
)

# LLM 호출 시 callback 사용
from langchain_community.llms import Ollama

llm = Ollama(model="llama2", base_url=os.getenv('OLLAMA_HOST'))
response = llm.invoke(
    "Generate SQL query", 
    callbacks=[langfuse_handler]
)
```

---

## 📊 Langfuse 주요 기능

### 1. Trace 분석
- 각 LLM 호출의 입력/출력 추적
- 실행 시간 측정
- 에러 및 예외 기록

### 2. 프롬프트 관리
- 프롬프트 버전 관리
- A/B 테스팅
- 프롬프트 템플릿 공유

### 3. 비용 분석
- 토큰 사용량 추적
- 모델별 비용 계산
- 일일/월별 통계

### 4. 데이터셋 관리
- Few-shot 예제 관리
- 테스트 케이스 저장
- 평가 데이터셋 구성

---

## 🔧 문제 해결

### Langfuse에 접속되지 않을 때

```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs langfuse-server

# 데이터베이스 연결 확인
docker compose logs langfuse-postgres
```

### ClickHouse 에러

ClickHouse는 많은 메모리를 사용합니다. 최소 4GB RAM 권장.

```bash
# ClickHouse 로그 확인
docker compose logs langfuse-clickhouse

# 메모리 부족 시 ClickHouse 비활성화 가능
# (일부 분석 기능 제한됨)
```

### 포트 충돌

기본 포트 3000이 이미 사용 중인 경우:

```yaml
# docker-compose.yml에서 포트 변경
services:
  langfuse-server:
    ports:
      - "3001:3000"  # 3001로 변경
    environment:
      NEXTAUTH_URL: http://localhost:3001  # URL도 변경
```

---

## 📚 추가 자료

- [Langfuse 공식 문서](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [OpenAI Integration](https://langfuse.com/docs/integrations/openai)

---

## ⚠️ 보안 주의사항

프로덕션 환경에서는 반드시:

1. **강력한 비밀번호 설정**
   ```bash
   # 안전한 비밀 키 생성
   openssl rand -base64 32
   ```

2. **환경 변수 보안**
   - `.env` 파일을 git에 커밋하지 않기
   - 프로덕션에서는 secret manager 사용

3. **네트워크 보안**
   - 외부 접근이 필요한 경우 HTTPS 사용
   - 방화벽 규칙 설정

4. **정기적인 업데이트**
   ```bash
   docker compose pull
   docker compose up -d
   ```

---

## 💡 학습 목적으로는 Langfuse 없이 시작하세요!

Text2SQL Lab의 모든 노트북과 예제는 Langfuse 없이도 완벽하게 작동합니다. Langfuse는 프로덕션 환경이나 팀 프로젝트에서 유용한 선택적(optional) 도구입니다.

먼저 Text2SQL 핵심 기능을 익힌 후, 필요할 때 Langfuse를 추가하는 것을 권장합니다.
