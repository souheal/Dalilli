from fastapi import APIRouter, HTTPException
import logging
import time

from app.models import ChatRequest, ChatResponse
from app.services.search import HybridSearchService
from app.services.llm_service import LLMService
from app.services.reranker import RerankerService
from app.services.embeddings import EmbeddingService
from app.services.conversation_context import conversation_context, RetrievalMode
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat query and return an answer based on documents"""
    start_time = time.time()

    try:
        # Initialize services
        embedding_service = EmbeddingService(model_name=request.embedding_model)
        llm_service = LLMService(
            model_name=request.llm_model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        search_service = HybridSearchService(
            embedding_service=embedding_service,
            bm25_weight=request.bm25_weight,
            semantic_weight=request.semantic_weight
        )
        reranker = RerankerService()

        collection = request.collection or "default"

        # --- Conversation context: classify + rewrite if follow-up ---
        enriched = conversation_context.process(
            query=request.query,
            collection=collection,
            llm_service=llm_service,
            session_id=request.session_id,
        )

        # Determine the search query: conversation rewrite takes priority,
        # then the existing query-rewriting feature, then the raw query.
        rewritten_query = None
        if enriched.rewritten:
            search_query = enriched.search_query
            rewritten_query = enriched.search_query
        elif request.enable_query_rewriting and settings.enable_llm:
            rewritten_query = llm_service.rewrite_query(request.query)
            search_query = rewritten_query
        else:
            search_query = request.query

        # --- Retrieval ---
        boost_ids = enriched.anchor_doc_ids if enriched.retrieval_mode == RetrievalMode.MERGE else None

        results = search_service.search(
            query=search_query,
            collection=collection,
            top_k=request.top_k * 2 if request.enable_reranking else request.top_k,
            boost_doc_ids=boost_ids,
        )

        # Filter by relevance threshold
        results = [r for r in results if r["score"] >= request.relevance_threshold]

        # Re-ranking (only if enabled)
        if request.enable_reranking and settings.enable_reranking and len(results) > 0:
            results = reranker.rerank(search_query, results, top_k=request.top_k)
        else:
            results = results[:request.top_k]

        # Generate answer
        if len(results) == 0:
            answer = "لم أتمكن من العثور على معلومات ذات صلة في المستندات للإجابة على سؤالك. يرجى رفع مستندات أولاً."
            sources = []
        else:
            context = "\n\n".join([
                f"Source: {r['metadata'].get('filename', 'Unknown')}\n{r['text']}"
                for r in results
            ])
            answer = llm_service.generate_answer(request.query, context)
            sources = [
                {
                    "filename": r["metadata"].get("filename", "Unknown"),
                    "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                    "score": r["score"],
                    "page": r["metadata"].get("page")
                }
                for r in results
            ]

        # --- Record this turn in session state ---
        source_doc_ids = list({
            r["metadata"].get("doc_id", "")
            for r in results
            if r["metadata"].get("doc_id")
        })
        conversation_context.record_turn(
            session_id=request.session_id,
            user_query=request.query,
            assistant_answer=answer[:200],
            source_doc_ids=source_doc_ids,
            collection=collection,
            rewritten_query=rewritten_query,
        )

        processing_time = time.time() - start_time

        return ChatResponse(
            answer=answer,
            sources=sources,
            rewritten_query=rewritten_query,
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response"""
    return await chat(request)
