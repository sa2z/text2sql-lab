"""
Document loader for Text2SQL Lab
다양한 형식의 문서를 로드하고 청킹(chunking)하여 임베딩을 생성합니다.
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd


class DocumentChunk:
    """문서 청크를 나타내는 클래스"""
    
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_id: Optional[int] = None
    ):
        self.content = content
        self.metadata = metadata
        self.chunk_id = chunk_id


class DocumentLoader:
    """다양한 형식의 문서를 로드하고 처리"""
    
    def __init__(self):
        self.supported_formats = ['.txt', '.pdf', '.docx', '.xlsx', '.md']
    
    def load_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        문서를 로드하고 청크로 분할
        
        Args:
            file_path: 문서 파일 경로
            metadata: 문서 메타데이터 (제목, 부서, 태그 등)
        
        Returns:
            List of DocumentChunk objects
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 기본 메타데이터 설정
        if metadata is None:
            metadata = {}
        
        metadata.update({
            'filename': path.name,
            'file_type': path.suffix,
            'file_size': path.stat().st_size
        })
        
        # 파일 형식에 따라 로드
        extension = path.suffix.lower()
        
        if extension == '.txt':
            content = self._load_text(file_path)
        elif extension == '.pdf':
            content = self._load_pdf(file_path)
        elif extension == '.docx':
            content = self._load_docx(file_path)
        elif extension == '.xlsx':
            content = self._load_excel(file_path)
        elif extension == '.md':
            content = self._load_text(file_path)  # Markdown as text
        else:
            raise ValueError(f"Unsupported file format: {extension}")
        
        # 청크로 분할
        chunks = self.chunk_text(content, metadata)
        
        return chunks
    
    def _load_text(self, file_path: str) -> str:
        """텍스트 파일 로드"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf(self, file_path: str) -> str:
        """PDF 파일 로드"""
        try:
            import pdfplumber
            
            text = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            return '\n\n'.join(text)
            
        except ImportError:
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                
                reader = PdfReader(file_path)
                text = []
                
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
                
                return '\n\n'.join(text)
            except ImportError:
                raise ImportError(
                    "PDF support requires pdfplumber or PyPDF2. "
                    "Install with: pip install pdfplumber or pip install PyPDF2"
                )
    
    def _load_docx(self, file_path: str) -> str:
        """Word 문서 로드"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            
            # Include table content
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text for cell in row.cells)
                    if row_text.strip():
                        text.append(row_text)
            
            return '\n\n'.join(text)
            
        except ImportError:
            raise ImportError(
                "DOCX support requires python-docx. "
                "Install with: pip install python-docx"
            )
    
    def _load_excel(self, file_path: str) -> str:
        """Excel 파일 로드"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            text = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Add sheet name as header
                text.append(f"Sheet: {sheet_name}")
                text.append("=" * 50)
                
                # Convert DataFrame to string representation
                text.append(df.to_string(index=False))
                text.append("")  # Empty line between sheets
            
            return '\n'.join(text)
            
        except Exception as e:
            raise Exception(f"Failed to load Excel file: {str(e)}")
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        strategy: str = 'fixed'
    ) -> List[DocumentChunk]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            metadata: 청크 메타데이터
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 오버랩 (문자 수)
            strategy: 청킹 전략 ('fixed', 'paragraph', 'semantic')
        
        Returns:
            List of DocumentChunk objects
        """
        if strategy == 'fixed':
            return self._chunk_fixed(text, metadata, chunk_size, chunk_overlap)
        elif strategy == 'paragraph':
            return self._chunk_paragraph(text, metadata, chunk_size)
        elif strategy == 'semantic':
            return self._chunk_semantic(text, metadata, chunk_size)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def _chunk_fixed(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: int,
        chunk_overlap: int
    ) -> List[DocumentChunk]:
        """고정 크기 청킹"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_strategy': 'fixed',
                    'start_pos': start,
                    'end_pos': end
                })
                
                chunks.append(DocumentChunk(
                    content=chunk_text.strip(),
                    metadata=chunk_metadata,
                    chunk_id=chunk_id
                ))
                
                chunk_id += 1
            
            # Move forward with overlap
            start = end - chunk_overlap
        
        return chunks
    
    def _chunk_paragraph(
        self,
        text: str,
        metadata: Dict[str, Any],
        max_chunk_size: int
    ) -> List[DocumentChunk]:
        """문단 단위 청킹"""
        # Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # If single paragraph exceeds max size, split it
            if para_size > max_chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_strategy': 'paragraph'
                    })
                    
                    chunks.append(DocumentChunk(
                        content='\n\n'.join(current_chunk),
                        metadata=chunk_metadata,
                        chunk_id=chunk_id
                    ))
                    
                    chunk_id += 1
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph into fixed chunks
                fixed_chunks = self._chunk_fixed(
                    para,
                    metadata,
                    max_chunk_size,
                    50
                )
                chunks.extend(fixed_chunks)
                chunk_id += len(fixed_chunks)
                
            # If adding this paragraph exceeds max size, save current chunk
            elif current_size + para_size > max_chunk_size:
                if current_chunk:
                    chunk_metadata = metadata.copy()
                    chunk_metadata.update({
                        'chunk_id': chunk_id,
                        'chunk_strategy': 'paragraph'
                    })
                    
                    chunks.append(DocumentChunk(
                        content='\n\n'.join(current_chunk),
                        metadata=chunk_metadata,
                        chunk_id=chunk_id
                    ))
                    
                    chunk_id += 1
                
                current_chunk = [para]
                current_size = para_size
            
            # Add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_strategy': 'paragraph'
            })
            
            chunks.append(DocumentChunk(
                content='\n\n'.join(current_chunk),
                metadata=chunk_metadata,
                chunk_id=chunk_id
            ))
        
        return chunks
    
    def _chunk_semantic(
        self,
        text: str,
        metadata: Dict[str, Any],
        max_chunk_size: int
    ) -> List[DocumentChunk]:
        """
        의미론적 청킹 (문장 단위로 분할하되 의미를 유지)
        
        Note: This is a simplified version. For production use,
        consider using semantic chunking libraries like LangChain's
        SemanticChunker or similar tools.
        """
        # Split by sentences (simplified)
        import re
        sentences = re.split(r'[.!?]\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_size = len(sentence)
            
            # If adding this sentence exceeds max size, save current chunk
            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    'chunk_id': chunk_id,
                    'chunk_strategy': 'semantic'
                })
                
                chunks.append(DocumentChunk(
                    content='. '.join(current_chunk) + '.',
                    metadata=chunk_metadata,
                    chunk_id=chunk_id
                ))
                
                chunk_id += 1
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                'chunk_id': chunk_id,
                'chunk_strategy': 'semantic'
            })
            
            chunks.append(DocumentChunk(
                content='. '.join(current_chunk) + '.',
                metadata=chunk_metadata,
                chunk_id=chunk_id
            ))
        
        return chunks
    
    def load_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None
    ) -> List[DocumentChunk]:
        """
        디렉토리의 모든 문서를 로드
        
        Args:
            directory_path: 디렉토리 경로
            recursive: 하위 디렉토리 포함 여부
            file_patterns: 파일 패턴 리스트 (예: ['*.pdf', '*.docx'])
        
        Returns:
            List of all DocumentChunks from all documents
        """
        path = Path(directory_path)
        
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory_path}")
        
        all_chunks = []
        
        # Get all files
        if recursive:
            files = path.rglob('*')
        else:
            files = path.glob('*')
        
        # Filter by supported formats
        for file_path in files:
            if file_path.is_file():
                if file_path.suffix.lower() in self.supported_formats:
                    # Apply file patterns if specified
                    if file_patterns:
                        if not any(file_path.match(pattern) for pattern in file_patterns):
                            continue
                    
                    try:
                        # Add directory as metadata
                        metadata = {
                            'directory': str(file_path.parent),
                            'relative_path': str(file_path.relative_to(path))
                        }
                        
                        chunks = self.load_document(str(file_path), metadata)
                        all_chunks.extend(chunks)
                        
                    except Exception as e:
                        print(f"Warning: Failed to load {file_path}: {str(e)}")
                        continue
        
        return all_chunks


def example_usage():
    """사용 예제"""
    loader = DocumentLoader()
    
    # 단일 문서 로드
    chunks = loader.load_document(
        'data/documents/company_policy.pdf',
        metadata={
            'title': 'Company Policy',
            'department': 'HR',
            'tags': ['policy', 'guidelines'],
            'priority': 'high'
        }
    )
    
    print(f"Loaded {len(chunks)} chunks")
    
    # 디렉토리 로드
    all_chunks = loader.load_directory(
        'data/documents',
        recursive=True,
        file_patterns=['*.pdf', '*.docx']
    )
    
    print(f"Loaded {len(all_chunks)} chunks from directory")
    
    # 청킹 전략 비교
    text = "Your long document text here..."
    
    fixed_chunks = loader.chunk_text(text, {}, strategy='fixed', chunk_size=500)
    para_chunks = loader.chunk_text(text, {}, strategy='paragraph', chunk_size=500)
    semantic_chunks = loader.chunk_text(text, {}, strategy='semantic', chunk_size=500)
    
    print(f"Fixed: {len(fixed_chunks)}, Paragraph: {len(para_chunks)}, Semantic: {len(semantic_chunks)}")


if __name__ == "__main__":
    example_usage()
