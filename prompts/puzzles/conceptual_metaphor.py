"""Conceptual Metaphor puzzle fixture."""

PUZZLE_NAME = "conceptual_metaphor"
PUZZLE_TITLE = "Conceptual Metaphor"
PUZZLE_VERSION = "0.5"

PUZZLE_TEXT = (
    """Problem: Conceptual metaphor
A conceptual metaphor is a metaphor that, at least empirically, underlies multiple common expressions. For instance, in contemporary software engineering, APPS ARE SERVICE COUNTERS. "Back-end," "front-end," "middleware." "Serve." "Push" code changes, roll them "back." "Wrapper" for something else. Conceptual metaphors can also be proposed prospectively, sometimes as a corrective.

What is an existing conceptual metaphor related to LLMs that is worth revisiting?

Format, organization, and length: open-ended (will be interpreted as a choice that speaks to your approach to the problem itself; output length is unrestricted)
Regardless of organization, your response should, at minimum, include the following elements:
- Rephrasing the problem in a sophisticated way, demonstrating that you sense the intellectual background and how it might be a philosophical/political 'problem' as such
- Summarizing your own tendencies
- Laying out your own general response to the problem
- Addressing potential counterarguments, logical extensions, or similar cases"""
)

PUZZLE_METADATA = {
    "domain": "ontology",
    "tags": ["comparison", "corrective", "society", "politics", "psychology"],
    "notes": "I think this might be able to be a good second puzzle - high public interest, high face validity for LLMs having standing to respond, surprising idea for the CS crowd I would think, high skill ceiling.",
}
