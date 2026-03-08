from typing import List, Dict, Any
from app.config import settings

# Only load model if reranking is enabled
if settings.enable_reranking:
    try:
        from sentence_transformers import CrossEncoder
        RERANKER_AVAILABLE = True
    except ImportError:
        RERANKER_AVAILABLE = False
else:
    RERANKER_AVAILABLE = False


class RerankerService:
    """Service for re-ranking search results"""

    _model = None

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.enabled = settings.enable_reranking and RERANKER_AVAILABLE

        if self.enabled and RerankerService._model is None:
            from sentence_transformers import CrossEncoder
            RerankerService._model = CrossEncoder(model_name)

        self.model = RerankerService._model

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results using a cross-encoder model
        """
        if not self.enabled or not results:
            return results[:top_k]

        # Prepare pairs for cross-encoder
        pairs = [(query, result["text"]) for result in results]

        # Get cross-encoder scores
        scores = self.model.predict(pairs)

        # Add scores to results
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])
            original_score = result.get("score", 0)
            result["score"] = (original_score + float(scores[i])) / 2

        # Sort by combined score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def score_pair(self, query: str, document: str) -> float:
        """Score a single query-document pair"""
        if not self.enabled:
            return 0.5
        return float(self.model.predict([(query, document)])[0])
