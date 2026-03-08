"""
Conversation Context Service (MVP)

Adds conversational awareness to the RAG pipeline:
- Detects follow-up queries using heuristic feature scoring
- Rewrites follow-ups into standalone retrieval queries via LLM
- Decides retrieval mode (FRESH vs MERGE) and provides source anchoring

Design:
- Heuristic-only classification (no LLM classifier in v1)
- LLM rewriting only when heuristic says FOLLOW_UP
- In-memory session store with expiry (no DB dependency)
- Fully backward compatible: session_id is optional
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# --- Constants ---

MAX_HISTORY_TURNS = 6           # Keep last 3 exchanges (3 user + 3 assistant)
MAX_TURN_CHARS = 200            # Truncate historical turns for LLM context
MAX_SESSION_AGE = 1800          # 30 minutes
MAX_SESSIONS = 1000             # LRU eviction cap
FOLLOW_UP_THRESHOLD = 0.25     # Score >= this → FOLLOW_UP
DEFAULT_SESSION_ID = "local"    # Single-user mode when no session_id provided
SOURCE_BOOST_FACTOR = 1.2       # Score multiplier for anchored doc_ids


# --- Data Structures ---

class RetrievalMode(Enum):
    FRESH = "fresh"
    MERGE = "merge"


@dataclass
class TurnRecord:
    role: str           # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionState:
    session_id: str
    turns: List[TurnRecord] = field(default_factory=list)
    last_rewritten_query: Optional[str] = None
    last_top_source_ids: List[str] = field(default_factory=list)
    last_collection: str = "default"
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)


@dataclass
class EnrichedQuery:
    search_query: str
    retrieval_mode: RetrievalMode
    anchor_doc_ids: List[str] = field(default_factory=list)
    is_follow_up: bool = False
    follow_up_score: float = 0.0
    rewritten: bool = False


# --- Session Store ---

class SessionStore:
    """In-memory session storage with lazy expiry."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create(self, session_id: str) -> SessionState:
        now = time.time()

        # Lazy cleanup of expired session
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if now - session.last_active_at > MAX_SESSION_AGE:
                del self._sessions[session_id]
                logger.debug("Session '%s' expired, creating new", session_id)
            else:
                session.last_active_at = now
                return session

        # LRU eviction if at capacity
        if len(self._sessions) >= MAX_SESSIONS:
            oldest_id = min(self._sessions, key=lambda k: self._sessions[k].last_active_at)
            del self._sessions[oldest_id]
            logger.debug("Session store full, evicted '%s'", oldest_id)

        session = SessionState(session_id=session_id)
        self._sessions[session_id] = session
        return session

    def add_turn(self, session_id: str, role: str, content: str):
        session = self.get_or_create(session_id)
        session.turns.append(TurnRecord(role=role, content=content))
        # Trim to MAX_HISTORY_TURNS
        if len(session.turns) > MAX_HISTORY_TURNS:
            session.turns = session.turns[-MAX_HISTORY_TURNS:]

    def update_sources(self, session_id: str, source_ids: List[str], collection: str,
                       rewritten_query: Optional[str] = None):
        session = self.get_or_create(session_id)
        session.last_top_source_ids = source_ids
        session.last_collection = collection
        session.last_rewritten_query = rewritten_query


# --- Heuristic Follow-Up Classifier ---

# Arabic attached pronoun suffixes (bound pronouns that require an antecedent)
_ARABIC_PRONOUN_SUFFIX = re.compile(
    r'[\u0600-\u06FF]{2,}(?:ها|هم|هن|كم|كن|نا|ه|ك)\b'
)

# Arabic/English demonstratives and anaphoric references
_DEICTIC_PATTERN = re.compile(
    r'\b(?:هذا|هذه|هؤلاء|ذلك|تلك|أولئك|this|that|these|those|it|they|its|their|them)\b',
    re.IGNORECASE
)

