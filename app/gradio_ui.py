"""
Gradio Web UI for Text2SQL Lab
사용자 친화적인 웹 인터페이스로 Text2SQL과 차트 생성을 테스트할 수 있습니다.
"""
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import gradio as gr
import plotly.express as px
import plotly.graph_objects as go

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.db_utils import DatabaseConnection
from src.utils.text2sql_utils import Text2SQLGenerator
from src.utils.viz_utils import auto_visualize, infer_chart_type


class Text2SQLApp:
    """Gradio application for Text2SQL"""
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.text2sql = None  # Initialized when model is selected
        self.last_result = None
        self.last_query = None
        self.query_history = []
        
    def initialize_llm(self, model_name: str) -> str:
        """Initialize LLM with selected model"""
        try:
            self.text2sql = Text2SQLGenerator(model_name=model_name)
            return f"✓ LLM 초기화 완료: {model_name}"
        except Exception as e:
            return f"✗ LLM 초기화 실패: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            import requests
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return ["llama2", "mistral", "codellama"]
        except:
            return ["llama2", "mistral", "codellama"]
    
    def get_schema_context(self) -> str:
        """Get database schema context"""
        try:
            tables = self.db.get_all_tables()
            schema_info = "Database Schema:\n\n"
            
            for table in tables:
                schema_df = self.db.get_table_schema(table)
                schema_info += f"Table: {table}\n"
                schema_info += "Columns:\n"
                for _, row in schema_df.iterrows():
                    schema_info += f"  - {row['column_name']} ({row['data_type']})\n"
                schema_info += "\n"
            
            return schema_info
        except Exception as e:
            return f"Failed to get schema: {str(e)}"
    
    def execute_text2sql(
        self, 
        natural_query: str,
        use_rag: bool = False,
        few_shot_count: int = 3
    ) -> Tuple[str, str, str, str]:
        """
        Execute Text2SQL query
        
        Returns:
            Tuple of (sql_query, result_table, execution_info, status)
        """
        if not natural_query.strip():
            return "", "", "질의를 입력해주세요.", "⚠️ 입력 필요"
        
        if self.text2sql is None:
            return "", "", "먼저 LLM 모델을 선택해주세요.", "✗ 모델 미선택"
        
        start_time = time.time()
        
        try:
            # Get schema context
            schema_context = self.get_schema_context()
            
            # Get few-shot examples if requested
            few_shot_examples = ""
            if few_shot_count > 0:
                # TODO: Implement few-shot example retrieval from database
                few_shot_examples = """
Example 1:
Natural Language: Show all employees
SQL: SELECT * FROM employees;

Example 2:
Natural Language: What is the average salary by department?
SQL: SELECT d.department_name, AVG(e.salary) as avg_salary 
     FROM employees e 
     JOIN departments d ON e.department_id = d.department_id 
     GROUP BY d.department_name;
"""
            
            # Generate SQL
            sql_query = self.text2sql.generate_sql(
                natural_query,
                schema_context,
                few_shot_examples
            )
            
            # Execute SQL
            result_df = self.db.execute_query_df(sql_query)
            execution_time = int((time.time() - start_time) * 1000)
            
            # Store for later use
            self.last_result = result_df
            self.last_query = sql_query
            
            # Log query
            self.db.log_query(
                natural_query,
                sql_query,
                success=True,
                execution_time=execution_time,
                result_count=len(result_df)
            )
            
            # Add to history
            self.query_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'query': natural_query,
                'sql': sql_query,
                'success': True,
                'rows': len(result_df),
                'time_ms': execution_time
            })
            
            # Format execution info
            exec_info = f"""
실행 시간: {execution_time}ms
결과 행 수: {len(result_df)}
결과 열 수: {len(result_df.columns)}
"""
            
            return sql_query, result_df, exec_info, "✓ 성공"
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            
            # Log failed query
            if 'sql_query' in locals():
                self.db.log_query(
                    natural_query,
                    sql_query,
                    success=False,
                    execution_time=execution_time,
                    error_message=error_msg
                )
                
                # Add to history
                self.query_history.append({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'query': natural_query,
                    'sql': sql_query if 'sql_query' in locals() else '',
                    'success': False,
                    'rows': 0,
                    'time_ms': execution_time,
                    'error': error_msg
                })
            
            exec_info = f"실행 시간: {execution_time}ms\n오류: {error_msg}"
            return sql_query if 'sql_query' in locals() else "", "", exec_info, "✗ 실패"
    
    def generate_chart(
        self,
        chart_type: str = "auto"
    ) -> Tuple[Any, str]:
        """
        Generate chart from last query result
        
        Returns:
            Tuple of (plotly_figure, status_message)
        """
        if self.last_result is None or self.last_result.empty:
            return None, "⚠️ 먼저 쿼리를 실행해주세요."
        
        try:
            if chart_type == "auto":
                # Use auto visualization
                fig = auto_visualize(self.last_result)
            else:
                # Manual chart type selection
                df = self.last_result
                
                if len(df.columns) < 2:
                    return None, "✗ 차트 생성을 위해 최소 2개의 컬럼이 필요합니다."
                
                x_col = df.columns[0]
                y_col = df.columns[1]
                
                if chart_type == "bar":
                    fig = px.bar(df, x=x_col, y=y_col, title="Bar Chart")
                elif chart_type == "line":
                    fig = px.line(df, x=x_col, y=y_col, title="Line Chart")
                elif chart_type == "scatter":
                    fig = px.scatter(df, x=x_col, y=y_col, title="Scatter Plot")
                elif chart_type == "pie":
                    # For pie chart, we need to aggregate if necessary
                    if len(df) > 20:
                        df = df.head(20)
                    fig = px.pie(df, names=x_col, values=y_col, title="Pie Chart")
                else:
                    fig = px.bar(df, x=x_col, y=y_col)
            
            return fig, "✓ 차트 생성 완료"
            
        except Exception as e:
            return None, f"✗ 차트 생성 실패: {str(e)}"
    
    def get_history_dataframe(self) -> pd.DataFrame:
        """Get query history as DataFrame"""
        if not self.query_history:
            return pd.DataFrame(columns=['시간', '질의', 'SQL', '상태', '행 수', '실행시간(ms)'])
        
        history_data = []
        for h in self.query_history[-20:]:  # Last 20 queries
            history_data.append({
                '시간': h['timestamp'],
                '질의': h['query'][:50] + '...' if len(h['query']) > 50 else h['query'],
                'SQL': h['sql'][:50] + '...' if len(h['sql']) > 50 else h['sql'],
                '상태': '✓' if h['success'] else '✗',
                '행 수': h['rows'],
                '실행시간(ms)': h['time_ms']
            })
        
        return pd.DataFrame(history_data)
    
    def get_statistics(self) -> str:
        """Get statistics summary"""
        if not self.query_history:
            return "아직 실행된 쿼리가 없습니다."
        
        total = len(self.query_history)
        success = sum(1 for h in self.query_history if h['success'])
        failed = total - success
        avg_time = sum(h['time_ms'] for h in self.query_history) / total
        
        return f"""
### 통계 요약

- **총 쿼리 수**: {total}
- **성공**: {success} ({success/total*100:.1f}%)
- **실패**: {failed} ({failed/total*100:.1f}%)
- **평균 실행 시간**: {avg_time:.1f}ms
"""


