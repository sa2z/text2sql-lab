# Gradio Web Interface for Text2SQL Lab

## Overview

이 디렉토리는 Text2SQL Lab의 웹 인터페이스를 포함합니다.

## 실행 방법

### Docker 환경에서 실행

```bash
# Jupyter 컨테이너 내에서 실행
docker-compose exec jupyter python /workspace/app/gradio_ui.py
```

### 로컬 환경에서 실행

```bash
# 필요한 패키지 설치 확인
pip install gradio>=4.0.0

# 환경 변수 설정
export POSTGRES_HOST=localhost
export POSTGRES_PORT=55433
export POSTGRES_USER=text2sql
export POSTGRES_PASSWORD=text2sql123
export POSTGRES_DB=text2sql_db
export OLLAMA_HOST=http://localhost:51435

# 실행
python app/gradio_ui.py
```

## 접속

실행 후 브라우저에서 접속:
- **URL**: http://localhost:7860

## 주요 기능

### 1. 📝 Text2SQL 실행
- 자연어 질의를 입력하면 자동으로 SQL을 생성하고 실행
- RAG (Retrieval-Augmented Generation) 지원
- 다양한 LLM 모델 선택 가능
- 실행 시간 및 결과 통계 표시

### 2. 📈 차트 생성
- 쿼리 결과를 자동으로 시각화
- 5가지 차트 타입 지원 (Auto, Bar, Line, Pie, Scatter)
- Plotly 기반 인터랙티브 차트

### 3. 📜 히스토리
- 최근 50개의 쿼리 실행 기록 조회
- 성공률, 평균 실행 시간 등 통계 제공
- 실시간 새로고침 기능

### 4. 📄 문서 업로드
- PDF, Word, Excel, Text 파일 업로드
- 자동 임베딩 및 벡터 저장
- RAG에 활용되는 문서 데이터베이스 구축

## 예제 질의

- "급여가 6000000원 이상인 직원들을 보여줘"
- "부서별 평균 급여를 알려줘"
- "진행 중인 프로젝트와 담당 부서를 보여줘"
- "지역별 총 매출을 내림차순으로 정렬해줘"
- "Engineering 부서의 직원 수는?"

## 기술 스택

- **UI Framework**: Gradio 4.0+
- **LLM**: LangChain + Ollama (Llama2, Llama3, Mistral, CodeLlama)
- **Database**: PostgreSQL + pgvector
- **Embeddings**: Sentence Transformers
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Document Processing**: PyPDF2, pdfplumber, python-docx, openpyxl

## 아키텍처

```
Gradio UI (Port 7860)
    ├── Text2SQL Generator (LangChain + Ollama)
    ├── Database Connection (PostgreSQL)
    ├── RAG System (Embeddings + pgvector)
    ├── Visualization Engine (Plotly)
    └── Document Loader (Multi-format support)
```

## 문제 해결

### 데이터베이스 연결 실패
```bash
# PostgreSQL 서비스 확인
make status

# 서비스 재시작
make restart
```

### Ollama 모델 없음
```bash
# 모델 설치
make install-model      # Llama2
make install-mistral    # Mistral
```

### 포트 충돌
```python
# gradio_ui.py에서 포트 변경
demo.launch(
    server_port=7861,  # 다른 포트로 변경
    ...
)
```

## 보안 고려사항

- SQL Injection 방지: 생성된 SQL에서 위험한 명령어 (INSERT, UPDATE, DELETE 등) 차단
- 읽기 전용 쿼리만 허용 (SELECT, WITH)
- 모든 오류는 로그에 기록되며 사용자에게는 안전한 메시지만 표시

## 개발 팁

### 디버그 모드 실행
```python
# app/gradio_ui.py 수정
demo.launch(
    server_port=7860,
    debug=True,  # 추가
    ...
)
```

### 로그 확인
```bash
# Python 로그 레벨 조정
export PYTHONPATH=/workspace
python -u app/gradio_ui.py 2>&1 | tee gradio.log
```

## 라이센스

이 프로젝트는 Text2SQL Lab의 일부입니다.
