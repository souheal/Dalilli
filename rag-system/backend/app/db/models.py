"""
SQLAlchemy ORM Models for Document Storage

This module defines the database schema for document ingestion.
All extracted text is stored in the database, enabling full-text search
and retrieval without needing to re-process files.

Schema Design:
- Document: Main record for each uploaded file
- DocumentPage: Per-page text storage (for PDFs)

The extracted_text field stores the full concatenated text,
while DocumentPage stores page-level text for granular access.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base


def generate_uuid():
    """Generate a UUID string for document IDs."""
    return str(uuid.uuid4())


class Document(Base):
    """
    Main document record.

    Stores file metadata and full extracted text.
    Each uploaded file creates one Document record.
    """
    __tablename__ = "documents"

    # Primary key - UUID string
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Original file information
    original_filename = Column(String(255), nullable=False, index=True)
    stored_filename = Column(String(255), nullable=False, unique=True)
    stored_path = Column(String(500), nullable=False)

    # File metadata
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Processing flags
    enable_ocr_used = Column(Boolean, default=False, nullable=False)
    ocr_applied = Column(Boolean, default=False, nullable=False)

    # Content information
    page_count = Column(Integer, default=1, nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_text_length = Column(Integer, default=0, nullable=False)

    # Additional metadata as JSON (title, author, etc.)
    metadata_json = Column(JSON, default=dict)

    # Processing status
    status = Column(String(50), default="completed", nullable=False)
    error_message = Column(Text, nullable=True)

    # Relationship to pages (for PDFs)
    pages = relationship(
        "DocumentPage",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentPage.page_number"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.original_filename})>"

    def to_dict(self, include_text: bool = False, include_pages: bool = False):
        """
        Convert to dictionary for API responses.

        Args:
            include_text: Include full extracted text
            include_pages: Include page-level text data
        """
        result = {
            "id": self.id,
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "stored_path": self.stored_path,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "enable_ocr_used": self.enable_ocr_used,
            "ocr_applied": self.ocr_applied,
            "page_count": self.page_count,
            "extracted_text_length": self.extracted_text_length,
            "metadata": self.metadata_json or {},
            "status": self.status,
        }

        if include_text:
            result["extracted_text"] = self.extracted_text

        if include_pages and self.pages:
            result["page_texts"] = [
                {
                    "page_number": p.page_number,
                    "text": p.text_content,
                    "text_length": p.text_length,
                    "ocr_applied": p.ocr_applied
                }
                for p in self.pages
            ]

        return result


class DocumentPage(Base):
    """
    Per-page text storage for multi-page documents (PDFs).

    Enables page-level text retrieval and tracks which pages
    required OCR processing.
    """
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to parent document
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Page information
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=True)
    text_length = Column(Integer, default=0, nullable=False)

    # OCR tracking per page
    ocr_applied = Column(Boolean, default=False, nullable=False)

    # Relationship back to document
    document = relationship("Document", back_populates="pages")

    def __repr__(self):
        return f"<DocumentPage(doc_id={self.document_id}, page={self.page_number})>"
