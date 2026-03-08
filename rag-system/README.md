# RAG Document Q&A System

An intelligent document retrieval system that allows you to upload documents and ask questions to get answers based on your contracts and documents.

## Features

- **Multiple File Support**: PDF, Word (.docx), Excel (.xlsx), and TXT files
- **Hybrid Search**: Combines BM25 (keyword) and semantic search with configurable weights
- **Multiple Embedding Models**: BAAI/bge-m3, E5 Multilingual
- **Multiple LLM Support**: Llama 3, Llama 3.1, Mistral, Mixtral, Gemma, Phi-3 (via Ollama)
- **Configurable Chunking**: Adjustable chunk size and overlap
- **Re-ranking**: Top-K re-ranking for improved relevance
- **Query Rewriting**: Automatic query enhancement
- **OCR Support**: Process scanned documents
- **Collections**: Organize documents into separate collections
- **Metadata Extraction**: Automatic metadata extraction from documents

## Tech Stack

### Backend
- **FastAPI** - REST API framework
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embedding models
- **Ollama** - Local LLM inference
- **LangChain** - LLM orchestration

### Frontend
- **Next.js 14** - React framework
- **Tailwind CSS** - Styling
- **TypeScript** - Type safety
- **Lucide React** - Icons

## Project Structure

```
rag-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── routers/
│   │   │   ├── documents.py
│   │   │   ├── chat.py
│   │   │   └── collections.py
│   │   ├── services/
│   │   │   ├── document_processor.py
│   │   │   ├── embeddings.py
│   │   │   ├── llm_service.py
│   │   │   ├── vector_store.py
│   │   │   ├── search.py
│   │   │   ├── chunking.py
│   │   │   ├── reranker.py
│   │   │   └── ocr.py
│   │   └── utils/
│   │       └── helpers.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Settings.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── DatabaseInfo.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── utils.ts
│   ├── package.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   └── Dockerfile
├── data/
├── docker-compose.yml
└── README.md
```

## Models Used

This project uses **3 types of AI models**, all running locally:

### 1. LLM (Large Language Model) - via Ollama

The main brain that generates answers from retrieved documents.

| Model | Size | Description |
|-------|------|-------------|
| **Llama 3.1** (default) | ~4.7 GB | Meta's latest open-source model, great for Q&A |

**How to add/switch models:**

```bash
# Install any Ollama-supported model
ollama pull llama3.1        # Default model
ollama pull mistral         # Alternative - fast and lightweight
ollama pull mixtral          # Mixture of experts - higher quality
ollama pull gemma2           # Google's open model
ollama pull phi3             # Microsoft's small but capable model

# Verify installed models
ollama list
```

The model is selected **per-request** from the UI - no backend restart needed. Just pull a new model and select it.

### 2. Embedding Model - BAAI/bge-m3

Converts text into vectors for semantic search. Downloaded automatically on first run.

| Model | Size | Description |
|-------|------|-------------|
| **BAAI/bge-m3** | ~2.2 GB | Multilingual embedding model (100+ languages, including Arabic) |

- Stored locally in: `bg/bge-m3/`
- Downloaded automatically from HuggingFace on first run
- To use a pre-downloaded model, place it in the `bg/bge-m3/` directory

### 3. Re-ranker Model (Optional)

Re-ranks search results for better relevance. Disabled by default.

| Model | Size | Description |
|-------|------|-------------|
| **cross-encoder/ms-marco-MiniLM-L-6-v2** | ~80 MB | Fast cross-encoder for result re-ranking |

- Enable in `.env`: `ENABLE_RERANKING=true`
- Downloaded automatically from HuggingFace when enabled

### 4. OCR - Tesseract (Optional)

For processing scanned documents and images. Not an AI model per se, but required for OCR.

- Enable in `.env`: `ENABLE_OCR=true`
- Requires separate installation (see below)

## Prerequisites

- Node.js 18+
- Python 3.10+
- Ollama (for local LLM inference)
- Tesseract OCR (optional, for OCR support)
- Poppler (optional, for PDF OCR)

## Installation

### 1. Install Ollama and Models

```bash
# Install Ollama from https://ollama.ai

# Pull the default model
ollama pull llama3.1

# (Optional) Pull additional models
ollama pull mistral
ollama pull gemma2
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Install Tesseract (Optional - for OCR)

**Windows:**
Download from https://github.com/UB-Mannheim/tesseract/wiki

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## Running the Application

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

Access the application at: http://localhost:3000

## Docker Deployment

```bash
docker-compose up --build
```

Access at: http://localhost:3000

## Configuration

### Retrieval Settings
- **BM25 Weight**: 0.3 (keyword search contribution)
- **Semantic Weight**: 0.7 (vector search contribution)
- **Top-K Results**: 5
- **Relevance Threshold**: 0.5

### Chunking Settings
- **Chunk Size**: 800 tokens
- **Chunk Overlap**: 200 tokens
- **Semantic Chunking**: Enabled

### LLM Settings
- **Temperature**: 0.1
- **Max Tokens**: 2048

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload documents |
| GET | `/api/documents` | List documents |
| DELETE | `/api/documents/{id}` | Delete document |
| POST | `/api/chat/` | Send chat message |
| GET | `/api/collections` | List collections |
| POST | `/api/collections` | Create collection |
| GET | `/api/stats` | Get database statistics |
| GET | `/api/health` | Health check |

## License

MIT License