def create_ui():
    """Create Gradio UI"""
    app = Text2SQLApp()
    
    with gr.Blocks(title="Text2SQL Lab", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🔬 Text2SQL Lab - 웹 인터페이스
        
        자연어를 SQL로 변환하고 결과를 시각화하는 인터랙티브 웹 인터페이스입니다.
        """)
        
        with gr.Tabs():
            # Tab 1: Text2SQL Execution
            with gr.Tab("📝 Text2SQL 실행"):
                gr.Markdown("### 자연어 질의를 SQL로 변환하고 실행합니다")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        natural_query_input = gr.Textbox(
                            label="자연어 질의",
                            placeholder="예: 급여가 6000000보다 큰 모든 직원을 보여주세요",
                            lines=3
                        )
                        
                        with gr.Row():
                            execute_btn = gr.Button("🚀 실행", variant="primary")
                            clear_btn = gr.Button("🗑️ 지우기")
                    
                    with gr.Column(scale=1):
                        status_output = gr.Textbox(
                            label="상태",
                            value="준비됨",
                            interactive=False
                        )
                        exec_info_output = gr.Textbox(
                            label="실행 정보",
                            lines=4,
                            interactive=False
                        )
                
                sql_output = gr.Textbox(
                    label="생성된 SQL 쿼리",
                    lines=5,
                    interactive=False
                )
                
                result_output = gr.Dataframe(
                    label="실행 결과",
                    interactive=False
                )
                
                # Example queries
                gr.Markdown("### 예제 질의")
                example_queries = [
                    ["모든 직원을 보여주세요"],
                    ["부서별 평균 급여는?"],
                    ["급여가 가장 높은 5명의 직원은?"],
                    ["각 부서의 직원 수를 세어주세요"],
                    ["마케팅 부서의 총 급여는?"]
                ]
                gr.Examples(
                    examples=example_queries,
                    inputs=[natural_query_input]
                )
            
            # Tab 2: Chart Generation
            with gr.Tab("📊 차트 생성"):
                gr.Markdown("### 쿼리 결과를 시각화합니다")
                
                with gr.Row():
                    chart_type_input = gr.Radio(
                        choices=["auto", "bar", "line", "pie", "scatter"],
                        value="auto",
                        label="차트 타입"
                    )
                    generate_chart_btn = gr.Button("📈 차트 생성", variant="primary")
                
                chart_status_output = gr.Textbox(
                    label="상태",
                    interactive=False
                )
                
                chart_output = gr.Plot(label="차트")
                
                gr.Markdown("""
                **참고**: 먼저 'Text2SQL 실행' 탭에서 쿼리를 실행한 후 차트를 생성할 수 있습니다.
                
                - **auto**: 데이터에 맞는 차트를 자동 선택
                - **bar**: 막대 그래프
                - **line**: 선 그래프
                - **pie**: 원형 그래프
                - **scatter**: 산점도
                """)
            
            # Tab 3: Settings
            with gr.Tab("⚙️ 설정"):
                gr.Markdown("### LLM 및 데이터베이스 설정")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### LLM 모델 설정")
                        
                        model_dropdown = gr.Dropdown(
                            choices=app.get_available_models(),
                            value="llama2",
                            label="LLM 모델 선택",
                            interactive=True
                        )
                        
                        init_model_btn = gr.Button("🔧 모델 초기화", variant="primary")
                        model_status_output = gr.Textbox(
                            label="모델 상태",
                            interactive=False
                        )
                        
                        gr.Markdown("#### RAG 설정")
                        use_rag_checkbox = gr.Checkbox(
                            label="RAG 활성화 (문서 검색 사용)",
                            value=False
                        )
                        
                        few_shot_slider = gr.Slider(
                            minimum=0,
                            maximum=10,
                            value=3,
                            step=1,
                            label="Few-shot 예제 개수"
                        )
                    
                    with gr.Column():
                        gr.Markdown("#### 데이터베이스 정보")
                        
                        db_info = f"""
- **호스트**: {app.db.host}
- **포트**: {app.db.port}
- **데이터베이스**: {app.db.database}
- **사용자**: {app.db.user}
                        """
                        gr.Markdown(db_info)
                        
                        gr.Markdown("#### 스키마 정보")
                        schema_output = gr.Textbox(
                            label="데이터베이스 스키마",
                            value=app.get_schema_context(),
                            lines=15,
                            interactive=False
                        )
            
            # Tab 4: History
            with gr.Tab("📜 히스토리"):
                gr.Markdown("### 쿼리 실행 히스토리")
                
                with gr.Row():
                    refresh_history_btn = gr.Button("🔄 새로고침")
                    clear_history_btn = gr.Button("🗑️ 히스토리 지우기")
                
                stats_output = gr.Markdown(value=app.get_statistics())
                
                history_output = gr.Dataframe(
                    value=app.get_history_dataframe(),
                    label="최근 쿼리"
                )
        
        # Event handlers
        execute_btn.click(
            fn=app.execute_text2sql,
            inputs=[natural_query_input],
            outputs=[sql_output, result_output, exec_info_output, status_output]
        )
        
        clear_btn.click(
            fn=lambda: ("", "", "", "준비됨"),
            outputs=[natural_query_input, sql_output, exec_info_output, status_output]
        )
        
        generate_chart_btn.click(
            fn=app.generate_chart,
            inputs=[chart_type_input],
            outputs=[chart_output, chart_status_output]
        )
        
        init_model_btn.click(
            fn=app.initialize_llm,
            inputs=[model_dropdown],
            outputs=[model_status_output]
        )
        
        refresh_history_btn.click(
            fn=lambda: (app.get_history_dataframe(), app.get_statistics()),
            outputs=[history_output, stats_output]
        )
        
        clear_history_btn.click(
            fn=lambda: (app.query_history.clear(), 
                       app.get_history_dataframe(), 
                       app.get_statistics()),
            outputs=[history_output, stats_output]
        )
    
    return demo


def main():
    """Main entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create and launch UI
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main()
