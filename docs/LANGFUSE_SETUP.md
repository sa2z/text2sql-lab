# Langfuse 별도 설치 가이드

Langfuse는 LLM 애플리케이션의 추적, 모니터링 및 디버깅을 위한 오픈소스 플랫폼입니다. Text2SQL Lab에서는 선택적으로 사용할 수 있습니다.

## 왜 별도 설치인가?

Langfuse는 다음과 같은 추가 의존성이 필요합니다:
- ClickHouse (분석 데이터베이스)
- Redis (캐싱, 선택사항)
- 추가 환경 설정

이러한 복잡성으로 인해 메인 docker-compose.yml을 간소화하고 Langfuse는 별도로 설치하도록 구성했습니다.

---

## 방법 1: 공식 Docker Compose 사용 (권장)

### 1.1 Langfuse 저장소 클론

```bash
# Langfuse 저장소를 별도 디렉토리에 클론
cd ~/projects  # 또는 원하는 위치
git clone https://github.com/langfuse/langfuse.git
cd langfuse
```

### 1.2 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필요한 부분만)
nano .env
```

최소 설정:
```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-random-secret-key-change-this
SALT=your-random-salt-change-this
```

### 1.3 서비스 시작

```bash
# Docker Compose로 시작
docker compose up -d

# 로그 확인
docker compose logs -f
```

### 1.4 접속 및 설정

1. 브라우저에서 http://localhost:3000 접속
2. 초기 계정 생성
3. 프로젝트 생성
4. API 키 생성 (Settings → API Keys)
   - Public Key (pk-xxx)
   - Secret Key (sk-xxx)

---

## 방법 2: 간소화된 Docker Compose 사용

Text2SQL Lab과 함께 실행할 수 있는 최소 구성입니다.

### 2.1 간소화된 docker-compose-langfuse.yml 생성

```yaml
version: '3.8'

services:
  # Langfuse용 PostgreSQL (Text2SQL Lab의 PostgreSQL과 별도)
  langfuse-db:
    image: postgres:16
    container_name: langfuse-db
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse123
      POSTGRES_DB: langfuse
    volumes:
      - langfuse_db_data:/var/lib/postgresql/data
    networks:
      - langfuse-network
    ports:
      - "5433:5432"

  # ClickHouse for Langfuse
  langfuse-clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: langfuse-clickhouse
    environment:
      CLICKHOUSE_DB: langfuse
      CLICKHOUSE_USER: langfuse
      CLICKHOUSE_PASSWORD: langfuse123
    volumes:
      - langfuse_clickhouse_data:/var/lib/clickhouse
    networks:
      - langfuse-network
    ports:
      - "8123:8123"

  # Langfuse Server
  langfuse:
    image: langfuse/langfuse:latest
    container_name: langfuse-server
    depends_on:
      - langfuse-db
      - langfuse-clickhouse
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse123@langfuse-db:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: change-this-to-random-secret
      SALT: change-this-to-random-salt
      CLICKHOUSE_URL: http://langfuse-clickhouse:8123
      CLICKHOUSE_USER: langfuse
      CLICKHOUSE_PASSWORD: langfuse123
      LANGFUSE_INIT_ORG_ID: text2sql-org
      LANGFUSE_INIT_ORG_NAME: Text2SQL Lab
      LANGFUSE_INIT_PROJECT_ID: text2sql-project
      LANGFUSE_INIT_PROJECT_NAME: Text2SQL Project
    networks:
      - langfuse-network

volumes:
  langfuse_db_data:
  langfuse_clickhouse_data:

networks:
  langfuse-network:
    driver: bridge
```

### 2.2 실행

```bash
# 별도 docker-compose 파일로 실행
docker-compose -f docker-compose-langfuse.yml up -d

