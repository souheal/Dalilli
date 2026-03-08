import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import json

from app.config import settings
from app.models import DocumentInfo, CollectionResponse, DatabaseStats
from app.services.bm25_cache import bm25_cache


class VectorStore:
    """Vector store service using ChromaDB"""

    def __init__(self):
        self.client = None
        self.collections = {}
        self.document_metadata = {}
        self.metadata_file = os.path.join(settings.data_dir, "document_metadata.json")

    def initialize(self):
        """Initialize the ChromaDB client"""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Ensure default collection exists
        self._get_or_create_collection("default")
        # Load document metadata
        self._load_metadata()

    def _get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a collection"""
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[name]

    def _load_metadata(self):
        """Load document metadata from file"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                self.document_metadata = json.load(f)
        else:
            self.document_metadata = {}

    def _save_metadata(self):
        """Save document metadata to file"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.document_metadata, f, indent=2, default=str)

    def add_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        doc_id: str
    ):
        """Add documents to the vector store"""
        collection = self._get_or_create_collection(collection_name)

        ids = [f"{doc_id}_{i}" for i in range(len(documents))]
        texts = [doc["text"] for doc in documents]
        metadatas = []

        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {}).copy()
            metadata["doc_id"] = doc_id
            metadata["chunk_index"] = i
            # Ensure all metadata values are JSON serializable
            metadatas.append({
                k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                for k, v in metadata.items()
                if k != "page_data"  # Exclude complex nested data
            })

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # Store document metadata
        self.document_metadata[doc_id] = {
            "filename": documents[0].get("metadata", {}).get("filename", "Unknown"),
            "file_type": documents[0].get("metadata", {}).get("file_type", "unknown"),
            "collection": collection_name,
            "num_chunks": len(documents),
            "size_bytes": documents[0].get("metadata", {}).get("file_size", 0),
            "uploaded_at": datetime.utcnow().isoformat(),
            "metadata": documents[0].get("metadata", {})
        }
        self._save_metadata()

        # Invalidate BM25 cache — corpus has changed
        bm25_cache.invalidate(collection_name)

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        collection = self._get_or_create_collection(collection_name)

        if collection.count() == 0:
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                # Convert distance to similarity score (cosine distance to similarity)
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance  # For cosine distance

                formatted_results.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": similarity
                })

        return formatted_results

    def get_all_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get all documents in a collection for BM25 indexing"""
        collection = self._get_or_create_collection(collection_name)

        if collection.count() == 0:
            return []

        results = collection.get(include=["documents", "metadatas"])

        documents = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                documents.append({
                    "text": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "id": results["ids"][i] if results["ids"] else str(i)
                })

        return documents

    def list_documents(self, collection_name: Optional[str] = None) -> List[DocumentInfo]:
        """List all documents"""
        documents = []
        for doc_id, doc_meta in self.document_metadata.items():
            if collection_name and doc_meta.get("collection") != collection_name:
                continue
            documents.append(DocumentInfo(
                id=doc_id,
                filename=doc_meta.get("filename", "Unknown"),
                file_type=doc_meta.get("file_type", "unknown"),
                collection=doc_meta.get("collection", "default"),
                num_chunks=doc_meta.get("num_chunks", 0),
                size_bytes=doc_meta.get("size_bytes", 0),
                uploaded_at=datetime.fromisoformat(doc_meta.get("uploaded_at", datetime.utcnow().isoformat())),
                metadata=doc_meta.get("metadata", {})
            ))
        return documents

    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """Get a specific document"""
        if doc_id not in self.document_metadata:
            return None

        doc_meta = self.document_metadata[doc_id]
        return DocumentInfo(
            id=doc_id,
            filename=doc_meta.get("filename", "Unknown"),
            file_type=doc_meta.get("file_type", "unknown"),
            collection=doc_meta.get("collection", "default"),
            num_chunks=doc_meta.get("num_chunks", 0),
            size_bytes=doc_meta.get("size_bytes", 0),
            uploaded_at=datetime.fromisoformat(doc_meta.get("uploaded_at", datetime.utcnow().isoformat())),
            metadata=doc_meta.get("metadata", {})
        )

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id not in self.document_metadata:
            return False

        doc_meta = self.document_metadata[doc_id]
        collection_name = doc_meta.get("collection", "default")
        collection = self._get_or_create_collection(collection_name)

        # Delete all chunks for this document
        num_chunks = doc_meta.get("num_chunks", 0)
        ids_to_delete = [f"{doc_id}_{i}" for i in range(num_chunks)]

        try:
            collection.delete(ids=ids_to_delete)
        except Exception:
            pass

        # Remove metadata
        del self.document_metadata[doc_id]
        self._save_metadata()

        # Invalidate BM25 cache — corpus has changed
        bm25_cache.invalidate(collection_name)

        return True

    def list_collections(self) -> List[CollectionResponse]:
        """List all collections"""
        collections = []
        existing_collections = {c.name for c in self.client.list_collections()}

        # Ensure default is always included
        existing_collections.add("default")

        for name in existing_collections:
            collection = self._get_or_create_collection(name)
            doc_count = sum(
                1 for doc_meta in self.document_metadata.values()
                if doc_meta.get("collection") == name
            )
            collections.append(CollectionResponse(
                name=name,
                description=None,
                document_count=doc_count,
                created_at=datetime.utcnow()
            ))

        return collections

    def create_collection(self, name: str, description: Optional[str] = None) -> CollectionResponse:
        """Create a new collection"""
        if name in self.collections:
            raise ValueError(f"Collection '{name}' already exists")

        self._get_or_create_collection(name)
        return CollectionResponse(
            name=name,
            description=description,
            document_count=0,
            created_at=datetime.utcnow()
        )

    def get_collection(self, name: str) -> Optional[CollectionResponse]:
        """Get collection details"""
        try:
            collection = self._get_or_create_collection(name)
            doc_count = sum(
                1 for doc_meta in self.document_metadata.values()
                if doc_meta.get("collection") == name
            )
            return CollectionResponse(
                name=name,
                description=None,
                document_count=doc_count,
                created_at=datetime.utcnow()
            )
        except Exception:
            return None

    def delete_collection(self, name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(name)
            if name in self.collections:
                del self.collections[name]

            # Delete documents metadata for this collection
            docs_to_delete = [
                doc_id for doc_id, doc_meta in self.document_metadata.items()
                if doc_meta.get("collection") == name
            ]
            for doc_id in docs_to_delete:
                del self.document_metadata[doc_id]
            self._save_metadata()

            # Invalidate BM25 cache — collection removed
            bm25_cache.invalidate(name)

            return True
        except Exception:
            return False

    def get_stats(self) -> DatabaseStats:
        """Get database statistics"""
        total_documents = len(self.document_metadata)
        total_chunks = sum(
            doc_meta.get("num_chunks", 0)
            for doc_meta in self.document_metadata.values()
        )
        collections = list({
            doc_meta.get("collection", "default")
            for doc_meta in self.document_metadata.values()
        })
        if "default" not in collections:
            collections.append("default")

        # Calculate storage size
        storage_size_bytes = 0
        if os.path.exists(settings.chroma_persist_dir):
            for dirpath, dirnames, filenames in os.walk(settings.chroma_persist_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    storage_size_bytes += os.path.getsize(fp)

        return DatabaseStats(
            total_documents=total_documents,
            total_chunks=total_chunks,
            collections=collections,
            storage_size_mb=round(storage_size_bytes / (1024 * 1024), 2)
        )


# Singleton instance
vector_store = VectorStore()
