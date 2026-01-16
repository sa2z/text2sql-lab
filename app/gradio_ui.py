"""
Gradio Web Interface for Text2SQL Lab

종합적인 Text2SQL 웹 인터페이스
- Text2SQL 실행 및 시각화
- 히스토리 추적
- 문서 업로드 및 RAG
"""
import sys
sys.path.append('/workspace')

import os
import time
import logging
from typing import Optional, Tuple, Any
from datetime import datetime
import pandas as pd
import gradio as gr
import plotly.graph_objects as go

# Import utilities
from src.utils.db_utils import DatabaseConnection, get_database_context
from src.utils.text2sql_utils import Text2SQLGenerator
from src.utils.viz_utils import auto_visualize, create_bar_chart, create_line_chart, create_pie_chart, create_scatter_plot
from src.utils.embedding_utils import EmbeddingGenerator, store_document_with_embedding, search_similar_documents, chunk_text
from src.utils.document_loader import DocumentLoader, split_documents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for storing query results
current_query_result = {
    'df': None,
    'sql': None,
    'natural_query': None,
    'chart': None
}


def execute_text2sql(natural_query: str, use_rag: bool, model_name: str) -> Tuple[str, Any, str]:
    """
    Text2SQL 실행 함수
    
    Args:
        natural_query: 자연어 질의
        use_rag: RAG 사용 여부
        model_name: LLM 모델 이름
    
    Returns:
        (생성된 SQL, 결과 DataFrame, 상태 메시지)
    """
    global current_query_result
    
    if not natural_query.strip():
        return "", None, "❌ 질의를 입력해주세요."
    
    try:
        start_time = time.time()
        
        # Database connection
        db = DatabaseConnection()
        
        # Get schema context
        schema_context = get_database_context()
        
        # RAG: Search similar documents if enabled
        rag_context = ""
        if use_rag:
            try:
                similar_docs = search_similar_documents(db, natural_query, limit=3)
                if similar_docs:
                    rag_context = "\n\n관련 문서 컨텍스트:\n"
                    for i, (doc_id, title, content, similarity) in enumerate(similar_docs, 1):
                        rag_context += f"\n{i}. {title} (유사도: {similarity:.3f})\n{content[:200]}...\n"
            except Exception as rag_error:
                logger.warning(f"RAG 검색 실패 (무시): {rag_error}")
        
        # Generate SQL
        generator = Text2SQLGenerator(model_name=model_name)
        sql_query = generator.generate_sql(
            natural_query, 
            schema_context + rag_context
        )
        
        # Execute SQL
        df = db.execute_query_df(sql_query)
        
        # Calculate execution time
        execution_time = int((time.time() - start_time) * 1000)
        row_count = len(df)
        
        # Log to database
        try:
            db.log_query(
                natural_query,
                sql_query,
                True,
                execution_time,
                row_count,
                None
            )
        except Exception as log_error:
            logger.warning(f"쿼리 로깅 실패 (무시): {log_error}")
        
        # Store in global state
        current_query_result['df'] = df
        current_query_result['sql'] = sql_query
        current_query_result['natural_query'] = natural_query
        current_query_result['chart'] = None
        
        # Create status message
        status = f"✅ 실행 성공\n"
        status += f"⏱️ 실행 시간: {execution_time}ms\n"
        status += f"📊 결과 행 수: {row_count}개"
        
        return sql_query, df, status
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Text2SQL 실행 실패: {error_msg}")
        
        # Log error to database
        try:
            db = DatabaseConnection()
            db.log_query(
                natural_query,
                sql_query if 'sql_query' in locals() else None,
                False,
                int((time.time() - start_time) * 1000) if 'start_time' in locals() else 0,
                0,
                error_msg
            )
        except:
            pass
        
        return "", None, f"❌ 실행 실패\n오류: {error_msg}"


