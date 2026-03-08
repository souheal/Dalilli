"""
Models Router - API endpoints for model discovery and management.

This router provides endpoints for:
1. Listing available Ollama models
2. Checking Ollama health status

These endpoints are separate from chat because they serve a different purpose:
- Chat is about interaction with a model
- Models is about discovering what's available

This separation makes the API cleaner and allows independent scaling/caching.
"""

from fastapi import APIRouter, HTTPException

from app.schemas import (
    ModelsListResponse,
    ModelInfo,
    OllamaHealthResponse,
    ErrorResponse,
)
from app.services.ollama_client import (
    ollama_client,
    OllamaNotRunningError,
)

router = APIRouter()


@router.get(
    "/",
    response_model=ModelsListResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Ollama service unavailable"}
    },
    summary="List available models",
    description="Returns all locally installed Ollama models that can be used for chat."
)
async def get_models():
    """
    Get all locally installed Ollama models.

    This endpoint queries the local Ollama service to get the actual
    installed models, not a hardcoded list. This ensures the UI always
    shows what's really available.

    Returns:
        ModelsListResponse with provider name and list of model names.

    Example response:
        {
            "provider": "ollama",
            "models": ["llama3.1", "mistral", "gemma"]
        }
    """
    try:
        # Get detailed model info
        models_detail = ollama_client.list_models()

        # Extract just the names for the simple list
        model_names = sorted(set(m["name"] for m in models_detail))

        # Build detailed info
        details = [
            ModelInfo(
                name=m["name"],
                size=m.get("size"),
                modified=m.get("modified")
            )
            for m in models_detail
        ]

        return ModelsListResponse(
            provider="ollama",
            models=model_names,
            details=details
        )

    except OllamaNotRunningError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ollama_unavailable",
                "detail": str(e),
            }
        )


@router.get(
    "/health",
    response_model=OllamaHealthResponse,
    summary="Check Ollama health",
    description="Check if the local Ollama service is running and reachable."
)
async def check_health():
    """
    Health check for Ollama service.

    Use this endpoint to verify Ollama is running before attempting
    to list models or send chat requests.

    Returns:
        OllamaHealthResponse with status and connection info.
    """
    is_running = ollama_client.is_healthy()

    if is_running:
        return OllamaHealthResponse(
            status="healthy",
            ollama_running=True,
            message="Ollama service is running and reachable"
        )
    else:
        return OllamaHealthResponse(
            status="unhealthy",
            ollama_running=False,
            message="Cannot connect to Ollama. Ensure it's running with: ollama serve"
        )
