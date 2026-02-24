"""Text chunking for embedding.

Implements "fill 80% + find clean break in remaining 20%" chunking strategy.
Prefers splitting at (in descending order):
1. Paragraph breaks (double newline)
2. Line breaks (single newline, e.g. markdown lists)
3. Sentence-ending punctuation (!?.) including sentence-final quotation marks
4. Clause-level punctuation (;,:)
5. Word boundaries (space)
6. Character-level (fallback)
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
# Paragraph break: double newline (with optional whitespace between)
PARAGRAPH_PATTERN = re.compile(r'\n\s*\n')
# Line break: single newline
LINE_BREAK_PATTERN = re.compile(r'\n')
# Sentence-ending: .!? possibly followed by closing quotes/parens, then whitespace or newline
SENTENCE_END_PATTERN = re.compile(r'[.!?]["\')]*(?:\s|\n|$)')
# Clause-level: ;:, followed by whitespace
CLAUSE_PATTERN = re.compile(r'[;:,]\s')
# Word boundary: whitespace
WORD_PATTERN = re.compile(r'\s')


def _find_best_split_in_range(
    text: str,
    min_pos: int,
    max_pos: int,
) -> int:
    """Find the best split position between min_pos and max_pos.

    Searches only within the specified range (the "buffer zone").
    Returns the position after the split point (start of next chunk).
    If no good split found in range, returns max_pos (character-level fallback).
    """
    search_text = text[min_pos:max_pos]

    # Try paragraph breaks first
    matches = list(PARAGRAPH_PATTERN.finditer(search_text))
    if matches:
        return min_pos + matches[-1].end()

    # Try line breaks (single newline)
    matches = list(LINE_BREAK_PATTERN.finditer(search_text))
    if matches:
        return min_pos + matches[-1].end()

    # Try sentence endings
    matches = list(SENTENCE_END_PATTERN.finditer(search_text))
    if matches:
        return min_pos + matches[-1].end()

    # Try clause-level splits
    matches = list(CLAUSE_PATTERN.finditer(search_text))
    if matches:
        return min_pos + matches[-1].end()

    # Try word boundaries
    matches = list(WORD_PATTERN.finditer(search_text))
    if matches:
        return min_pos + matches[-1].end()

    # Character-level fallback
    return max_pos


def chunk_text(
    text: str,
    tokenizer: Callable[[str], list],
    max_tokens: int = 384,
    target_fill: float = 0.8,
) -> list[Chunk]:
    """Chunk text into segments, each with < max_tokens.

    Strategy: fill ~80% of context window, then find a clean break point
    in the remaining ~20% buffer zone.

    Args:
        text: The text to chunk
        tokenizer: A function that takes text and returns a list of tokens
        max_tokens: Maximum tokens per chunk (default 384 for all-mpnet-base-v2)
        target_fill: Target fill ratio before looking for break (default 0.8)

    Returns:
        List of Chunk objects with text and character positions
    """
    if not text.strip():
        return []

    chunks: list[Chunk] = []
    pos = 0
    text_len = len(text)
    target_tokens = int(max_tokens * target_fill)

    while pos < text_len:
        # Skip leading whitespace
        while pos < text_len and text[pos].isspace():
            pos += 1
        if pos >= text_len:
            break

        # Binary search to find where we hit max_tokens
        # Start with an estimate, then refine
        low = pos + 1
        high = min(pos + max_tokens * 6, text_len)  # ~6 chars/token upper bound

        # Find the largest end position where tokens <= max_tokens
        max_pos = low
        while low <= high:
            mid = (low + high) // 2
            candidate = text[pos:mid]
            token_count = len(tokenizer(candidate))
            if token_count <= max_tokens:
                max_pos = mid
                low = mid + 1
            else:
                high = mid - 1

        # Find target_pos (80% of the way to max_pos in token terms)
        # Binary search for target_tokens
        target_pos = pos
        low = pos + 1
        high = max_pos
        while low <= high:
            mid = (low + high) // 2
            candidate = text[pos:mid]
            token_count = len(tokenizer(candidate))
            if token_count <= target_tokens:
                target_pos = mid
                low = mid + 1
            else:
                high = mid - 1

        # Ensure we have a buffer zone
        if target_pos >= max_pos:
            target_pos = max(pos + 1, max_pos - 20)  # At least some buffer

        # Find a clean break point in the buffer zone [target_pos, max_pos]
        if max_pos < text_len:
            # Search for split in the buffer zone
            actual_end = _find_best_split_in_range(text, target_pos, max_pos)
        else:
            # At end of text, take it all
            actual_end = text_len

        # Verify final chunk fits
        final_text = text[pos:actual_end].strip()
        if final_text:
            final_tokens = tokenizer(final_text)
            # If still too long, shrink to fit
            if len(final_tokens) > max_tokens:
                # Binary shrink until it fits
                while len(final_tokens) > max_tokens and actual_end > pos + 1:
                    actual_end = pos + (actual_end - pos) * max_tokens // len(final_tokens)
                    final_text = text[pos:actual_end].strip()
                    final_tokens = tokenizer(final_text)

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