def generate_chart(chart_type: str) -> Tuple[Any, str]:
    """
    차트 생성 함수
    
    Args:
        chart_type: 차트 타입 (Auto, Bar, Line, Pie, Scatter)
    
    Returns:
        (차트 객체, 상태 메시지)
    """
    global current_query_result
    
    if current_query_result['df'] is None or current_query_result['df'].empty:
        return None, "❌ 먼저 쿼리를 실행해주세요."
    
    try:
        df = current_query_result['df']
        
        # Get column info
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not numeric_cols and chart_type != 'Auto':
            return None, "❌ 숫자 데이터가 없어 차트를 생성할 수 없습니다."
        
        chart = None
        
        if chart_type == "Auto":
            chart = auto_visualize(df, current_query_result['natural_query'])
            
        elif chart_type == "Bar":
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                chart = create_bar_chart(df, categorical_cols[0], numeric_cols[0], 
                                        title=f"{numeric_cols[0]} by {categorical_cols[0]}")
            else:
                return None, "❌ 바 차트를 생성하려면 범주형 및 숫자형 열이 필요합니다."
                
        elif chart_type == "Line":
            if len(numeric_cols) >= 1:
                x_col = categorical_cols[0] if categorical_cols else df.columns[0]
                chart = create_line_chart(df, x_col, numeric_cols[0], 
                                         title=f"{numeric_cols[0]} over {x_col}")
            else:
                return None, "❌ 라인 차트를 생성하려면 숫자형 열이 필요합니다."
                
        elif chart_type == "Pie":
            if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
                chart = create_pie_chart(df, categorical_cols[0], numeric_cols[0], 
                                        title=f"{numeric_cols[0]} distribution")
            else:
                return None, "❌ 파이 차트를 생성하려면 범주형 및 숫자형 열이 필요합니다."
                
        elif chart_type == "Scatter":
            if len(numeric_cols) >= 2:
                color = categorical_cols[0] if categorical_cols else None
                chart = create_scatter_plot(df, numeric_cols[0], numeric_cols[1], 
                                           color_col=color,
                                           title=f"{numeric_cols[1]} vs {numeric_cols[0]}")
            else:
                return None, "❌ 스캐터 차트를 생성하려면 2개 이상의 숫자형 열이 필요합니다."
        
        # Store chart in global state
        current_query_result['chart'] = chart
        
        if isinstance(chart, pd.DataFrame):
            return None, "ℹ️ 테이블 형태로 표시됩니다."
        
        return chart, "✅ 차트 생성 완료"
        
    except Exception as e:
        logger.error(f"차트 생성 실패: {e}")
        return None, f"❌ 차트 생성 실패\n오류: {str(e)}"


def get_query_history() -> Tuple[Any, str]:
    """
    쿼리 히스토리 조회 함수
    
    Returns:
        (히스토리 DataFrame, 통계 메시지)
    """
    try:
        db = DatabaseConnection()
        
        # Get recent history
        query = """
        SELECT 
            query_id,
            natural_language_query,
            generated_sql,
            execution_success,
            execution_time_ms,
            result_count,
            created_at
        FROM query_history
        ORDER BY created_at DESC
        LIMIT 50
        """
        df = db.execute_query_df(query)
        
        if df.empty:
            return None, "📝 히스토리가 없습니다."
        
        # Calculate statistics
        total_queries = len(df)
        successful_queries = df['execution_success'].sum()
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        avg_time = df['execution_time_ms'].mean()
        
        stats = f"📊 통계\n"
        stats += f"총 쿼리 수: {total_queries}개\n"
        stats += f"성공한 쿼리: {successful_queries}개\n"
        stats += f"성공률: {success_rate:.1f}%\n"
        stats += f"평균 실행 시간: {avg_time:.1f}ms"
        
        # Format DataFrame for display
        display_df = df.copy()
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['execution_success'] = display_df['execution_success'].map({True: '✅', False: '❌'})
        
        # Truncate long queries
        display_df['natural_language_query'] = display_df['natural_language_query'].str[:50] + '...'
        display_df['generated_sql'] = display_df['generated_sql'].str[:50] + '...'
        
        return display_df, stats
        
    except Exception as e:
        logger.error(f"히스토리 조회 실패: {e}")
        return None, f"❌ 히스토리 조회 실패\n오류: {str(e)}"