# 또는 파일 이름 저장 후
docker-compose up -d
```

---

## Text2SQL Lab과 통합

### 3.1 API 키 발급

1. Langfuse 웹 인터페이스 접속 (http://localhost:3000)
2. Settings → API Keys 메뉴
3. "Create New API Key" 클릭
4. Public Key와 Secret Key 복사

### 3.2 환경 변수 설정

Text2SQL Lab의 `.env` 파일에 추가:

```env
# Langfuse Configuration
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
```

### 3.3 노트북에서 사용

```python
from langfuse import Langfuse
import os

# Langfuse 클라이언트 초기화
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

# Text2SQL 쿼리 추적
trace = langfuse.trace(name="text2sql-query")

# 생성 단계 추적
generation = trace.generation(
    name="sql-generation",
    model="llama2",
    input={"query": "Show me all employees with salary > 60000"},
    output={"sql": "SELECT * FROM employees WHERE salary > 60000"}
)

# 완료
generation.end()
```

### 3.4 LangChain 통합

```python
from langchain.callbacks.tracers import LangChainTracer
from langfuse.callback import CallbackHandler

# Langfuse 콜백 핸들러
langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

# LangChain에서 사용
from langchain_community.llms import Ollama

llm = Ollama(model="llama2")
response = llm.invoke(
    "Convert to SQL: Show employees",
    config={"callbacks": [langfuse_handler]}
)
```

---

## 문제 해결

### Langfuse가 시작되지 않음

```bash
# 로그 확인
docker logs langfuse-server

# 데이터베이스 연결 확인
docker exec -it langfuse-db psql -U langfuse -d langfuse
```

### ClickHouse 연결 오류

```bash
# ClickHouse 상태 확인
docker exec -it langfuse-clickhouse clickhouse-client --query "SELECT 1"

# 로그 확인
docker logs langfuse-clickhouse
```

### API 키 오류

- Public Key와 Secret Key가 올바르게 복사되었는지 확인
- `.env` 파일에 따옴표 없이 입력했는지 확인
- Langfuse 웹 UI에서 API 키가 활성화되어 있는지 확인

---

## 성능 최적화

### ClickHouse 메모리 설정

대용량 데이터 처리 시 ClickHouse 메모리 설정 조정:

```yaml
langfuse-clickhouse:
  environment:
    CLICKHOUSE_DB: langfuse
    CLICKHOUSE_USER: langfuse
    CLICKHOUSE_PASSWORD: langfuse123
    # 메모리 제한 (선택사항)
    MAX_MEMORY_USAGE: 4000000000  # 4GB
```

### PostgreSQL 최적화

```yaml
langfuse-db:
  environment:
    POSTGRES_USER: langfuse
    POSTGRES_PASSWORD: langfuse123
    POSTGRES_DB: langfuse
    # 성능 설정
    POSTGRES_SHARED_BUFFERS: 256MB
    POSTGRES_MAX_CONNECTIONS: 100
```

---

## 대안: Langfuse Cloud 사용

로컬 설치 대신 Langfuse Cloud를 사용할 수도 있습니다:

1. https://cloud.langfuse.com 접속
2. 무료 계정 생성
3. 프로젝트 생성 및 API 키 발급
4. Text2SQL Lab `.env`에 설정:

```env
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
```

**장점:**
- 설치 및 관리 불필요
- 자동 업데이트
- 백업 및 확장성

**단점:**
- 데이터가 외부에 저장됨
- 인터넷 연결 필요

---

## 참고 자료

- [Langfuse 공식 문서](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [LangChain Integration](https://langfuse.com/docs/integrations/langchain)
- [Self-Hosting Guide](https://langfuse.com/docs/deployment/self-host)

---

## 요약

1. **간단한 사용**: Langfuse Cloud 사용 (https://cloud.langfuse.com)
2. **완전한 제어**: 공식 Docker Compose 사용
3. **Text2SQL Lab 통합**: 간소화된 docker-compose-langfuse.yml 사용

Text2SQL Lab은 Langfuse 없이도 완전히 작동하며, LLM 모니터링이 필요할 때만 선택적으로 설치하면 됩니다.
