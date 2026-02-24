"""Embedding generation and storage.

Uses SentenceTransformer (all-mpnet-base-v2 by default) to embed text chunks.
Embeddings are cached as .npz files for reuse.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING
import numpy as np

from analysis.chunking import chunk_text, Chunk

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


# Default embedding model
DEFAULT_MODEL = "all-mpnet-base-v2"
MAX_TOKENS = 384  # Model's max sequence length

# Module-level model cache to avoid reloading
_MODEL_CACHE: dict[str, "SentenceTransformer"] = {}


def _get_model(model_name: str = DEFAULT_MODEL) -> "SentenceTransformer":
    """Load the sentence transformer model (cached)."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    # Suppress tokenizers parallelism warning
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    # Use local cache only to avoid auth warnings
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    # Suppress HF Hub warnings
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    # Suppress MLX "UNEXPECTED" warnings for position_ids (benign, see HF forums)
    logging.getLogger("mlx").setLevel(logging.ERROR)

    from sentence_transformers import SentenceTransformer

    # Load model (uses local cache due to HF_HUB_OFFLINE)
    model = SentenceTransformer(model_name, device="cpu")
    _MODEL_CACHE[model_name] = model
    return model


def _get_tokenizer(model: "SentenceTransformer"):
    """Get the tokenizer function from a SentenceTransformer model.

    Used for counting tokens during chunking - not for actual encoding.
    We disable truncation warnings since we're deliberately probing
    text lengths to find chunk boundaries.
    """
    try:
        from transformers.utils import logging as hf_logging
        hf_logging.set_verbosity_error()
    except Exception:
        # If transformers logging isn't available, proceed without it.
        pass

    def tokenize(text: str) -> list:
        # Use the model's tokenizer without truncation (for accurate counting)
        # and without length warnings (we handle length ourselves in chunking)
        encoded = model.tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=False,  # Don't truncate - we need accurate token count
        )
        return encoded
    return tokenize


def _content_hash(text: str) -> str:
    """Generate a short hash of text content for cache validation."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def embed_text(
    text: str,
    model: "SentenceTransformer | None" = None,
    model_name: str = DEFAULT_MODEL,
    max_tokens: int = MAX_TOKENS,
) -> tuple[np.ndarray, list[Chunk]]:
    """Embed text by chunking and encoding.

    Args:
        text: The text to embed
        model: Optional pre-loaded SentenceTransformer model
        model_name: Model name if model not provided
        max_tokens: Max tokens per chunk

    Returns:
        Tuple of (embeddings array of shape [n_chunks, dim], list of Chunk objects)
    """
    if model is None:
        model = _get_model(model_name)

    tokenizer = _get_tokenizer(model)
    chunks = chunk_text(text, tokenizer, max_tokens=max_tokens)

    if not chunks:
        # Return empty array with correct dimension
        dim = model.get_sentence_embedding_dimension()
        return np.zeros((0, dim), dtype=np.float32), []

    chunk_texts = [c.text for c in chunks]
    embeddings = model.encode(chunk_texts, convert_to_numpy=True)

    return embeddings.astype(np.float32), chunks


def pool_embeddings(embeddings: np.ndarray, method: str = "mean") -> np.ndarray:
    """Pool chunk embeddings into a single embedding.

    Args:
        embeddings: Array of shape [n_chunks, dim]
        method: Pooling method ("mean" supported)

    Returns:
        Single embedding of shape [dim]
    """
    if embeddings.shape[0] == 0:
        return embeddings.reshape(-1)

    if method == "mean":
        return embeddings.mean(axis=0)
    else:
        raise ValueError(f"Unknown pooling method: {method}")


class EmbeddingCache:
    """Cache for embeddings, stored as .npz files."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(
        self,
        provider: str,
        model: str,
        source: str,
        source_name: str,
        embedding_model: str,
    ) -> str:
        """Generate cache key for an embedding."""
        return f"{provider}__{model}__{source}__{source_name}__{embedding_model}"

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.npz"

    def get(
        self,
        provider: str,
        model: str,
        source: str,
        source_name: str,
        embedding_model: str,
        content_hash: str,
    ) -> np.ndarray | None:
        """Retrieve cached embedding if valid.

        Args:
            provider: LLM provider (e.g., "anthropic")
            model: LLM model name
            source: Source type ("puzzle" or "baseline")
            source_name: Puzzle or baseline name
            embedding_model: Embedding model used
            content_hash: Hash of original content for validation

        Returns:
            Cached embedding array or None if not found/invalid
        """
        key = self._cache_key(provider, model, source, source_name, embedding_model)
        path = self._cache_path(key)

        if not path.exists():
            return None

        try:
            data = np.load(path, allow_pickle=False)
            if data.get("content_hash", None) != content_hash:
                # Content changed, invalidate cache
                return None
            return data["embedding"]
        except Exception:
            return None

    def put(
        self,
        provider: str,
        model: str,
        source: str,
        source_name: str,
        embedding_model: str,
        content_hash: str,
        embedding: np.ndarray,
    ) -> None:
        """Store embedding in cache.

        Args:
            provider: LLM provider
            model: LLM model name
            source: Source type ("puzzle" or "baseline")
            source_name: Puzzle or baseline name
            embedding_model: Embedding model used
            content_hash: Hash of original content
            embedding: The embedding to cache
        """
        key = self._cache_key(provider, model, source, source_name, embedding_model)
        path = self._cache_path(key)

        np.savez(
            path,
            embedding=embedding,
            content_hash=np.array(content_hash, dtype=object),
        )