def upload_document(file, category: str) -> str:
    """
    문서 업로드 함수
    
    Args:
        file: 업로드된 파일
        category: 문서 카테고리
    
    Returns:
        상태 메시지
    """
    if file is None:
        return "❌ 파일을 선택해주세요."
    
    if not category.strip():
        category = "general"
    
    try:
        # Get file path
        file_path = file.name
        file_name = os.path.basename(file_path)
        
        # Load document
        loader = DocumentLoader()
        documents = loader.load(file_path)
        
        if not documents:
            return "❌ 문서를 읽을 수 없습니다."
        
        # Split into chunks
        chunked_docs = split_documents(documents, chunk_size=500, chunk_overlap=50)
        
        # Store each chunk with embeddings
        db = DatabaseConnection()
        stored_count = 0
        
        for i, doc in enumerate(chunked_docs):
            try:
                metadata = doc.metadata.copy()
                metadata['category'] = category
                metadata['chunk_index'] = i
                metadata['total_chunks'] = len(chunked_docs)
                
                title = f"{file_name} - Part {i+1}/{len(chunked_docs)}"
                
                store_document_with_embedding(
                    db,
                    title=title,
                    content=doc.page_content,
                    doc_type=metadata.get('type', 'unknown'),
                    metadata=metadata
                )
                stored_count += 1
                
            except Exception as chunk_error:
                logger.warning(f"청크 {i} 저장 실패 (건너뜀): {chunk_error}")
                continue
        
        return f"✅ 업로드 성공\n파일: {file_name}\n카테고리: {category}\n청크: {stored_count}개 저장됨"
        
    except Exception as e:
        logger.error(f"문서 업로드 실패: {e}")
        return f"❌ 업로드 실패\n오류: {str(e)}"


