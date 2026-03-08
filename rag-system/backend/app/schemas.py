"""
Pydantic schemas for the Ollama API endpoints.

These schemas are intentionally simple and separate from the RAG-related models.
This keeps the direct LLM interaction clean and allows independent evolution
of RAG features vs. direct chat features.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class SimpleChatRequest(BaseModel):
    """
    Request body for direct chat with Ollama.

    The model is specified per-request, allowing instant switching.
    This design means the UI can change models without any backend state management.
    """
    model: str = Field(
        ...,  # Required field
        description="The Ollama model to use (e.g., 'llama3.1', 'mistral')",
        examples=["llama3.1", "mistral", "gemma"]
    )
    message: str = Field(
        ...,
        description="The user's message/prompt",
        min_length=1
    )
    # Optional parameters for future expansion (RAG, streaming, etc.)
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness. Lower = more focused, higher = more creative"
    )
    max_tokens: Optional[int] = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum tokens in the response"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt to set context/behavior"
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class SimpleChatResponse(BaseModel):
    """
    Response from direct chat endpoint.

    Includes the model name so the UI can confirm which model responded.
    This is important when users are switching models frequently.
    """
    model: str = Field(description="The model that generated this response")
    answer: str = Field(description="The model's response text")


class ModelInfo(BaseModel):
    """Details about a single installed model."""
    name: str = Field(description="Model name as used in requests")
    size: Optional[str] = Field(default=None, description="Model size (e.g., '4.7 GB')")
    modified: Optional[str] = Field(default=None, description="Last modified timestamp")


class ModelsListResponse(BaseModel):
    """
    Response containing all locally installed Ollama models.

    The provider field allows future expansion to support multiple
    LLM backends (e.g., llama.cpp, vLLM) without changing the API structure.
    """
    provider: str = Field(
        default="ollama",
        description="The LLM provider/runtime"
    )
    models: List[str] = Field(
        description="List of available model names"
    )
    details: Optional[List[ModelInfo]] = Field(
        default=None,
        description="Detailed info about each model (optional)"
    )


class OllamaHealthResponse(BaseModel):
    """Health check response for Ollama connection."""
    status: str = Field(description="'healthy' or 'unhealthy'")
    ollama_running: bool = Field(description="Whether Ollama service is reachable")
    message: Optional[str] = Field(default=None, description="Additional status info")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(description="Error type/code")
    detail: str = Field(description="Human-readable error message")
    model: Optional[str] = Field(default=None, description="Model that caused the error, if applicable")
