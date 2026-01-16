# Text2SQL Lab

온프레미스 환경에서 Text2SQL, RAG, 그리고 AI 에이전트를 실습하기 위한 완전한 테스트 환경입니다.

## 📋 개요

이 프로젝트는 다음을 제공합니다:
- 🤖 **Ollama** - 로컬 LLM 실행 및 관리
- 🌐 **Open-WebUI** - LLM 모델 관리 인터페이스
- 🗄️ **PostgreSQL + pgvector** - 벡터 검색 지원 데이터베이스
- 📊 **Langfuse** - LLM 모니터링 및 관찰성
- 🔬 **JupyterLab** - 대화형 노트북 환경
- 📚 **LangChain/LangGraph** - AI 에이전트 워크플로우
- 🎨 **시각화 도구** - 차트 및 그래프 생성

## 🚀 빠른 시작

### 1. 사전 요구사항

- Docker & Docker Compose
- 8GB 이상의 RAM
- (선택사항) NVIDIA GPU (Ollama 성능 향상)

### 2. 설치 및 실행

```bash
# 저장소 클론
git clone https://github.com/sa2z/text2sql-lab.git
cd text2sql-lab

# 환경 변수 설정
cp .env.example .env

# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 서비스 접속

서비스가 시작되면 다음 URL로 접속할 수 있습니다:

- **JupyterLab**: http://localhost:8888 (토큰 없이 접속)
- **Open-WebUI**: http://localhost:3000
- **Langfuse**: http://localhost:3001
- **PostgreSQL**: localhost:5432
- **Ollama API**: http://localhost:11434

### 4. LLM 모델 설치

```bash
# Ollama 컨테이너에서 모델 다운로드
docker exec -it text2sql-ollama ollama pull llama2

# 또는 다른 모델
docker exec -it text2sql-ollama ollama pull mistral
docker exec -it text2sql-ollama ollama pull codellama
```

## 📚 노트북 가이드

프로젝트에는 6개의 단계별 주피터 노트북이 포함되어 있습니다:

### 1. Setup and Connection (`01_setup_and_connection.ipynb`)
- 데이터베이스 연결 확인
- 서비스 상태 확인
- 데이터베이스 스키마 탐색

### 2. Embedding and RAG (`02_embedding_and_rag.ipynb`)
- 텍스트 임베딩 생성
- pgvector를 사용한 벡터 저장
- 시맨틱 검색
- RAG 시스템 구축

### 3. Text2SQL Basic (`03_text2sql_basic.ipynb`)
- 자연어를 SQL로 변환
- 쿼리 실행 및 검증
- 에러 처리
- 쿼리 히스토리 로깅

### 4. Agent Workflow (`04_agent_workflow.ipynb`)
- LangChain을 사용한 에이전트 생성
- LangGraph 워크플로우
- 에이전트 도구 통합
- 상태 관리

### 5. Visualization (`05_visualization.ipynb`)
- 쿼리 결과 시각화
- 다양한 차트 타입
- 자동 시각화
- 대시보드 생성

### 6. End-to-End (`06_end_to_end.ipynb`)
- 전체 파이프라인 데모
- RAG + Text2SQL + 시각화
- 성능 모니터링

## 🏗️ 프로젝트 구조

```
text2sql-lab/
├── docker-compose.yml          # 서비스 구성
├── Dockerfile.jupyter          # JupyterLab 이미지
├── requirements.txt            # Python 의존성
├── .env.example               # 환경 변수 템플릿
├── scripts/
│   └── init_db.sql            # 데이터베이스 초기화
├── src/
│   └── utils/
│       ├── db_utils.py        # 데이터베이스 유틸리티
│       ├── embedding_utils.py # 임베딩 유틸리티
│       ├── text2sql_utils.py  # Text2SQL 유틸리티
│       └── viz_utils.py       # 시각화 유틸리티
├── notebooks/
│   ├── 01_setup_and_connection.ipynb
│   ├── 02_embedding_and_rag.ipynb
│   ├── 03_text2sql_basic.ipynb
│   ├── 04_agent_workflow.ipynb
│   ├── 05_visualization.ipynb
│   └── 06_end_to_end.ipynb
├── data/
│   └── sample_data/           # 샘플 데이터
└── docs/                      # 추가 문서

