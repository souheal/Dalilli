from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    JSON = "json"


class EmbeddingModel(str, Enum):
    BGE_M3 = "BAAI/bge-m3"
    E5_MULTILINGUAL = "intfloat/multilingual-e5-large"


class LLMModel(str, Enum):
    LLAMA3 = "llama3"
    LLAMA3_1 = "llama3.1"
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"
    GEMMA = "gemma"
    PHI3 = "phi3"


# Request Models
class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    num_chunks: int
    collection: str
    metadata: Dict[str, Any]
    uploaded_at: datetime


class ChatRequest(BaseModel):
    query: str
    collection: Optional[str] = None
    session_id: Optional[str] = None
    embedding_model: str = "BAAI/bge-m3"
    llm_model: str = "llama3"
    temperature: float = 0.1
    max_tokens: int = 2048
    bm25_weight: float = 0.3
    semantic_weight: float = 0.7
    top_k: int = 5
    relevance_threshold: float = 0.1
    enable_reranking: bool = True
    enable_query_rewriting: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    rewritten_query: Optional[str] = None
    processing_time: float


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    name: str
    description: Optional[str]
    document_count: int
    created_at: datetime


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    collection: str
    num_chunks: int
    size_bytes: int
    uploaded_at: datetime
    metadata: Dict[str, Any]


class DatabaseStats(BaseModel):
    total_documents: int
    total_chunks: int
    collections: List[str]
    storage_size_mb: float


class RetrievalSettings(BaseModel):
    bm25_weight: float = Field(0.3, ge=0.0, le=1.0)
    semantic_weight: float = Field(0.7, ge=0.0, le=1.0)
    top_k: int = Field(5, ge=1, le=20)
    relevance_threshold: float = Field(0.5, ge=0.0, le=1.0)
    enable_reranking: bool = True
    enable_query_rewriting: bool = True


class ChunkingSettings(BaseModel):
    chunk_size: int = Field(800, ge=100, le=2000)
    chunk_overlap: int = Field(200, ge=0, le=500)
    enable_semantic_chunking: bool = True


class LLMSettings(BaseModel):
    model: str = "llama3"
    temperature: float = Field(0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(2048, ge=256, le=8192)
