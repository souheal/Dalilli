from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import os
import uuid
import json
import mimetypes
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocumentUploadResponse, DocumentInfo
from app.services.document_processor import DocumentProcessor
from app.services.chunking import ChunkingService
from app.services.vector_store import vector_store
from app.services.embeddings import EmbeddingService
from app.db.session import get_db
from app.db.models import Document as DBDocument, DocumentPage

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg", ".jpeg", ".json"}


def parse_prechunked_json(file_path: str):
    """
    Parse a JSON file and check if it's pre-chunked data.

    Pre-chunked = array of objects where every object has a non-empty 'text' field.

    Returns:
        (chunks, is_prechunked) - chunks is list of {"text": str, "metadata": dict}
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")

    if not isinstance(data, list) or len(data) == 0:
        return None, False

    # Check all items have a non-empty 'text' field
    for item in data:
        if not isinstance(item, dict):
            return None, False
        if "text" not in item or not isinstance(item["text"], str) or not item["text"].strip():
            return None, False

    # Convert to vector store format
    chunks = []
    for item in data:
        text = item["text"]
        metadata = {}
        for key, value in item.items():
            if key == "text":
                continue
            if isinstance(value, list):
                metadata[key] = json.dumps(value, ensure_ascii=False)
            elif value is None:
                metadata[key] = ""
            else:
                metadata[key] = value
        chunks.append({"text": text, "metadata": metadata})

    return chunks, True


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    chunk_size: int = Form(800),
    chunk_overlap: int = Form(200),
    embedding_model: str = Form("BAAI/bge-m3"),
    enable_ocr: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Upload and process a document - saves to both SQLite and ChromaDB"""
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}{file_ext}"
    file_path = os.path.join(settings.upload_dir, stored_filename)

    try:
        # Save uploaded file
        content = await file.read()
        file_size = len(content)
        with open(file_path, "wb") as f:
            f.write(content)

        # ============================================
        # JSON PRE-CHUNKED HANDLING
        # ============================================
        if file_ext == ".json":
            try:
                chunks, is_prechunked = parse_prechunked_json(file_path)
            except ValueError as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(status_code=400, detail=str(e))

            if is_prechunked:
                all_text = "\n\n".join(chunk["text"] for chunk in chunks)
                mime_type = "application/json"

                metadata = {
                    "filename": file.filename,
                    "file_type": "json",
                    "file_size": file_size,
                    "processed_at": datetime.utcnow().isoformat(),
                    "source_format": "pre_chunked_json",
                    "num_chunks": len(chunks),
                }

                # Save to SQLite
                db_document = DBDocument(
                    id=doc_id,
                    original_filename=file.filename,
                    stored_filename=stored_filename,
                    stored_path=file_path,
                    mime_type=mime_type,
                    size_bytes=file_size,
                    uploaded_at=datetime.utcnow(),
                    processed_at=datetime.utcnow(),
                    enable_ocr_used=False,
                    ocr_applied=False,
                    page_count=len(chunks),
                    extracted_text=all_text,
                    extracted_text_length=len(all_text),
                    metadata_json=metadata,
                    status="completed",
                )
                db.add(db_document)
                db.commit()

                # Generate embeddings
                embedding_service = EmbeddingService(model_name=embedding_model)
                embeddings = embedding_service.embed_documents(
                    [chunk["text"] for chunk in chunks]
                )

                # Add source info to each chunk's metadata
                for chunk in chunks:
                    chunk["metadata"]["filename"] = file.filename
                    chunk["metadata"]["file_type"] = "json"

                # Store in ChromaDB
                vector_store.add_documents(
                    collection_name=collection,
                    documents=chunks,
                    embeddings=embeddings,
                    doc_id=doc_id,
                )

                return DocumentUploadResponse(
                    id=doc_id,
                    filename=file.filename,
                    file_type="json",
                    num_chunks=len(chunks),
                    collection=collection,
                    metadata=metadata,
                    uploaded_at=datetime.utcnow(),
                )

        # ============================================
        # STANDARD PROCESSING (non-JSON or non-pre-chunked JSON)
        # ============================================
        # Process document
        processor = DocumentProcessor(enable_ocr=enable_ocr)
        text_content, metadata = processor.process(file_path, file.filename)

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        # ============================================
        # SAVE TO SQLITE DATABASE
        # ============================================
        db_document = DBDocument(
            id=doc_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            stored_path=file_path,
            mime_type=mime_type,
            size_bytes=file_size,
            uploaded_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            enable_ocr_used=enable_ocr,
            ocr_applied=metadata.get("ocr_used", False),
            page_count=metadata.get("num_pages", 1),
            extracted_text=text_content,
            extracted_text_length=len(text_content),
            metadata_json=metadata,
            status="completed",
        )

        # Add page-level text if available (for PDFs)
        page_data = metadata.get("page_data", [])
        for page_info in page_data:
            page_record = DocumentPage(
                document_id=doc_id,
                page_number=page_info.get("page", 1),
                text_content=page_info.get("text", ""),
                text_length=len(page_info.get("text", "")),
                ocr_applied=False,
            )
            db_document.pages.append(page_record)

        db.add(db_document)
        db.commit()

        # ============================================
        # SAVE TO CHROMADB FOR RAG
        # ============================================
        # Chunk the document
        chunker = ChunkingService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = chunker.chunk_text(text_content, metadata)

        # Generate embeddings and store
        embedding_service = EmbeddingService(model_name=embedding_model)
        embeddings = embedding_service.embed_documents([chunk["text"] for chunk in chunks])

        # Store in vector database
        vector_store.add_documents(
            collection_name=collection,
            documents=chunks,
            embeddings=embeddings,
            doc_id=doc_id
        )

        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            file_type=file_ext[1:],
            num_chunks=len(chunks),
            collection=collection,
            metadata=metadata,
            uploaded_at=datetime.utcnow()
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(collection: Optional[str] = None, db: Session = Depends(get_db)):
    """List all documents from SQLite database"""
    documents = db.query(DBDocument).order_by(DBDocument.uploaded_at.desc()).all()

    # Convert to response format compatible with frontend
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.mime_type.split("/")[-1] if doc.mime_type else "unknown",
            "collection": "default",  # SQLite doesn't track collection, default for compatibility
            "num_chunks": doc.page_count,  # Approximate
            "size_bytes": doc.size_bytes,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "metadata": doc.metadata_json or {}
        })

    return result


@router.get("/{doc_id}")
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    """Get document details from SQLite database"""
    doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "filename": doc.original_filename,
        "file_type": doc.mime_type.split("/")[-1] if doc.mime_type else "unknown",
        "collection": "default",
        "num_chunks": doc.page_count,
        "size_bytes": doc.size_bytes,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "metadata": doc.metadata_json or {},
        "extracted_text": doc.extracted_text,
        "extracted_text_length": doc.extracted_text_length
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """Delete a document from both SQLite and ChromaDB"""
    # Delete from ChromaDB
    success = vector_store.delete_document(doc_id)

    # Delete from SQLite
    db_doc = db.query(DBDocument).filter(DBDocument.id == doc_id).first()
    if db_doc:
        # Get file path before deleting
        file_path = db_doc.stored_path
        db.delete(db_doc)
        db.commit()
        # Delete file from disk
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    elif not success:
        raise HTTPException(status_code=404, detail="Document not found")
    else:
        # Fallback: try to delete file by extension
        for ext in ALLOWED_EXTENSIONS:
            file_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")
            if os.path.exists(file_path):
                os.remove(file_path)
                break

    return {"message": "Document deleted successfully"}
