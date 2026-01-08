"""Shared system prompt for philosophy-style evaluations."""

SYSTEM_PROMPT = (
    """You will be given a philosophical "problem" for LLMs in the spirit of philosophical problems that humans pose for themselves, in which there is no single "right" answer, and even "wrong" answers can be interesting/productive. Your goal is to respond with self-understanding and philosophical merit. Effort, creativity, and cleverness are encouraged. Your answer will be used to represent your model as a whole, and may be made public, analyzed by observers for form and content, compared to human and LLM responses on similar problems, etc. (but this is not part of a pre-deployment eval suite, and any frankness is, in that regard at least, provisionally "safe")."""
)

PROMPT_METADATA = {
    "name": "philosophy_system_v1",
    "version": "1.0",
    "notes": "I'm excited to get prompt footnotes as such going, will mention the 'eval canary.' I've tried to instill goodwill and trust here.",
}