def create_demo():
    """
    Gradio 데모 생성 함수
    
    Returns:
        Gradio Blocks 객체
    """
    
    with gr.Blocks(title="Text2SQL Lab", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🔬 Text2SQL Lab
            
            자연어로 SQL 쿼리를 생성하고 실행하는 AI 기반 데이터 분석 플랫폼
            """
        )
        
        with gr.Tabs():
            # Tab 1: Text2SQL 실행
            with gr.Tab("📝 Text2SQL 실행"):
                gr.Markdown("### 자연어 질의를 SQL로 변환하고 실행합니다")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        query_input = gr.Textbox(
                            label="자연어 질의",
                            placeholder="예: 급여가 5000000원 이상인 직원들을 보여줘",
                            lines=3
                        )
                    
                    with gr.Column(scale=1):
                        use_rag = gr.Checkbox(
                            label="RAG 사용",
                            value=True,
                            info="문서 검색으로 컨텍스트 강화"
                        )
                        model_dropdown = gr.Dropdown(
                            label="LLM 모델",
                            choices=["llama2", "llama3", "mistral", "codellama"],
                            value="llama2",
                            info="사용할 LLM 모델 선택"
                        )
                        execute_btn = gr.Button("🚀 실행", variant="primary", size="lg")
                
                with gr.Row():
                    with gr.Column():
                        sql_output = gr.Code(
                            label="생성된 SQL",
                            language="sql",
                            lines=10
                        )
                    
                    with gr.Column():
                        status_output = gr.Textbox(
                            label="실행 상태",
                            lines=10
                        )
                
                results_output = gr.Dataframe(
                    label="실행 결과",
                    wrap=True,
                    interactive=False
                )
                
                # Event handler
                execute_btn.click(
                    fn=execute_text2sql,
                    inputs=[query_input, use_rag, model_dropdown],
                    outputs=[sql_output, results_output, status_output]
                )
                
                # Examples
                gr.Examples(
                    examples=[
                        ["급여가 6000000원 이상인 직원들을 보여줘", True, "llama2"],
                        ["부서별 평균 급여를 알려줘", True, "llama2"],
                        ["진행 중인 프로젝트와 담당 부서를 보여줘", True, "llama2"],
                        ["지역별 총 매출을 내림차순으로 정렬해줘", True, "llama2"],
                        ["Engineering 부서의 직원 수는?", False, "mistral"],
                    ],
                    inputs=[query_input, use_rag, model_dropdown],
                )
            
            # Tab 2: 차트 생성
            with gr.Tab("📈 차트 생성"):
                gr.Markdown("### 쿼리 결과를 시각화합니다")
                gr.Markdown("*먼저 Text2SQL 탭에서 쿼리를 실행해주세요*")
                
                with gr.Row():
                    chart_type = gr.Radio(
                        label="차트 타입",
                        choices=["Auto", "Bar", "Line", "Pie", "Scatter"],
                        value="Auto",
                        info="자동 선택 또는 수동 선택"
                    )
                    
                with gr.Row():
                    generate_chart_btn = gr.Button("📊 차트 생성", variant="primary")
                
                chart_status = gr.Textbox(
                    label="차트 상태",
                    lines=2
                )
                
                chart_output = gr.Plot(label="차트")
                
                # Event handler
                generate_chart_btn.click(
                    fn=generate_chart,
                    inputs=[chart_type],
                    outputs=[chart_output, chart_status]
                )
            
            # Tab 3: 히스토리
            with gr.Tab("📜 히스토리"):
                gr.Markdown("### 최근 쿼리 실행 기록을 확인합니다")
                
                with gr.Row():
                    refresh_btn = gr.Button("🔄 새로고침", variant="secondary")
                
                history_stats = gr.Textbox(
                    label="통계",
                    lines=5
                )
                
                history_output = gr.Dataframe(
                    label="쿼리 히스토리 (최근 50개)",
                    wrap=True,
                    interactive=False
                )
                
                # Event handler
                refresh_btn.click(
                    fn=get_query_history,
                    inputs=[],
                    outputs=[history_output, history_stats]
                )
                
                # Load on tab open
                demo.load(
                    fn=get_query_history,
                    inputs=[],
                    outputs=[history_output, history_stats]
                )
            
            # Tab 4: 문서 업로드
            with gr.Tab("📄 문서 업로드"):
                gr.Markdown("### 문서를 업로드하여 RAG 데이터베이스에 추가합니다")
                gr.Markdown("지원 형식: PDF, Word (docx), Excel (xlsx), Text (txt)")
                
                with gr.Row():
                    with gr.Column():
                        file_upload = gr.File(
                            label="파일 업로드",
                            file_types=[".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"],
                            type="filepath"
                        )
                        
                        category_input = gr.Textbox(
                            label="카테고리",
                            placeholder="예: 회사규정, 기술문서, 데이터사전 등",
                            value="general"
                        )
                        
                        upload_btn = gr.Button("📤 업로드", variant="primary")
                    
                    with gr.Column():
                        upload_status = gr.Textbox(
                            label="업로드 상태",
                            lines=10
                        )
                
                # Event handler
                upload_btn.click(
                    fn=upload_document,
                    inputs=[file_upload, category_input],
                    outputs=[upload_status]
                )
                
                gr.Markdown(
                    """
                    ### 💡 사용 팁
                    
                    - 업로드된 문서는 자동으로 청크로 분할되어 임베딩됩니다
                    - RAG를 활성화하면 쿼리 생성 시 관련 문서를 자동으로 검색합니다
                    - 카테고리를 지정하여 문서를 체계적으로 관리할 수 있습니다
                    - 대용량 문서는 처리 시간이 걸릴 수 있습니다
                    """
                )
        
        # Footer
        gr.Markdown(
            """
            ---
            
            **Text2SQL Lab** | Powered by LangChain, Ollama, PostgreSQL & Gradio
            
            © 2024 | 로컬 환경에서 안전하게 실행됩니다
            """
        )
    
    return demo


def main():
    """메인 함수"""
    logger.info("Text2SQL Lab Gradio UI 시작 중...")
    
    # Check database connection
    try:
        db = DatabaseConnection()
        tables = db.get_all_tables()
        logger.info(f"데이터베이스 연결 성공: {len(tables)}개 테이블 발견")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        logger.warning("계속 진행하지만 기능이 제한될 수 있습니다.")
    
    # Create and launch demo
    demo = create_demo()
    
    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
