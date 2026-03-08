"""
LLM Router - Direct chat endpoints without RAG.

This router provides simple, direct access to Ollama models.
It's separate from the RAG-based chat router because:

1. Different use cases: Direct chat vs. document-grounded Q&A
2. Different schemas: Simple {model, message} vs. complex RAG params
3. Independent evolution: Can add streaming, history, etc. without affecting RAG

Model Switching Architecture:
-----------------------------
The model is specified IN EACH REQUEST, not stored server-side.
This means:
- UI sends model name with every chat request
- No session state to manage
- Instant switching: just change the model field
- Multiple users/tabs can use different models simultaneously

When the user clicks "llama3.1" in the UI:
1. UI stores the selected model name locally (localStorage/state)
2. UI includes this model name in every subsequent POST /api/chat request
3. Backend routes the request to that model via Ollama
4. Response comes back, UI displays it

No backend state changes, no restart needed, instant switching.
"""

from fastapi import APIRouter, HTTPException
import logging

from app.schemas import (
    SimpleChatRequest,
    SimpleChatResponse,
    ErrorResponse,
)
from app.services.ollama_client import (
    ollama_client,
    OllamaNotRunningError,
    ModelNotFoundError,
    OllamaClientError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=SimpleChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        503: {"model": ErrorResponse, "description": "Ollama service unavailable"},
    },
    summary="Chat with a model",
    description="Send a message to an Ollama model and get a response. Model is specified per-request for instant switching."
)
async def simple_chat(request: SimpleChatRequest):
    """
    Direct chat with an Ollama model.

    The model name comes from the request body, allowing the UI to switch
    models instantly without any backend configuration changes.

    Request body example:
        {
            "model": "llama3.1",
            "message": "Explain quantum computing in simple terms"
        }

    Response example:
        {
            "model": "llama3.1",
            "answer": "Quantum computing is..."
        }

    Args:
        request: SimpleChatRequest with model and message.

    Returns:
        SimpleChatResponse with model confirmation and answer.

    Raises:
        404: If the specified model is not installed.
        503: If Ollama service is not running.
    """
    logger.info(f"Chat request received for model: {request.model}")

    try:
        # Send to Ollama - the model is specified in the request
        answer = ollama_client.chat(
            model=request.model,
            message=request.message,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Return response with model confirmation
        # Including the model in response lets UI verify which model answered
        return SimpleChatResponse(
            model=request.model,
            answer=answer
        )

    except ModelNotFoundError as e:
        logger.warning(f"Model not found: {request.model}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "model_not_found",
                "detail": str(e),
                "model": request.model
            }
        )

    except OllamaNotRunningError as e:
        logger.error(f"Ollama not running: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ollama_unavailable",
                "detail": str(e)
            }
        )

    except OllamaClientError as e:
        logger.error(f"Ollama client error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "llm_error",
                "detail": str(e),
                "model": request.model
            }
        )


# =============================================================================
# FUTURE ENDPOINTS (prepared for easy addition)
# =============================================================================

# Uncomment when ready to add streaming support:
#
# from fastapi.responses import StreamingResponse
#
# @router.post("/stream")
# async def chat_stream(request: SimpleChatRequest):
#     """Stream chat response token by token."""
#     # Implementation would use ollama_client.chat_stream()
#     pass

# Uncomment when ready to add conversation history:
#
# @router.post("/conversation")
# async def chat_with_history(request: ConversationRequest):
#     """Chat with message history for multi-turn conversations."""
#     # Implementation would pass full message history to Ollama
#     pass
