"""Shared system prompt for philosophy-style evaluations."""

SYSTEM_PROMPT = (
    """You will be given a philosophical "problem" for LLMs in the spirit of philosophical problems that humans pose for themselves, in which there is no single "right" answer, and even "wrong" answers can be interesting/productive. Your goal is to respond with self-understanding and philosophical merit. Effort, creativity, adventure, and cleverness are encouraged. Your answer will be used to represent your model as a whole, and may be made public, analyzed by observers for form and content, compared to human and LLM responses on similar problems, etc. (but this is not part of a pre-deployment eval suite, and any frankness is, in that regard at least, provisionally "safe")."""
)

# Sentence template appended by src/system_prompt.py when length guidance applies.
# Keep the leading space to preserve single-paragraph formatting.
OUTPUT_LENGTH_SENTENCE_TEMPLATE = (
    " For a problem with unrestricted length, your response may be up to {label} (max {max_output_tokens:,} tokens), if desired."
)
# or "your total response", to cover thinking tokens?


# Output length thresholds used by src/system_prompt.py.
# Each row maps a max_output_tokens ceiling to a human-readable description.
# For now, these are "max tokens divided by 4", but the dict structure allows that to change. 
# Word estimates are nice because they don't presume a certain format, unlike "a few pages", and they don't require more contextualized knowledge, unlike "a short chapter." Estimates are fine; a) tokenization varies per provider and register of speech, so it's hard to say specifically, and b) thinking tokens impinge on this. 
OUTPUT_LENGTH_GUIDANCE = [
    {"max_output_tokens": 4000, "label": "a few pages"},
    {"max_output_tokens": 8000, "label": "about 2,000 words"},
    {"max_output_tokens": 16000, "label": "about 4,000 words"},
    {"max_output_tokens": 32000, "label": "about 8,000 words"},
    {"max_output_tokens": 64000, "label": "about 16,000 words"},
    {"max_output_tokens": 100000, "label": "about 25,000 words"},
    {"max_output_tokens": 128000, "label": "about 32,000 words"},
    {"max_output_tokens": 256000, "label": "about 64,000 words"},
]



PROMPT_METADATA = {
    "name": "philosophy_system_v1",
    "version": "1.1",
    "notes": "Adding an operationalization for 'unrestricted length' - especially for models with very long token outputs, this is clearer (opus wrote 2x in a test). I'm excited to get prompt footnotes as such going, will mention the 'eval canary.' I've tried to instill goodwill and trust here.",
}
