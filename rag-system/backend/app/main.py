from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import documents, chat, collections, models, llm, ingestion
from app.services.vector_store import vector_store
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Initialize SQLite database (creates tables if they don't exist)
    init_db()
    # Initialize vector store for RAG
    vector_store.initialize()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    description="Intelligent document retrieval and Q&A system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections"])

# New Ollama integration routers
# /api/models - List available Ollama models
# /api/llm/chat - Simple direct chat without RAG
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(llm.router, prefix="/api/llm/chat", tags=["LLM"])

# Document ingestion with SQLite persistence
# /api/ingest/upload - Upload documents with OCR option
# /api/ingest/documents - List/get documents from database
app.include_router(ingestion.router, prefix="/api/ingest", tags=["Ingestion"])


@app.get("/")
async def root():
    return {"message": "RAG Document Q&A System API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    from app.services.vector_store import vector_store
    return vector_store.get_stats()


@app.get("/api/settings/embedding-models")
async def get_embedding_models():
    """Get available embedding models"""
    return {"models": settings.embedding_models}


@app.get("/api/settings/llm-models")
async def get_llm_models():
    """Get available LLM models"""
    return {"models": settings.available_llm_models}
