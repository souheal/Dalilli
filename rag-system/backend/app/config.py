from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "RAG Document Q&A System"
    debug: bool = True

    # AI Mode - set to False to run without Ollama/LLM
    enable_llm: bool = True
    enable_reranking: bool = False

    # Paths - use absolute paths to avoid issues with working directory changes
    data_dir: str = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data"))
    chroma_persist_dir: str = os.path.join(data_dir, "chroma_db")
    upload_dir: str = os.path.join(data_dir, "uploads")
    database_path: str = os.path.join(data_dir, "app.db")

    # Local model paths
    local_models_dir: str = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "bg"))
    local_model_paths: dict = {
        "BAAI/bge-m3": os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "bg")),
            "bge-m3"
        )
    }

    # Embedding Models - using bge-m3 as default
    default_embedding_model: str = "BAAI/bge-m3"
    embedding_models: list = ["BAAI/bge-m3"]

    # LLM Settings
    ollama_base_url: str = "http://localhost:11434"
    default_llm_model: str = "llama3.1"
    available_llm_models: list = ["llama3.1"]
    default_temperature: float = 0.1
    default_max_tokens: int = 2048

    # Chunking Settings
    default_chunk_size: int = 800
    default_chunk_overlap: int = 200
    enable_semantic_chunking: bool = True

    # Search Settings
    bm25_weight: float = 0.15
    semantic_weight: float = 0.85
    top_k_results: int = 5
    relevance_threshold: float = 0.3
    enable_query_rewriting: bool = False

    # OCR Settings
    enable_ocr: bool = False
    tesseract_path: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)
os.makedirs(settings.upload_dir, exist_ok=True)
