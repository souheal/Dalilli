"""
Ollama Client Service

This module provides a clean interface to the local Ollama runtime.
All LLM-specific logic is isolated here, making it easy to:
1. Swap out Ollama for another runtime (llama.cpp, vLLM, etc.)
2. Add features like connection pooling, retries, caching
3. Integrate RAG context without touching the API layer

Design Decision: We use the official `ollama` Python package rather than
raw HTTP requests because:
- It handles connection management properly
- It's maintained by the Ollama team
- It provides proper typing and error handling
"""

import logging
from typing import List, Optional, Dict, Any

# The ollama package provides a clean Python interface to the local Ollama service
import ollama
from ollama import Client, ResponseError

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Custom exception for Ollama-related errors."""
    pass


class OllamaNotRunningError(OllamaClientError):
    """Raised when Ollama service is not reachable."""
    pass


class ModelNotFoundError(OllamaClientError):
    """Raised when the requested model is not installed."""
    pass


class OllamaClient:
    """
    Client for interacting with the local Ollama runtime.

    This class encapsulates all Ollama-specific logic. The API layer
    (routes) should only call methods on this class, never import
    the ollama package directly.

    Model Switching Design:
    -----------------------
    Models are specified per-request rather than stored as instance state.
    This is intentional because:
    1. No server restart needed when switching models
    2. Multiple users/tabs can use different models simultaneously
    3. The UI just sends the model name with each request
    4. Ollama handles model loading/unloading automatically

    Future RAG Integration:
    -----------------------
    The `chat()` method accepts an optional `context` parameter.
    When you add RAG, simply pass the retrieved documents as context.
    The prompt engineering is handled here, not in the routes.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the Ollama client.

        Args:
            base_url: Ollama server URL. Defaults to config setting.
        """
        self._base_url = base_url or settings.ollama_base_url
        self._client = Client(host=self._base_url)

    def is_healthy(self) -> bool:
        """
        Check if Ollama service is running and reachable.

        Returns:
            True if Ollama is running, False otherwise.
        """
        try:
            # Listing models is a lightweight way to check connectivity
            self._client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get all locally installed Ollama models.

        Returns:
            List of model info dictionaries with 'name', 'size', 'modified' keys.

        Raises:
            OllamaNotRunningError: If Ollama service is not reachable.
        """
        try:
            response = self._client.list()
            models = []

            # Handle both dict and object responses (ollama package version differences)
            models_list = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])

            for model in models_list:
                # Handle both dict and object model entries
                if isinstance(model, dict):
                    name = model.get("name", "")
                    size = model.get("size", 0)
                    modified = model.get("modified_at", "")
                else:
                    name = getattr(model, "name", "") or getattr(model, "model", "")
                    size = getattr(model, "size", 0)
                    modified = getattr(model, "modified_at", "")

                # Convert modified to string if it's a datetime
                if hasattr(modified, 'isoformat'):
                    modified = modified.isoformat()
                elif modified and not isinstance(modified, str):
                    modified = str(modified)

                models.append({
                    "name": name.split(":")[0] if name else "",  # Remove tag suffix
                    "full_name": name,
                    "size": self._format_size(size) if isinstance(size, (int, float)) else str(size),
                    "modified": modified,
                })

            return models

        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            raise OllamaNotRunningError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Ensure Ollama is running with: ollama serve"
            ) from e

    def get_model_names(self) -> List[str]:
        """
        Get just the names of installed models (for simple dropdowns).

        Returns:
            List of model names like ['llama3.1', 'mistral', 'gemma']
        """
        models = self.list_models()
        # Use a set to deduplicate (same model with different tags)
        unique_names = list(set(m["name"] for m in models))
        return sorted(unique_names)

    def model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model is installed locally.

        Args:
            model_name: The model name to check (e.g., 'llama3.1')

        Returns:
            True if model is installed, False otherwise.
        """
        try:
            installed_models = self.get_model_names()
            # Check both exact match and partial match (for versioned names)
            return model_name in installed_models or any(
                m.startswith(model_name) for m in installed_models
            )
        except OllamaNotRunningError:
            return False

    def chat(
        self,
        model: str,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,  # For future RAG integration
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send a chat message and get a response.

        This is the core method for LLM interaction. The model is specified
        per-request, allowing instant switching without server state.

        Args:
            model: Ollama model name (e.g., 'llama3.1', 'mistral')
            message: The user's message/prompt
            system_prompt: Optional system prompt for behavior control
            context: Optional RAG context to include (for future use)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            The model's response text.

        Raises:
            OllamaNotRunningError: If Ollama service is not reachable.
            ModelNotFoundError: If the specified model is not installed.
        """
        # Build the messages list
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build user message, optionally including RAG context
        user_content = message
        if context:
            # RAG-ready: context is prepended to the user message
            user_content = f"Context:\n{context}\n\nQuestion: {message}"

        messages.append({"role": "user", "content": user_content})

        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            return response["message"]["content"]

        except ResponseError as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                raise ModelNotFoundError(
                    f"Model '{model}' is not installed. "
                    f"Install it with: ollama pull {model}"
                ) from e
            raise OllamaClientError(f"Ollama error: {e}") from e

        except Exception as e:
            if "connection" in str(e).lower() or "refused" in str(e).lower():
                raise OllamaNotRunningError(
                    f"Cannot connect to Ollama at {self._base_url}. "
                    "Ensure Ollama is running with: ollama serve"
                ) from e
            raise OllamaClientError(f"Unexpected error: {e}") from e

    def _format_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable size string."""
        if size_bytes == 0:
            return "Unknown"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Single instance for the application to use.
# This avoids creating new connections on every request while still
# allowing model switching (model is per-request, not per-client).
ollama_client = OllamaClient()