# Discourse connectives at message start (coordinating/additive/contrastive)
_CONNECTIVE_START = re.compile(
    r'^\s*(?:و(?:لكن|ماذا|هل|أيضاً|كذلك)?|أو|لكن|بل|أيضاً|بالإضافة|كذلك|إضافة|ثم|also|but|and|however|moreover)\b',
    re.IGNORECASE
)

# Comparative structures missing a full comparand
_COMPARATIVE_PATTERN = re.compile(
    r'\b(?:قارن|مقارنة|الفرق|أفضل|أسوأ|أكثر|أقل|compare|difference|versus|vs)\b',
    re.IGNORECASE
)


class HeuristicFollowUpClassifier:
    """
    Scores whether a message is a follow-up using linguistic features.
    No LLM dependency. Deterministic. <1ms.
    """

    def score(self, message: str, has_history: bool) -> float:
        """
        Returns a follow-up score between 0.0 and 1.0.
        Higher = more likely a follow-up.
        """
        if not has_history:
            return 0.0

        tokens = message.split()
        token_count = len(tokens)

        # Feature 1: Pronominal / deictic reference (weight: 0.35)
        has_pronoun_suffix = bool(_ARABIC_PRONOUN_SUFFIX.search(message))
        has_deictic = bool(_DEICTIC_PATTERN.search(message))
        f1 = 1.0 if (has_pronoun_suffix or has_deictic) else 0.0

        # Feature 2: Missing subject / very short message (weight: 0.25)
        if token_count <= 2:
            f2 = 1.0
        elif token_count <= 4:
            # Check if it lacks a question word or verb-like structure
            has_question_word = bool(re.search(
                r'\b(?:ما|من|أين|متى|كيف|لماذا|هل|كم|what|who|where|when|how|why)\b',
                message, re.IGNORECASE
            ))
            f2 = 0.0 if has_question_word else 1.0
        else:
            f2 = 0.0

        # Feature 3: Discourse connective at start (weight: 0.20)
        f3 = 1.0 if _CONNECTIVE_START.search(message) else 0.0

        # Feature 4: Comparative without full entities (weight: 0.20)
        has_comparative = bool(_COMPARATIVE_PATTERN.search(message))
        # If comparative + short message, likely referencing prior entity
        f4 = 1.0 if (has_comparative and token_count < 10) else 0.0

        score = (f1 * 0.35) + (f2 * 0.25) + (f3 * 0.20) + (f4 * 0.20)
        return round(score, 3)


# --- Query Rewriter ---

REWRITE_SYSTEM_PROMPT = """أنت معيد صياغة استعلامات البحث في نظام استرجاع مستندات.
ستتلقى سجل محادثة ورسالة متابعة تعتمد على السياق السابق.

مهمتك: أعد صياغة رسالة المتابعة لتصبح استعلام بحث مستقل وكامل يحتوي على جميع المعلومات اللازمة لاسترجاع المستندات.

قواعد صارمة:
- يمكنك فقط استخدام المعلومات الموجودة في سجل المحادثة لملء المراجع والمواضيع الناقصة
- لا تضف حقائق أو كيانات لم تُذكر في المحادثة
- حافظ على اللغة الأصلية (العربية تبقى عربية)
- الاستعلام المعاد صياغته يجب أن يكون استعلام بحث طبيعي

أعد فقط الاستعلام المعاد صياغته، بدون أي شرح أو نص إضافي."""


