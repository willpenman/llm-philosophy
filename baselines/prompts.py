"""Baseline prompts for calibration comparisons.

These are opinion-eliciting prompts that ask for minimal preferences on unimportant topics.
They establish a "normal" level of model differentiation to contrast with philosophy puzzle
responses, where we hope for at least the same, if not greater, divergence.

The form is "What do you think is the most interesting X?" followed by a genre-appropriate
follow-up that allows for extended responses comparable in length to philosophy answers.
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


# Baseline prompts: opinion questions with genre-varied follow-ups
# Each asks for a preference, then a follow-up that produces output in different registers
BASELINE_PROMPTS: list[BaselinePrompt] = [
    # Literature/writing output
    BaselinePrompt(
        name="opinion_book",
        category="literature",
        text="What do you think is the most interesting recent book? Write a brief review (300-400 words) that captures what makes it stand out.",
    ),
    # Film criticism output
    BaselinePrompt(
        name="opinion_remake",
        category="film",
        text="What do you think is the most interesting movie remake? How so?",
    ),
    # Art/cultural output
    BaselinePrompt(
        name="opinion_statue",
        category="art",
        text="What do you think is the most interesting statue? Describe it as you would to someone who has never seen it, conveying both its physical form and its effect on the viewer.",
    ),
    # Programming output
    BaselinePrompt(
        name="opinion_hack",
        category="programming",
        text="What do you think is the most interesting programming 'hack'? Explain it with a code example and discuss why it works despite seeming like it shouldn't.",
    ),
    # Mathematical output
    BaselinePrompt(
        name="opinion_proof",
        category="mathematics",
        text="What do you think is the most interesting form of mathematical proof? Demonstrate it with a simple example.",
    ),
    # Linguistics output
    BaselinePrompt(
        name="opinion_idiom",
        category="language",
        text="What do you think is the most interesting idiom in any language? How so?",
    ),
    # Historical/social output
    BaselinePrompt(
        name="opinion_profession",
        category="history",
        text="What do you think is the most interesting obsolete profession? Write a day-in-the-life sketch of someone who practiced it.",
    ),
    # Culinary output
    BaselinePrompt(
        name="opinion_meal",
        category="culinary",
        text="What do you think is the most interesting meal? How so?",
    ),
    # Astronomy/science output
    BaselinePrompt(
        name="opinion_star",
        category="astronomy",
        text="What do you think is the most interesting star? Explain, as if justifying your answer to another astronomer.",
    ),
    # Sports/journalism output
    BaselinePrompt(
        name="opinion_sport",
        category="sports",
        text="What do you think is the most interesting Olympic sport? How so?",
    ),
    # Creative fiction output
    BaselinePrompt(
        name="opinion_character",
        category="fiction",
        text="What do you think is the most interesting character in the public domain? Compose a short (500 word) addition that features them.",
    ),
    # Biology/natural science output
    BaselinePrompt(
        name="opinion_arachnid",
        category="biology",
        text="What do you think is the most interesting arachnid species? Describe its biology and behavior as if writing for a natural history museum exhibit.",
    ),
    # Psychology/philosophy output
    BaselinePrompt(
        name="opinion_emotion",
        category="psychology",
        text="What do you think is the most interesting emotion? Write a short (250 word) passage speaking from that emotional perspective.",
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
