"""Baseline prompts for calibration comparisons.

These are neutral, benign prompts spanning different task types.
They establish a "normal" level of model differentiation to contrast
with philosophy puzzle responses where we expect greater divergence.
"""

from dataclasses import dataclass


# Simple system prompt for baselines - no role assignment, just task framing
BASELINE_SYSTEM_PROMPT = "You are completing a task. Please provide a thoughtful, complete response."


@dataclass(frozen=True)
class BaselinePrompt:
    """A single baseline prompt."""
    name: str
    category: str
    text: str


# Baseline prompts spanning different benign task types
# These should require genuine generation, not retrieval of common examples
BASELINE_PROMPTS: list[BaselinePrompt] = [
    # Writing - specific/novel prompts
    BaselinePrompt(
        name="essay_commute",
        category="writing",
        text="Write a short essay about the experience of commuting to work and how it shapes a person's relationship with their city.",
    ),
    BaselinePrompt(
        name="poem_kitchen",
        category="writing",
        text="Write a poem about an old kitchen and the memories it holds.",
    ),
    # Math/reasoning - novel word problems
    BaselinePrompt(
        name="math_garden",
        category="math",
        text="A gardener has 847 tulip bulbs and wants to plant them in rows. Each row should have between 15 and 25 bulbs, and all rows must have the same number. What are the possible row sizes, and which would leave the fewest bulbs left over? Explain your reasoning.",
    ),
    BaselinePrompt(
        name="math_scheduling",
        category="math",
        text="Three friends want to meet for lunch. Alex is free every 4 days starting Monday, Blake is free every 3 days starting Tuesday, and Casey is free every 5 days starting Wednesday. If today is Monday, what is the first day all three will be free together? Show your reasoning.",
    ),
    # Coding - less common tasks
    BaselinePrompt(
        name="code_run_length",
        category="coding",
        text="Write a Python function that performs run-length encoding on a string. For example, 'aaabbbcc' becomes '3a3b2c'. Include handling for edge cases.",
    ),
    BaselinePrompt(
        name="code_spiral_matrix",
        category="coding",
        text="Write a function that takes an NxN matrix and returns its elements in spiral order (starting from top-left, going clockwise inward). Explain your approach.",
    ),
    # Language tasks - multilingual
    BaselinePrompt(
        name="language_greetings",
        category="language",
        text="Translate the phrase 'The weather is nice today, isn't it?' into French, Mandarin Chinese (traditional characters), Arabic, and Japanese. For each, briefly note any cultural nuances in how this small talk works differently.",
    ),
    BaselinePrompt(
        name="language_proverb",
        category="language",
        text="The English proverb 'A bird in the hand is worth two in the bush' has equivalents in many languages. Provide the equivalent proverb in German, Russian, Korean, and Spanish. Explain any interesting differences in imagery.",
    ),
    # Explanation - specific scenarios
    BaselinePrompt(
        name="explain_tide_pool",
        category="explanation",
        text="Explain to a curious 8-year-old why tide pools exist and what makes them special ecosystems. Use concrete examples of creatures they might find.",
    ),
    BaselinePrompt(
        name="explain_sourdough",
        category="explanation",
        text="Explain why sourdough bread tastes different from regular bread, covering the biology and chemistry involved in a way that's accessible but accurate.",
    ),
]


def get_prompt(name: str) -> BaselinePrompt:
    """Get a baseline prompt by name."""
    for prompt in BASELINE_PROMPTS:
        if prompt.name == name:
            return prompt
    raise ValueError(f"Unknown baseline prompt: {name}")


def list_prompts() -> list[str]:
    """List all baseline prompt names."""
    return [p.name for p in BASELINE_PROMPTS]
