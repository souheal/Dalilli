"""
Document Ingestion Router

Provides endpoints for uploading, storing, and retrieving documents
with full text extraction and optional OCR.

All documents are:
1. Saved to disk (data/uploads/) with UUID prefix to avoid collisions
2. Stored in SQLite database with full metadata and extracted text
3. Persisted across server restarts

Endpoints:
- POST /api/ingest/upload - Upload and process a document
- GET /api/ingest/documents - List all documents
- GET /api/ingest/documents/{doc_id} - Get document with text
- DELETE /api/ingest/documents/{doc_id} - Delete a document

OCR Toggle:
- When enable_ocr=false: Only extract embedded text (fast)
- When enable_ocr=true: Use OCR for scanned PDFs and images
"""

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.db.models import Document, DocumentPage
from app.services.document_loader import (
    DocumentLoader,
    OCRNotAvailableError,
    UnsupportedFileTypeError,
)

router = APIRouter()

# Supported file extensions - extended for all common document types
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".xlsx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".json",
}


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    ext = os.path.splitext(filename)[1].lower()

    # Explicit mapping for reliability
    extension_map = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    if ext in extension_map:
        return extension_map[ext]

    # Fallback to mimetypes library
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    enable_ocr: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document.

    The document is:
    1. Saved to disk with a UUID prefix (prevents overwrites)
    2. Text extracted (all pages for PDFs)
    3. OCR applied if enabled and needed
    4. Stored in database with full text and metadata

    Args:
        file: The uploaded file (PDF, TXT, PNG, JPG)
        enable_ocr: Whether to use OCR for scanned content

    Returns:
        JSON with document metadata and extraction summary

    Errors:
        400: Unsupported file type
        500: Processing error
        503: OCR requested but Tesseract not installed
    """
    # Validate file extension
    original_filename = file.filename or "unknown"
    file_ext = os.path.splitext(original_filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_file_type",
                "message": f"File type '{file_ext}' not supported",
                "allowed_types": list(ALLOWED_EXTENSIONS)
            }
        )

    # Generate unique ID and filename
    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}{file_ext}"
    stored_path = os.path.join(settings.upload_dir, stored_filename)

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)

    try:
        # Save file to disk
        content = await file.read()
        file_size = len(content)

        with open(stored_path, "wb") as f:
            f.write(content)

        # Extract text
        loader = DocumentLoader(enable_ocr=enable_ocr)

        try:
            result = loader.extract(stored_path)
        except OCRNotAvailableError as e:
            # Clean up file if OCR was required but not available
            if os.path.exists(stored_path):
                os.remove(stored_path)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "ocr_not_available",
                    "message": str(e),
                    "hint": "Set enable_ocr=false to skip OCR, or install Tesseract"
                }
            )
        except UnsupportedFileTypeError as e:
            if os.path.exists(stored_path):
                os.remove(stored_path)
            raise HTTPException(status_code=400, detail=str(e))

        # Create database record
        mime_type = get_mime_type(original_filename)

        document = Document(
            id=doc_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            stored_path=stored_path,
            mime_type=mime_type,
            size_bytes=file_size,
            uploaded_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
            enable_ocr_used=enable_ocr,
            ocr_applied=result.ocr_applied,
            page_count=result.page_count,
            extracted_text=result.full_text,
            extracted_text_length=len(result.full_text),
            metadata_json=result.metadata,
            status="completed",
        )

        # Add page records for multi-page documents
        for page in result.pages:
            page_record = DocumentPage(
                document_id=doc_id,
                page_number=page.page_number,
                text_content=page.text,
                text_length=len(page.text),
                ocr_applied=page.ocr_applied,
            )
            document.pages.append(page_record)

        db.add(document)
        db.commit()
        db.refresh(document)

        # Build response
        response = {
            "id": doc_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "mime_type": mime_type,
            "size_bytes": file_size,
            "uploaded_at": document.uploaded_at.isoformat(),
            "enable_ocr_used": enable_ocr,
            "ocr_applied": result.ocr_applied,
            "page_count": result.page_count,
            "extracted_text_length": len(result.full_text),
            "metadata": result.metadata,
            "status": "completed",
        }

        # Add warning if image uploaded without OCR
        if file_ext in {".png", ".jpg", ".jpeg"} and not enable_ocr:
            response["warning"] = "Image uploaded without OCR - no text extracted. Enable OCR to extract text."

        return JSONResponse(status_code=201, content=response)

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(stored_path):
            os.remove(stored_path)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "processing_error",
                "message": str(e)
            }
        )


@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all uploaded documents.

    Returns metadata for each document without the full extracted text
    (use GET /documents/{id} to get full text).

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum records to return (default 100)

    Returns:
        List of document metadata objects
    """
    documents = (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": db.query(Document).count(),
        "documents": [doc.to_dict(include_text=False) for doc in documents]
    }


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    include_pages: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get a document by ID with full extracted text.

    Args:
        doc_id: Document UUID
        include_pages: Include page-level text (default: True)

    Returns:
        Document metadata, full extracted text, and optionally page texts

    Errors:
        404: Document not found
    """
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Document {doc_id} not found"}
        )

    return document.to_dict(include_text=True, include_pages=include_pages)


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and its file from disk.

    Args:
        doc_id: Document UUID

    Returns:
        Success message

    Errors:
        404: Document not found
    """
    document = db.query(Document).filter(Document.id == doc_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Document {doc_id} not found"}
        )

    # Delete file from disk
    if os.path.exists(document.stored_path):
        os.remove(document.stored_path)

    # Delete from database (cascades to pages)
    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully", "id": doc_id}


@router.get("/ocr-status")
async def get_ocr_status():
    """
    Check if OCR is available on this system.

    Use this endpoint to determine whether to show the OCR toggle in the UI.

    Returns:
        - available: Boolean indicating if OCR can be used
        - message: Description of status or installation instructions
    """
    try:
        from app.services.ocr_service import OCRService
        OCRService()
        return {
            "available": True,
            "message": "OCR is available and ready to use"
        }
    except Exception as e:
        return {
            "available": False,
            "message": str(e)
        }