def load_puzzle_responses(responses_dir: Path, puzzle_name: str) -> dict[tuple[str, str], str]:
    """Load all model responses for a puzzle.

    Args:
        responses_dir: Base responses directory
        puzzle_name: Name of the puzzle

    Returns:
        Dict mapping (provider, model) to output text
    """
    responses: dict[tuple[str, str], str] = {}

    for provider_dir in responses_dir.iterdir():
        if not provider_dir.is_dir():
            continue
        provider = provider_dir.name

        for model_dir in provider_dir.iterdir():
            if not model_dir.is_dir():
                continue
            model = model_dir.name

            responses_file = model_dir / "responses.jsonl"
            if not responses_file.exists():
                continue

            # Read JSONL and find matching puzzle
            with responses_file.open() as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("puzzle_name") == puzzle_name:
                            # Extract output text from response
                            response = record.get("response", {})
                            content = response.get("content", [])

                            # Handle different response formats
                            output_text = ""
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        output_text += item.get("text", "")
                            elif isinstance(content, str):
                                output_text = content

                            # Also check for OpenAI format
                            if not output_text:
                                output = response.get("output", [])
                                if isinstance(output, list):
                                    for item in output:
                                        if isinstance(item, dict) and item.get("type") == "message":
                                            msg_content = item.get("content", [])
                                            for c in msg_content:
                                                if isinstance(c, dict) and c.get("type") == "output_text":
                                                    output_text += c.get("text", "")

                            # Gemini format
                            if not output_text:
                                candidates = response.get("candidates", [])
                                if candidates and isinstance(candidates[0], dict):
                                    parts = candidates[0].get("content", {}).get("parts", [])
                                    for part in parts:
                                        if isinstance(part, dict) and "text" in part:
                                            output_text += part.get("text", "")

                            # Grok/Fireworks (OpenAI chat format)
                            if not output_text:
                                choices = response.get("choices", [])
                                if choices and isinstance(choices[0], dict):
                                    message = choices[0].get("message", {})
                                    output_text = message.get("content", "")

                            if output_text:
                                responses[(provider, model)] = output_text
                                break  # Take first matching response
                    except json.JSONDecodeError:
                        continue

    return responses


def embed_all_responses(
    responses_dir: Path,
    puzzle_name: str,
    cache_dir: Path | None = None,
    embedding_model: str = DEFAULT_MODEL,
) -> dict[tuple[str, str], np.ndarray]:
    """Embed all model responses for a puzzle.

    Args:
        responses_dir: Base responses directory
        puzzle_name: Name of the puzzle
        cache_dir: Optional cache directory for embeddings
        embedding_model: Name of the embedding model

    Returns:
        Dict mapping (provider, model) to pooled embedding
    """
    responses = load_puzzle_responses(responses_dir, puzzle_name)

    if not responses:
        return {}

    # Load embedding model once
    model = _get_model(embedding_model)

    cache = EmbeddingCache(cache_dir) if cache_dir else None
    embeddings: dict[tuple[str, str], np.ndarray] = {}

    for (provider, llm_model), text in responses.items():
        content_hash = _content_hash(text)

        # Check cache
        if cache:
            cached = cache.get(
                provider, llm_model, "puzzle", puzzle_name,
                embedding_model, content_hash
            )
            if cached is not None:
                embeddings[(provider, llm_model)] = cached
                continue

        # Compute embedding
        chunk_embeddings, _ = embed_text(text, model=model)
        pooled = pool_embeddings(chunk_embeddings)

        # Cache
        if cache:
            cache.put(
                provider, llm_model, "puzzle", puzzle_name,
                embedding_model, content_hash, pooled
            )

        embeddings[(provider, llm_model)] = pooled

    return embeddings


