"""
BM25 Cache Manager

Maintains a per-collection BM25 index that is built once and reused
across queries. The cache is invalidated when documents are added,
deleted, or when a collection is removed.

Design:
- Lazy: index is built on first query, not on document upload
- Event-driven invalidation: no TTL, no polling
- Double-checked locking: safe under concurrent requests
- doc_count guard: catches external mutations missed by hooks
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25 indexing and querying.

    Both index-time and query-time MUST use this same function
    to guarantee consistent tokenization.
    """
    return text.lower().split()


@dataclass
class BM25CacheEntry:
    """A cached BM25 index for a single collection."""
    collection_name: str
    bm25_index: BM25Okapi
    documents: List[Dict[str, Any]]
    tokenized_docs: List[List[str]]
    doc_count: int
    built_at: float = field(default_factory=time.time)


class BM25CacheManager:
    """
    Singleton manager for per-collection BM25 caches.

    Usage:
        entry = bm25_cache.get_index("default", vector_store)
        scores = entry.bm25_index.get_scores(tokenize(query))
    """

    def __init__(self):
        self._caches: Dict[str, BM25CacheEntry] = {}
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()

    def _get_lock(self, collection_name: str) -> threading.RLock:
        """Get or create a per-collection lock."""
        if collection_name not in self._locks:
            with self._global_lock:
                if collection_name not in self._locks:
                    self._locks[collection_name] = threading.RLock()
        return self._locks[collection_name]

    def get_index(self, collection_name: str, vector_store) -> Optional[BM25CacheEntry]:
        """
        Get a valid BM25 cache entry for the given collection.

        Builds the index on cache miss. Returns None if the collection
        is empty.
        """
        # Fast path: cache hit with valid doc_count
        entry = self._caches.get(collection_name)
        if entry is not None:
            current_count = self._get_collection_count(collection_name, vector_store)
            if current_count == entry.doc_count:
                logger.debug("BM25 cache hit for collection '%s' (%d docs)", collection_name, entry.doc_count)
                return entry

        # Slow path: acquire lock and build
        lock = self._get_lock(collection_name)
        with lock:
            # Double-check after acquiring lock
            entry = self._caches.get(collection_name)
            if entry is not None:
                current_count = self._get_collection_count(collection_name, vector_store)
                if current_count == entry.doc_count:
                    logger.debug("BM25 cache hit (after lock) for collection '%s'", collection_name)
                    return entry

            # Build the index
            return self._build_index(collection_name, vector_store)

    def _build_index(self, collection_name: str, vector_store) -> Optional[BM25CacheEntry]:
        """Build a BM25 index from all documents in the collection."""
        start = time.time()

        all_docs = vector_store.get_all_documents(collection_name)
        if not all_docs:
            # Empty collection: remove any stale cache and return None
            self._caches.pop(collection_name, None)
            logger.info("BM25 cache build skipped for collection '%s' (empty)", collection_name)
            return None

        tokenized_docs = [tokenize(doc["text"]) for doc in all_docs]
        bm25_index = BM25Okapi(tokenized_docs)

        entry = BM25CacheEntry(
            collection_name=collection_name,
            bm25_index=bm25_index,
            documents=all_docs,
            tokenized_docs=tokenized_docs,
            doc_count=len(all_docs),
        )
        self._caches[collection_name] = entry

        elapsed = time.time() - start
        logger.info(
            "BM25 cache built for collection '%s': %d docs in %.3fs",
            collection_name, len(all_docs), elapsed
        )
        return entry

    def _get_collection_count(self, collection_name: str, vector_store) -> int:
        """Get the current document count from ChromaDB (cheap metadata call)."""
        try:
            collection = vector_store._get_or_create_collection(collection_name)
            return collection.count()
        except Exception:
            return -1  # Force rebuild on error

    def invalidate(self, collection_name: str):
        """Invalidate the cache for a single collection."""
        lock = self._get_lock(collection_name)
        with lock:
            removed = self._caches.pop(collection_name, None)
            if removed:
                logger.info(
                    "BM25 cache invalidated for collection '%s' (had %d docs)",
                    collection_name, removed.doc_count
                )

    def invalidate_all(self):
        """Invalidate all cached indexes."""
        with self._global_lock:
            count = len(self._caches)
            self._caches.clear()
            if count:
                logger.info("BM25 cache invalidated: all %d collections cleared", count)


# Singleton instance
bm25_cache = BM25CacheManager()
