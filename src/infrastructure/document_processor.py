"""
PDF Document Processor Implementation
"""

import fitz  # PyMuPDF
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime

from ..domain.services import DocumentProcessorService
from ..domain.entities import DocumentChunk, GaitParameter, DocumentType, DiseaseCategory
from ..domain.value_objects import PaperId

logger = logging.getLogger(__name__)


class PDFDocumentProcessor(DocumentProcessorService):
    """PDF document processing implementation"""
    
    # Gait parameter keywords for detection
    GAIT_KEYWORDS = [
        # English terms
        'speed', 'velocity', 'cadence', 'step length', 'stride length',
        'step width', 'step time', 'stride time', 'double support',
        'single support', 'stance', 'swing', 'asymmetry', 'gait',
        'walking speed', 'gait speed', 'spatiotemporal', 'kinematic',
        'kinetic', 'ground reaction force', 'joint angle', 'rom',
        
        # Korean terms
        '속도', '보행', '보폭', '걸음', '보행속도', '걸음걸이',
        '보행패턴', '보행분석', '관절각도', '지면반력'
    ]
    
    # Disease category patterns
    DISEASE_PATTERNS = {
        DiseaseCategory.STROKE: [
            'stroke', 'hemiplegia', 'hemiparesis', 'cerebral', 'cva',
            '뇌졸중', '편마비', '뇌경색', '뇌출혈'
        ],
        DiseaseCategory.PARKINSON: [
            'parkinson', "parkinson's", 'parkinsonian', 'pd',
            '파킨슨', '파킨슨병'
        ],
        DiseaseCategory.ARTHRITIS: [
            'arthritis', 'osteoarthritis', 'rheumatoid', 'oa', 'ra',
            '관절염', '류마티스', '퇴행성관절염'
        ],
        DiseaseCategory.SCOLIOSIS: [
            'scoliosis', 'spinal', 'spine deformity',
            '측만증', '척추측만', '척추변형'
        ]
    }
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        max_pages: Optional[int] = None
    ):
        """
        Initialize PDF processor
        
        Args:
            chunk_size: Size of text chunks (in words)
            chunk_overlap: Overlap between chunks (in words)
            max_pages: Maximum pages to process (None for all)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_pages = max_pages
    
    async def extract_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF file"""
        doc = fitz.open(str(file_path))
        
        result = {
            "text_pages": [],
            "tables": [],
            "metadata": {
                "filename": file_path.name,
                "total_pages": len(doc),
                "file_path": str(file_path),
                "extracted_at": datetime.now().isoformat()
            }
        }
        
        try:
            # 처리할 페이지 수 결정 (max_pages가 설정되면 제한)
            pages_to_process = min(len(doc), self.max_pages) if self.max_pages else len(doc)
            
            for page_num in range(pages_to_process):
                page = doc[page_num]
                
                # PDF 페이지에서 텍스트 추출
                text = page.get_text()
                if text.strip():
                    result["text_pages"].append({
                        "page_number": page_num + 1,
                        "content": text
                    })
                
                # Extract tables
                tables = page.find_tables()
                for table_idx, table in enumerate(tables):
                    try:
                        df = table.to_pandas()
                        table_text = df.to_string()
                        
                        # Check for gait parameters
                        has_gait_params = self._contains_gait_keywords(table_text)
                        
                        table_data = {
                            "page_number": page_num + 1,
                            "table_index": table_idx,
                            "content": table_text,
                            "dataframe": df,
                            "has_gait_params": has_gait_params
                        }
                        
                        result["tables"].append(table_data)
                        
                    except Exception as e:
                        logger.debug(f"Error processing table {table_idx} on page {page_num}: {e}")
                        continue
        
        finally:
            doc.close()
        
        # Extract additional metadata
        result["metadata"]["disease_category"] = self._detect_disease_category(result)
        
        logger.info(
            f"Extracted {len(result['text_pages'])} text pages and "
            f"{len(result['tables'])} tables from {file_path.name}"
        )
        
        return result
    
    async def create_chunks(
        self,
        content: Dict[str, Any],
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Create chunks from extracted content"""
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        chunks = []
        chunk_index = 0
        
        # Create paper ID from full file path for uniqueness
        # Use relative path from data directory if possible
        file_path = content["metadata"].get("file_path", content["metadata"]["filename"])
        if "data/" in file_path:
            # Extract relative path from data directory
            paper_id = file_path.split("data/", 1)[1] if "data/" in file_path else file_path
        else:
            paper_id = file_path
        
        # Process text pages
        for page_data in content["text_pages"]:
            page_chunks = self._chunk_text(
                page_data["content"],
                chunk_size,
                overlap
            )
            
            for chunk_text in page_chunks:
                # Extract gait parameters
                gait_params = await self.extract_gait_parameters(chunk_text)
                
                chunk = DocumentChunk(
                    chunk_id=f"{paper_id}::chunk_{chunk_index}",
                    document_id=paper_id,
                    content=chunk_text,
                    page_number=page_data["page_number"],
                    chunk_index=chunk_index,
                    chunk_type=DocumentType.TEXT,
                    metadata={
                        "word_count": len(chunk_text.split())
                    },
                    gait_parameters=gait_params
                )
                
                chunks.append(chunk)
                chunk_index += 1
        
        # Process tables
        for table_data in content["tables"]:
            # Extract gait parameters from table
            gait_params = []
            if table_data["has_gait_params"] and "dataframe" in table_data:
                gait_params = self._extract_table_gait_params(table_data["dataframe"])
            
            chunk = DocumentChunk(
                chunk_id=f"{paper_id}::chunk_{chunk_index}",
                document_id=paper_id,
                content=table_data["content"],
                page_number=table_data["page_number"],
                chunk_index=chunk_index,
                chunk_type=DocumentType.TABLE,
                metadata={
                    "table_index": table_data["table_index"]
                },
                gait_parameters=gait_params
            )
            
            chunks.append(chunk)
            chunk_index += 1
        
        logger.info(f"Created {len(chunks)} chunks from content")
        return chunks
    
    async def extract_gait_parameters(self, text: str) -> List[GaitParameter]:
        """Extract gait parameters from text"""
        parameters = []
        text_lower = text.lower()
        
        # Pattern for finding numeric values with units
        patterns = [
            # Pattern: "speed: 1.2 m/s" or "speed = 1.2m/s"
            r'(\w+(?:\s+\w+)?)\s*[:=]\s*([\d.]+)\s*([a-zA-Z/]+)?',
            # Pattern: "walking speed of 1.2 m/s"
            r'(\w+(?:\s+\w+)?)\s+of\s+([\d.]+)\s*([a-zA-Z/]+)?',
            # Pattern: "1.2 m/s walking speed"
            r'([\d.]+)\s*([a-zA-Z/]+)?\s+(\w+(?:\s+\w+)?)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                # Check if any group contains gait keywords
                param_name = None
                value = None
                unit = None
                
                for i, group in enumerate(groups):
                    if group and any(kw in str(group).lower() for kw in self.GAIT_KEYWORDS):
                        # Found a gait keyword
                        if i == 0 or i == 2:  # Parameter name position
                            param_name = group
                            # Find the numeric value
                            for g in groups:
                                if g and re.match(r'^[\d.]+$', g) and g != '.':
                                    try:
                                        value = float(g)
                                        break
                                    except ValueError:
                                        continue
                            # Find the unit
                            for g in groups:
                                if g and re.match(r'^[a-zA-Z/]+$', g):
                                    unit = g
                                    break
                
                if param_name and value is not None:
                    try:
                        parameter = GaitParameter(
                            name=param_name.strip(),
                            value=value,
                            unit=unit.strip() if unit else None
                        )
                        parameters.append(parameter)
                    except ValueError:
                        continue
        
        return parameters
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from document"""
        metadata = {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_path": str(file_path),
            "extracted_at": datetime.now().isoformat()
        }
        
        # Try to extract title, authors, year from filename or first page
        # Pattern: "Author Year.pdf" or "Author_Year.pdf"
        filename_pattern = r'^([A-Za-z]+)[\s_](\d{4})\.pdf$'
        match = re.match(filename_pattern, file_path.name)
        
        if match:
            metadata["author_hint"] = match.group(1)
            metadata["year_hint"] = int(match.group(2))
        
        return metadata
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        
        step = max(1, chunk_size - overlap)
        
        for i in range(0, len(words), step):
            chunk_words = words[i:i + chunk_size]
            if chunk_words:
                chunk = ' '.join(chunk_words)
                chunks.append(chunk)
        
        return chunks
    
    def _contains_gait_keywords(self, text: str) -> bool:
        """Check if text contains gait-related keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.GAIT_KEYWORDS)
    
    def _detect_disease_category(self, content: Dict[str, Any]) -> DiseaseCategory:
        """Detect disease category from content"""
        # Combine all text for analysis
        all_text = ""
        for page in content.get("text_pages", []):
            all_text += page["content"] + " "
        
        all_text_lower = all_text.lower()
        
        # Count matches for each category
        category_scores = {}
        
        for category, keywords in self.DISEASE_PATTERNS.items():
            score = sum(1 for keyword in keywords if keyword in all_text_lower)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return DiseaseCategory.OTHER
    
    def _extract_table_gait_params(self, df: pd.DataFrame) -> List[GaitParameter]:
        """Extract gait parameters from table DataFrame"""
        parameters = []
        
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Check if column name contains gait keywords
            for keyword in self.GAIT_KEYWORDS:
                if keyword in col_lower:
                    # Try to extract numeric values
                    numeric_vals = pd.to_numeric(df[col], errors='coerce')
                    numeric_vals = numeric_vals.dropna()
                    
                    if not numeric_vals.empty:
                        # Create parameter with statistics
                        parameter = GaitParameter(
                            name=str(col),
                            value=float(numeric_vals.mean()),
                            mean=float(numeric_vals.mean()),
                            std=float(numeric_vals.std()) if len(numeric_vals) > 1 else None
                        )
                        parameters.append(parameter)
                    break
        
        return parameters