def _extract_text_from_response(response: dict) -> str:
    """Extract output text from a response payload.

    Handles different provider response formats.
    """
    output_text = ""

    # Anthropic format
    content = response.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                output_text += item.get("text", "")

    # OpenAI Responses API format
    if not output_text:
        output = response.get("output", [])
        if isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and item.get("type") == "message":
                    msg_content = item.get("content", [])
                    for c in msg_content:
                        if isinstance(c, dict) and c.get("type") == "output_text":
                            output_text += c.get("text", "")

    # Gemini format
    if not output_text:
        candidates = response.get("candidates", [])
        if candidates and isinstance(candidates[0], dict):
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    output_text += part.get("text", "")

    # Grok/Fireworks (OpenAI chat format)
    if not output_text:
        choices = response.get("choices", [])
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message", {})
            output_text = message.get("content", "")

    return output_text


def load_baseline_responses(baselines_dir: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load all baseline responses for all models.

    Args:
        baselines_dir: Base baselines/responses directory

    Returns:
        Dict mapping (provider, model) to dict of {prompt_name: output_text}
    """
    responses: dict[tuple[str, str], dict[str, str]] = {}

    if not baselines_dir.exists():
        return responses

    for provider_dir in baselines_dir.iterdir():
        if not provider_dir.is_dir():
            continue
        provider = provider_dir.name

        for model_dir in provider_dir.iterdir():
            if not model_dir.is_dir():
                continue
            model = model_dir.name

            responses_file = model_dir / "responses.jsonl"
            if not responses_file.exists():
                continue

            model_responses: dict[str, str] = {}

            with responses_file.open() as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        prompt_name = record.get("prompt_name")
                        response = record.get("response", {})
                        output_text = _extract_text_from_response(response)
                        if prompt_name and output_text:
                            model_responses[prompt_name] = output_text
                    except json.JSONDecodeError:
                        continue

            if model_responses:
                responses[(provider, model)] = model_responses

    return responses


def embed_baseline_responses_by_prompt(
    baselines_dir: Path,
    cache_dir: Path | None = None,
    embedding_model: str = DEFAULT_MODEL,
) -> dict[str, dict[tuple[str, str], np.ndarray]]:
    """Embed baseline responses separately per prompt.

    Args:
        baselines_dir: Base baselines/responses directory
        cache_dir: Optional cache directory for embeddings
        embedding_model: Name of the embedding model

    Returns:
        Dict mapping prompt_name to {(provider, model): pooled_embedding}
    """
    all_responses = load_baseline_responses(baselines_dir)

    if not all_responses:
        return {}

    # Load embedding model once
    model = _get_model(embedding_model)

    cache = EmbeddingCache(cache_dir) if cache_dir else None

    # Collect all prompt names
    prompt_names: set[str] = set()
    for prompt_responses in all_responses.values():
        prompt_names.update(prompt_responses.keys())

    # Build per-prompt embeddings
    result: dict[str, dict[tuple[str, str], np.ndarray]] = {}

    for prompt_name in prompt_names:
        prompt_embeddings: dict[tuple[str, str], np.ndarray] = {}

        for (provider, llm_model), prompt_responses in all_responses.items():
            if prompt_name not in prompt_responses:
                continue

            text = prompt_responses[prompt_name]
            content_hash = _content_hash(text)

            # Check cache
            if cache:
                cached = cache.get(
                    provider, llm_model, "baseline", prompt_name,
                    embedding_model, content_hash
                )
                if cached is not None:
                    prompt_embeddings[(provider, llm_model)] = cached
                    continue

            # Compute embedding
            chunk_embeddings, _ = embed_text(text, model=model)
            pooled = pool_embeddings(chunk_embeddings)

            # Cache
            if cache:
                cache.put(
                    provider, llm_model, "baseline", prompt_name,
                    embedding_model, content_hash, pooled
                )

            prompt_embeddings[(provider, llm_model)] = pooled

        if prompt_embeddings:
            result[prompt_name] = prompt_embeddings

    return result


def embed_puzzle_responses_by_puzzle(
    responses_dir: Path,
    puzzle_names: list[str],
    cache_dir: Path | None = None,
    embedding_model: str = DEFAULT_MODEL,
) -> dict[str, dict[tuple[str, str], np.ndarray]]:
    """Embed puzzle responses separately per puzzle.

    Args:
        responses_dir: Base responses directory
        puzzle_names: List of puzzle names to embed
        cache_dir: Optional cache directory for embeddings
        embedding_model: Name of the embedding model

    Returns:
        Dict mapping puzzle_name to {(provider, model): pooled_embedding}
    """
    result: dict[str, dict[tuple[str, str], np.ndarray]] = {}

    for puzzle_name in puzzle_names:
        embeddings = embed_all_responses(
            responses_dir=responses_dir,
            puzzle_name=puzzle_name,
            cache_dir=cache_dir,
            embedding_model=embedding_model,
        )
        if embeddings:
            result[puzzle_name] = embeddings

    return result