```

## 🗄️ 데이터베이스 스키마

프로젝트에는 다음 테이블이 포함되어 있습니다:

- **employees** - 직원 정보
- **departments** - 부서 정보
- **projects** - 프로젝트 정보
- **project_assignments** - 프로젝트 할당
- **sales** - 판매 데이터
- **customers** - 고객 정보
- **lexicon** - 용어집 (RAG용)
- **documents** - 문서 (RAG용)
- **query_history** - 쿼리 히스토리

## 💡 사용 예제

### Python에서 Text2SQL 사용

```python
from src.utils.db_utils import DatabaseConnection
from src.utils.text2sql_utils import execute_text2sql

db = DatabaseConnection()
result = execute_text2sql(
    db, 
    "Show me all employees with salary greater than 6000000"
)

if result['success']:
    print(result['results'])
```

### RAG를 사용한 문서 검색

```python
from src.utils.embedding_utils import search_similar_documents

docs = search_similar_documents(
    db, 
    "How to implement text2sql?", 
    limit=3
)

for doc_id, title, content, similarity in docs:
    print(f"{title}: {similarity:.4f}")
```

### 자동 시각화

```python
from src.utils.viz_utils import auto_visualize

result = execute_text2sql(db, "What is the total sales by region?")
viz = auto_visualize(result['results'])
viz.show()
```

## 🔧 고급 설정

### vLLM 활성화 (선택사항)

고성능 LLM 추론을 위해 vLLM을 활성화할 수 있습니다:

1. `docker-compose.yml`에서 vLLM 섹션 주석 제거
2. GPU 드라이버가 설치되어 있는지 확인
3. 서비스 재시작

### Langfuse 설정

1. http://localhost:3001 접속
2. 계정 생성
3. API 키 생성
4. `.env` 파일에 키 추가

```env
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

## 🎯 주요 기능

### Text2SQL
- 자연어를 SQL로 자동 변환
- Few-shot 학습 지원
- 에러 처리 및 검증
- 쿼리 히스토리 추적

### RAG (Retrieval-Augmented Generation)
- pgvector를 사용한 벡터 검색
- 문서 및 용어집 임베딩
- 시맨틱 유사도 검색
- 컨텍스트 증강 생성

### AI 에이전트
- LangChain ReAct 에이전트
- LangGraph 워크플로우
- 커스텀 도구 통합
- 상태 관리

### 시각화
- Plotly 인터랙티브 차트
- 자동 차트 타입 선택
- 대시보드 생성
- 다양한 차트 타입 지원

## 📊 모니터링

### 쿼리 성능 모니터링

```sql
SELECT 
    natural_language_query,
    execution_time_ms,
    execution_success,
    created_at
FROM query_history
ORDER BY created_at DESC
LIMIT 10;
```

### 성공률 통계

```sql
SELECT 
    COUNT(*) as total_queries,
    AVG(execution_time_ms) as avg_time,
    SUM(CASE WHEN execution_success THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_rate
FROM query_history;
```

## 🤝 참고 자료

- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Langfuse Documentation](https://langfuse.com/docs)
- [open-agent-platform](https://github.com/open-agent-platform) - 참고 프로젝트

## 🐛 문제 해결

### Ollama가 시작되지 않을 때

```bash
docker-compose restart ollama
docker-compose logs ollama
```

### 데이터베이스 연결 오류

```bash
docker-compose restart postgres
# 데이터베이스가 준비될 때까지 대기
docker-compose logs postgres | grep "ready to accept connections"
```

### JupyterLab이 접속되지 않을 때

```bash
docker-compose restart jupyter
docker-compose logs jupyter
```

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제공됩니다.

## 🙏 기여

이슈 및 풀 리퀘스트를 환영합니다!