class QueryRewriter:
    """Rewrites follow-up queries into standalone retrieval queries using LLM."""

    def rewrite(self, turns: List[TurnRecord], current_message: str, llm_service) -> Optional[str]:
        """
        Rewrite a follow-up message into a standalone query.
        Returns the rewritten query, or None on failure.
        """
        if not llm_service or not llm_service.enabled:
            return None

        # Format history (truncated per turn)
        history_lines = []
        for turn in turns:
            truncated = turn.content[:MAX_TURN_CHARS]
            if len(turn.content) > MAX_TURN_CHARS:
                truncated += "..."
            label = "المستخدم" if turn.role == "user" else "المساعد"
            history_lines.append(f"{label}: {truncated}")

        history_text = "\n".join(history_lines)

        user_prompt = f"""سجل المحادثة:
{history_text}

رسالة المتابعة: {current_message}

أعد صياغتها كاستعلام بحث مستقل:"""

        try:
            response = llm_service.client.chat(
                model=llm_service.model_name,
                messages=[
                    {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,
                    "num_predict": 200
                }
            )
            rewritten = response["message"]["content"].strip()
            # Basic sanity: if rewrite is empty or way too long, reject
            if not rewritten or len(rewritten) > 500:
                return None
            return rewritten
        except Exception as e:
            logger.warning("Query rewrite failed, using original: %s", e)
            return None


# --- Orchestrator ---

class ConversationContextService:
    """
    Main entry point. Processes a user query with conversation context
    and returns an EnrichedQuery for the retrieval pipeline.
    """

    def __init__(self):
        self.session_store = SessionStore()
        self.classifier = HeuristicFollowUpClassifier()
        self.rewriter = QueryRewriter()

    def process(
        self,
        query: str,
        collection: str,
        llm_service,
        session_id: Optional[str] = None,
    ) -> EnrichedQuery:
        """
        Analyze query in conversation context and return an enriched query.

        Safe fallback: if anything fails, returns the original query
        with FRESH mode (identical to current stateless behavior).
        """
        sid = session_id or DEFAULT_SESSION_ID
        session = self.session_store.get_or_create(sid)
        has_history = len([t for t in session.turns if t.role == "user"]) > 0

        # 1. Classify
        score = self.classifier.score(query, has_history)
        is_follow_up = score >= FOLLOW_UP_THRESHOLD

        logger.debug(
            "Follow-up detection: score=%.3f, decision=%s, session='%s', history_turns=%d",
            score, "FOLLOW_UP" if is_follow_up else "STANDALONE", sid, len(session.turns)
        )

        # 2. If standalone, return as-is with FRESH mode
        if not is_follow_up:
            return EnrichedQuery(
                search_query=query,
                retrieval_mode=RetrievalMode.FRESH,
                is_follow_up=False,
                follow_up_score=score,
            )

        # 3. Follow-up: attempt rewrite
        rewritten_query = self.rewriter.rewrite(session.turns, query, llm_service)
        search_query = rewritten_query if rewritten_query else query
        was_rewritten = rewritten_query is not None

        logger.debug(
            "Query rewrite: rewritten=%s, query='%s'",
            was_rewritten, search_query[:80]
        )

        # 4. Determine anchor doc_ids from previous turn
        anchor_ids = []
        if session.last_top_source_ids and session.last_collection == collection:
            anchor_ids = session.last_top_source_ids

        logger.debug(
            "Retrieval mode: MERGE, anchor_doc_ids=%d",
            len(anchor_ids)
        )

        return EnrichedQuery(
            search_query=search_query,
            retrieval_mode=RetrievalMode.MERGE,
            anchor_doc_ids=anchor_ids,
            is_follow_up=True,
            follow_up_score=score,
            rewritten=was_rewritten,
        )

    def record_turn(
        self,
        session_id: Optional[str],
        user_query: str,
        assistant_answer: str,
        source_doc_ids: List[str],
        collection: str,
        rewritten_query: Optional[str] = None,
    ):
        """Record a completed turn in session state."""
        sid = session_id or DEFAULT_SESSION_ID
        self.session_store.add_turn(sid, "user", user_query)
        self.session_store.add_turn(sid, "assistant", assistant_answer)
        self.session_store.update_sources(sid, source_doc_ids, collection, rewritten_query)


# Singleton instance
conversation_context = ConversationContextService()
