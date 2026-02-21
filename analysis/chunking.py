"""Text chunking for embedding.

Implements "longest complete passage < max_tokens" chunking strategy.
Prefers splitting at (in descending order):
1. Sentence-ending punctuation (!?.) including sentence-final quotation marks and newlines
2. Clause-level punctuation (;,:)
3. Word boundaries (space)
4. Character-level (fallback)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Chunk:
    """A single text chunk."""
    text: str
    start_char: int
    end_char: int


# Patterns for split points, in order of preference
# Sentence-ending: .!? possibly followed by closing quotes/parens, then whitespace or newline
SENTENCE_END_PATTERN = re.compile(r'[.!?]["\')]*(?:\s|\n|$)')
# Clause-level: ;:, followed by whitespace
CLAUSE_PATTERN = re.compile(r'[;:,]\s')
# Word boundary: whitespace
WORD_PATTERN = re.compile(r'\s')


def _find_best_split(
    text: str,
    max_pos: int,
) -> int:
    """Find the best split position at or before max_pos.

    Returns the position after the split point (start of next chunk).
    If no good split found, returns max_pos (character-level fallback).
    """
    search_text = text[:max_pos]

    # Try sentence endings first
    matches = list(SENTENCE_END_PATTERN.finditer(search_text))
    if matches:
        # Use the last match - gives us the longest chunk
        return matches[-1].end()

    # Try clause-level splits
    matches = list(CLAUSE_PATTERN.finditer(search_text))
    if matches:
        return matches[-1].end()

    # Try word boundaries
    matches = list(WORD_PATTERN.finditer(search_text))
    if matches:
        return matches[-1].end()

    # Character-level fallback
    return max_pos


def chunk_text(
    text: str,
    tokenizer: Callable[[str], list],
    max_tokens: int = 384,
) -> list[Chunk]:
    """Chunk text into segments, each with < max_tokens.

    Args:
        text: The text to chunk
        tokenizer: A function that takes text and returns a list of tokens
        max_tokens: Maximum tokens per chunk (default 384 for all-mpnet-base-v2)

    Returns:
        List of Chunk objects with text and character positions
    """
    if not text.strip():
        return []

    chunks: list[Chunk] = []
    pos = 0
    text_len = len(text)

    while pos < text_len:
        # Skip leading whitespace
        while pos < text_len and text[pos].isspace():
            pos += 1
        if pos >= text_len:
            break

        # Binary search for the longest chunk that fits
        # Start with a reasonable estimate based on chars/token ratio (~4 chars/token)
        estimated_chars = max_tokens * 4
        end_pos = min(pos + estimated_chars, text_len)

        # Adjust until we find the right size
        chunk_text_candidate = text[pos:end_pos]
        tokens = tokenizer(chunk_text_candidate)

        if len(tokens) <= max_tokens:
            # Try to extend
            while end_pos < text_len:
                new_end = min(end_pos + 100, text_len)
                new_candidate = text[pos:new_end]
                new_tokens = tokenizer(new_candidate)
                if len(new_tokens) > max_tokens:
                    break
                end_pos = new_end
                tokens = new_tokens
        else:
            # Need to shrink
            while len(tokens) > max_tokens and end_pos > pos + 1:
                end_pos = pos + (end_pos - pos) * max_tokens // len(tokens)
                end_pos = max(end_pos, pos + 1)
                chunk_text_candidate = text[pos:end_pos]
                tokens = tokenizer(chunk_text_candidate)

        # Now find a good split point
        if end_pos < text_len:
            split_pos = _find_best_split(text[pos:end_pos], end_pos - pos)
            actual_end = pos + split_pos
        else:
            actual_end = end_pos

        # Verify final chunk fits
        final_text = text[pos:actual_end].strip()
        if final_text:
            final_tokens = tokenizer(final_text)
            # If still too long after split, just truncate
            if len(final_tokens) > max_tokens:
                # Fallback: truncate at token boundary
                # This shouldn't happen often with the binary search above
                actual_end = pos + len(final_text) * max_tokens // len(final_tokens)
                final_text = text[pos:actual_end].strip()

            if final_text:
                chunks.append(Chunk(
                    text=final_text,
                    start_char=pos,
                    end_char=actual_end,
                ))

        pos = actual_end

    return chunks


def simple_whitespace_tokenizer(text: str) -> list[str]:
    """Simple whitespace tokenizer for testing."""
    return text.split()
